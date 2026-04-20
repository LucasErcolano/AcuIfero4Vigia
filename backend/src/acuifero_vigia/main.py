from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any, Type

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, SQLModel, select

from acuifero_vigia.adapters.llm import OpenAICompatibleLLM
from acuifero_vigia.core.settings import get_settings
from acuifero_vigia.db.database import get_central_session, get_session, init_db
from acuifero_vigia.models.domain import (
    FusedAlert,
    HydrometSnapshot,
    NodeObservation,
    ParsedObservation,
    Site,
    SiteCalibration,
    SyncQueueItem,
    VolunteerReport,
)
from acuifero_vigia.schemas.api import (
    CalibrationPayload,
    ConnectivityStatus,
    ExternalSnapshotResponse,
    RecomputeRequest,
    RuntimeStatus,
)
from acuifero_vigia.services.calibration import get_latest_site_calibration
from acuifero_vigia.services.decision_engine import recompute_site_alert
from acuifero_vigia.services.external_data import ExternalDataService
from acuifero_vigia.services.node_analysis import NodeAnalyzer
from acuifero_vigia.services.report_structuring import structure_report, structured_result_to_json
from acuifero_vigia.services.storage import (
    get_fixture_dir,
    get_upload_dir,
    persist_upload,
    public_asset_url_for_path,
    resolve_local_asset_path,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    get_upload_dir()
    get_fixture_dir().mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Acuifero 4 + Vigia API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
get_fixture_dir().mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(get_upload_dir())), name="uploads")
app.mount("/fixtures", StaticFiles(directory=str(get_fixture_dir())), name="fixtures")

llm_client = OpenAICompatibleLLM()
external_data_service = ExternalDataService()
node_analyzer = NodeAnalyzer()
is_online = True


def _site_payload(site: Site) -> dict[str, Any]:
    payload = site.model_dump()
    payload["sample_video_url"] = public_asset_url_for_path(site.sample_video_path)
    payload["sample_frame_url"] = public_asset_url_for_path(site.sample_frame_path)
    return payload


def _serialize_observation(observation: NodeObservation) -> dict[str, Any]:
    payload = observation.model_dump(mode="json")
    payload["evidence_frame_url"] = public_asset_url_for_path(observation.evidence_frame_path)
    return payload


def _serialize_external_snapshot(snapshot: HydrometSnapshot) -> ExternalSnapshotResponse:
    return ExternalSnapshotResponse(
        site_id=snapshot.site_id,
        signal_score=snapshot.signal_score,
        summary=snapshot.summary,
        precipitation_mm=snapshot.precipitation_mm,
        precipitation_probability=snapshot.precipitation_probability,
        river_discharge=snapshot.river_discharge,
        river_discharge_max=snapshot.river_discharge_max,
        river_discharge_trend=snapshot.river_discharge_trend,
    )


def _create_node_observation(
    session: Session,
    site_id: str,
    source_type: str,
    video_path: str,
    result,
) -> tuple[NodeObservation, FusedAlert]:
    observation = NodeObservation(
        site_id=site_id,
        source_type=source_type,
        video_path=video_path,
        started_at=result.started_at,
        ended_at=result.ended_at,
        frames_analyzed=result.frames_analyzed,
        waterline_ratio=result.waterline_ratio,
        rise_velocity=result.rise_velocity,
        crossed_critical_line=result.crossed_critical_line,
        confidence=result.confidence,
        decision_trace=json.dumps(result.decision_trace, ensure_ascii=True),
        severity_score=result.severity_score,
        evidence_frame_path=result.evidence_frame_path,
        analysis_mode="banded-window-v1",
    )
    session.add(observation)
    session.flush()
    _enqueue_entity(session, "node_observation", observation)

    alert = recompute_site_alert(session, site_id)
    session.flush()
    _enqueue_entity(session, "fused_alert", alert)
    session.commit()
    session.refresh(observation)
    session.refresh(alert)
    return observation, alert


@app.get("/api/health")
async def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "llm_enabled": settings.llm_enabled,
        "hydromet_enabled": settings.hydromet_enabled,
    }


@app.get("/api/settings/runtime", response_model=RuntimeStatus)
async def get_runtime_status() -> RuntimeStatus:
    llm_status = llm_client.health()
    hydromet_status = external_data_service.health()
    return RuntimeStatus(
        is_online=is_online,
        llm={
            "enabled": llm_status.enabled,
            "reachable": llm_status.reachable,
            "base_url": llm_status.base_url,
            "model": llm_status.model,
            "detail": llm_status.detail,
        },
        hydromet={
            "enabled": hydromet_status.enabled,
            "reachable": hydromet_status.reachable,
            "detail": hydromet_status.detail,
        },
    )


@app.get("/api/sites")
async def get_sites(session: Session = Depends(get_session)) -> list[Site]:
    return session.exec(select(Site).order_by(Site.name)).all()


@app.post("/api/sites")
async def create_site(site: Site, session: Session = Depends(get_session)) -> Site:
    session.add(site)
    session.commit()
    session.refresh(site)
    return site


@app.get("/api/sites/{site_id}")
async def get_site(site_id: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    site = session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return _site_payload(site)


@app.get("/api/sites/{site_id}/calibration")
async def get_site_calibration(site_id: str, session: Session = Depends(get_session)) -> SiteCalibration | None:
    return get_latest_site_calibration(session, site_id)


@app.post("/api/sites/{site_id}/calibration")
async def create_calibration(
    site_id: str,
    payload: CalibrationPayload,
    session: Session = Depends(get_session),
) -> SiteCalibration:
    if not session.get(Site, site_id):
        raise HTTPException(status_code=404, detail="Site not found")

    calibration = SiteCalibration(
        site_id=site_id,
        roi_polygon=json.dumps(payload.roi_polygon or [], ensure_ascii=True),
        critical_line=json.dumps(payload.critical_line or [], ensure_ascii=True),
        reference_line=json.dumps(payload.reference_line or [], ensure_ascii=True),
        notes=payload.notes,
    )
    session.add(calibration)
    session.commit()
    session.refresh(calibration)
    return calibration


@app.get("/api/sites/{site_id}/external-snapshot", response_model=ExternalSnapshotResponse)
async def get_latest_external_snapshot(site_id: str, session: Session = Depends(get_session)) -> ExternalSnapshotResponse:
    snapshot = session.exec(
        select(HydrometSnapshot)
        .where(HydrometSnapshot.site_id == site_id)
        .order_by(HydrometSnapshot.created_at.desc())
    ).first()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="No hydromet snapshot stored for site")
    return _serialize_external_snapshot(snapshot)


@app.post("/api/sites/{site_id}/external-snapshot/refresh", response_model=ExternalSnapshotResponse)
async def refresh_external_snapshot(site_id: str, session: Session = Depends(get_session)) -> ExternalSnapshotResponse:
    site = session.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    try:
        snapshot = external_data_service.fetch_snapshot(site)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Hydromet refresh failed: {exc}") from exc

    session.add(snapshot)
    session.flush()
    _enqueue_entity(session, "hydromet_snapshot", snapshot)
    alert = recompute_site_alert(session, site_id)
    session.flush()
    _enqueue_entity(session, "fused_alert", alert)
    session.commit()
    session.refresh(snapshot)
    return _serialize_external_snapshot(snapshot)


@app.post("/api/node/analyze")
async def analyze_node(
    site_id: str = Form(...),
    video: UploadFile | None = File(None),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    site = session.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    if video is None:
        raise HTTPException(status_code=400, detail="video is required for real node analysis")

    video_path = persist_upload(video, "video")
    calibration = get_latest_site_calibration(session, site_id)
    try:
        result = node_analyzer.analyze_video(video_path or "", calibration)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Node analysis failed: {exc}") from exc

    observation, alert = _create_node_observation(
        session=session,
        site_id=site_id,
        source_type="video",
        video_path=video_path or "",
        result=result,
    )

    if alert.local_alarm_triggered:
        print(f"!!! LOCAL ALARM TRIGGERED FOR SITE {site_id} VIA NODE ANALYSIS !!!")

    return {"observation": _serialize_observation(observation), "alert": alert}


@app.post("/api/sites/{site_id}/sample-node-analysis")
async def analyze_site_sample(site_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    site = session.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    if not site.sample_video_path:
        raise HTTPException(status_code=404, detail="Site does not have a bundled sample clip")

    sample_path = resolve_local_asset_path(site.sample_video_path)
    if sample_path is None or not sample_path.exists():
        raise HTTPException(status_code=404, detail="Bundled sample clip is missing from disk")

    calibration = get_latest_site_calibration(session, site_id)
    try:
        result = node_analyzer.analyze_video(str(sample_path), calibration)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Sample node analysis failed: {exc}") from exc

    observation, alert = _create_node_observation(
        session=session,
        site_id=site_id,
        source_type="sample_video",
        video_path=str(sample_path),
        result=result,
    )

    return {
        "observation": _serialize_observation(observation),
        "alert": alert,
        "sample_video_url": public_asset_url_for_path(site.sample_video_path),
        "sample_video_source_url": site.sample_video_source_url,
    }


@app.post("/api/reports")
async def create_report(
    site_id: str = Form(...),
    reporter_name: str = Form(...),
    reporter_role: str = Form(...),
    transcript_text: str = Form(""),
    offline_created: bool = Form(False),
    photo: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    site = session.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    report = VolunteerReport(
        site_id=site_id,
        reporter_name=reporter_name,
        reporter_role=reporter_role,
        photo_path=persist_upload(photo, "photo"),
        audio_path=persist_upload(audio, "audio"),
        transcript_text=transcript_text,
        offline_created=offline_created,
    )
    session.add(report)
    session.flush()
    _enqueue_entity(session, "volunteer_report", report)

    structured = structure_report(transcript_text, site, llm_client)
    parsed = ParsedObservation(
        volunteer_report_id=report.id or 0,
        water_level_category=structured.water_level_category,
        trend=structured.trend,
        road_status=structured.road_status,
        bridge_status=structured.bridge_status,
        homes_affected=structured.homes_affected,
        urgency=structured.urgency,
        confidence=structured.confidence,
        structured_json=structured_result_to_json(structured),
        decision_trace=json.dumps(structured.decision_trace, ensure_ascii=True),
        parser_source=structured.parser_source,
        severity_score=structured.severity_score,
        summary=structured.summary,
    )
    session.add(parsed)
    session.flush()
    _enqueue_entity(session, "parsed_observation", parsed)

    alert = recompute_site_alert(session, site_id)
    session.flush()
    _enqueue_entity(session, "fused_alert", alert)
    session.commit()
    session.refresh(report)
    session.refresh(parsed)
    session.refresh(alert)

    if alert.local_alarm_triggered:
        print(f"!!! LOCAL ALARM TRIGGERED FOR SITE {site_id} FROM VOLUNTEER REPORT !!!")

    return {"report": report, "parsed": parsed, "alert": alert}


@app.get("/api/reports")
async def get_reports(session: Session = Depends(get_session)) -> list[VolunteerReport]:
    return session.exec(select(VolunteerReport).order_by(VolunteerReport.created_at.desc())).all()


@app.get("/api/alerts")
async def get_alerts(session: Session = Depends(get_session)) -> list[FusedAlert]:
    return session.exec(select(FusedAlert).order_by(FusedAlert.created_at.desc())).all()


@app.post("/api/alerts/recompute")
async def recompute_alerts(
    payload: RecomputeRequest,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    site_ids = [payload.site_id] if payload.site_id else [site.id for site in session.exec(select(Site)).all()]
    results: list[dict[str, object]] = []
    for site_id in site_ids:
        alert = recompute_site_alert(session, site_id)
        session.flush()
        _enqueue_entity(session, "fused_alert", alert)
        results.append({"site_id": site_id, "score": alert.score, "level": alert.level})
    session.commit()
    return {"recomputed": len(results), "items": results}


@app.post("/api/sync/flush")
async def flush_sync(
    edge_session: Session = Depends(get_session),
    central_session: Session = Depends(get_central_session),
) -> dict[str, int]:
    items = edge_session.exec(
        select(SyncQueueItem)
        .where(SyncQueueItem.status == "pending")
        .order_by(SyncQueueItem.created_at)
    ).all()
    flushed = 0
    failed = 0

    model_map: dict[str, Type[SQLModel]] = {
        "volunteer_report": VolunteerReport,
        "parsed_observation": ParsedObservation,
        "fused_alert": FusedAlert,
        "node_observation": NodeObservation,
        "hydromet_snapshot": HydrometSnapshot,
    }

    try:
        for item in items:
            model_cls = model_map.get(item.entity_type)
            if model_cls is None:
                item.status = "failed"
                failed += 1
                continue

            edge_record = edge_session.get(model_cls, item.entity_id)
            if edge_record is None:
                item.status = "failed"
                failed += 1
                continue

            if hasattr(edge_record, "sync_status"):
                setattr(edge_record, "sync_status", "synced")
            central_session.merge(model_cls(**edge_record.model_dump()))
            item.status = "synced"
            flushed += 1

        central_session.commit()
        edge_session.commit()
    except Exception as exc:
        central_session.rollback()
        edge_session.rollback()
        raise HTTPException(status_code=500, detail=f"Sync failed: {exc}") from exc

    return {"queued": len(items), "flushed": flushed, "failed": failed}


@app.get("/api/settings/connectivity")
async def get_connectivity() -> ConnectivityStatus:
    return ConnectivityStatus(is_online=is_online)


@app.post("/api/settings/connectivity")
async def set_connectivity(payload: ConnectivityStatus) -> ConnectivityStatus:
    global is_online
    is_online = payload.is_online
    return ConnectivityStatus(is_online=is_online)



def _enqueue_entity(session: Session, entity_type: str, entity: SQLModel) -> None:
    entity_id = getattr(entity, "id", None)
    if entity_id is None:
        return
    queue_item = SyncQueueItem(
        entity_type=entity_type,
        entity_id=entity_id,
        payload=json.dumps(entity.model_dump(mode="json"), ensure_ascii=True),
    )
    session.add(queue_item)
