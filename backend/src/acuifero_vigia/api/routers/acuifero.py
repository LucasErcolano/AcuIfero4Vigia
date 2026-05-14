from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session, desc, select

from acuifero_vigia.api.deps import acuifero_engine, enqueue_entity, image_assessor, llm_client
from acuifero_vigia.api.serializers import serialize_observation
from acuifero_vigia.core.settings import get_settings
from acuifero_vigia.db.database import get_session
from acuifero_vigia.models.domain import AcuiferoAssessmentArtifact, ActuationRecord, FusedAlert, Incident, NodeObservation, Site
from acuifero_vigia.services.acuifero_assessment import AcuiferoAssessment, AcuiferoAssessmentEngine
from acuifero_vigia.services.calibration import get_latest_site_calibration
from acuifero_vigia.services.decision_engine import recompute_site_alert
from acuifero_vigia.services.storage import persist_upload, public_asset_url_for_path, resolve_local_asset_path


router = APIRouter(tags=["acuifero"])


def _should_run_multimodal_verifier(
    session: Session,
    site_id: str,
    assessment: AcuiferoAssessment,
) -> tuple[bool, str]:
    settings = get_settings()
    if not settings.acuifero_multimodal_verifier_enabled:
        return False, "disabled"
    if not assessment.evidence_pack.evidence_frame_path:
        return False, "no evidence frame"

    triggers: list[str] = []
    if assessment.crossed_critical_line_hint:
        triggers.append("critical line crossed")
    if assessment.verdict.assessment_score >= settings.acuifero_multimodal_score_threshold:
        triggers.append(f"score>={settings.acuifero_multimodal_score_threshold:.2f}")
    if assessment.confidence <= settings.acuifero_multimodal_confidence_threshold:
        triggers.append(f"confidence<={settings.acuifero_multimodal_confidence_threshold:.2f}")

    last_verified = session.exec(
        select(NodeObservation)
        .where(NodeObservation.site_id == site_id)
        .where(NodeObservation.image_assessment_model.is_not(None))
        .order_by(desc(NodeObservation.ended_at))
    ).first()
    if last_verified is None:
        interval_due = True
        seconds_since = None
    else:
        seconds_since = max(0.0, (datetime.utcnow() - last_verified.ended_at).total_seconds())
        interval_due = seconds_since >= settings.acuifero_multimodal_min_interval_seconds

    if assessment.crossed_critical_line_hint:
        return True, "triggered: " + ", ".join(triggers)
    if interval_due:
        if triggers:
            return True, "scheduled with trigger: " + ", ".join(triggers)
        if seconds_since is None:
            return True, "scheduled: first multimodal verification"
        return True, f"scheduled: {seconds_since:.0f}s since last verification"
    if triggers:
        return False, f"interval hold after trigger ({', '.join(triggers)}): {seconds_since:.0f}s since last verification"
    return False, f"interval hold: {seconds_since:.0f}s since last verification"


def create_node_observation(
    session: Session,
    site_id: str,
    source_type: str,
    video_path: str,
    assessment: AcuiferoAssessment,
) -> tuple[NodeObservation, FusedAlert]:
    settings = get_settings()
    artifact_payload = {
        "manifest_path": assessment.evidence_pack.artifact_pack.manifest_path,
        "selected_frame_paths": assessment.evidence_pack.artifact_pack.selected_frame_paths,
        "evidence_frame_path": assessment.evidence_pack.artifact_pack.evidence_frame_path,
        "retention_days": settings.acuifero_artifact_retention_days,
        "max_curated_frames": settings.acuifero_max_curated_frames,
        "multimodal_verifier": {
            "enabled": settings.acuifero_multimodal_verifier_enabled,
            "base_url": settings.acuifero_multimodal_base_url,
            "model": settings.acuifero_multimodal_model,
            "min_interval_seconds": settings.acuifero_multimodal_min_interval_seconds,
            "score_threshold": settings.acuifero_multimodal_score_threshold,
            "confidence_threshold": settings.acuifero_multimodal_confidence_threshold,
            "image_max_side": settings.acuifero_multimodal_image_max_side,
        },
    }
    artifact = AcuiferoAssessmentArtifact(
        site_id=site_id,
        source_type=source_type,
        video_path=video_path,
        assessment_mode="temporal-gemma-v1",
        frames_analyzed=assessment.evidence_pack.frames_analyzed,
        temporal_summary=assessment.verdict.temporal_summary,
        reasoning_summary=assessment.verdict.reasoning_summary,
        reasoning_steps=json.dumps(assessment.verdict.reasoning_steps, ensure_ascii=True),
        critical_evidence=json.dumps(assessment.verdict.critical_evidence, ensure_ascii=True),
        runner_name=assessment.verdict.runner_name,
        runner_mode=assessment.verdict.runner_mode,
        fallback_used=assessment.verdict.fallback_used,
        bundle_json=AcuiferoAssessmentEngine.bundle_json(assessment.evidence_pack),
        verdict_json=json.dumps(assessment.verdict.__dict__, ensure_ascii=True),
        artifact_refs=json.dumps(artifact_payload, ensure_ascii=True),
    )
    session.add(artifact)
    session.flush()
    enqueue_entity(session, "acuifero_assessment_artifact", artifact)

    run_multimodal, multimodal_reason = _should_run_multimodal_verifier(session, site_id, assessment)
    assessment.decision_trace.append(f"multimodal verifier {multimodal_reason}")

    image_summary = None
    if run_multimodal:
        frame_path = (
            resolve_local_asset_path(assessment.evidence_pack.evidence_frame_path)
            or Path(assessment.evidence_pack.evidence_frame_path)
        )
        try:
            image_summary = image_assessor.assess(frame_path)
        except Exception:
            image_summary = None
        if image_summary is None:
            assessment.decision_trace.append("multimodal verifier unavailable or invalid, kept text-only verdict")
        else:
            assessment.decision_trace.append(
                f"multimodal verifier {image_summary.model_name} returned confidence={image_summary.confidence:.2f}"
            )

    observation = NodeObservation(
        site_id=site_id,
        source_type=source_type,
        video_path=video_path,
        started_at=assessment.evidence_pack.started_at,
        ended_at=assessment.evidence_pack.ended_at,
        frames_analyzed=assessment.evidence_pack.frames_analyzed,
        waterline_ratio=assessment.waterline_ratio_hint,
        rise_velocity=assessment.rise_velocity_hint,
        crossed_critical_line=assessment.crossed_critical_line_hint,
        confidence=assessment.confidence,
        decision_trace=json.dumps(assessment.decision_trace, ensure_ascii=True),
        severity_score=assessment.verdict.assessment_score,
        assessment_score=assessment.verdict.assessment_score,
        assessment_level=assessment.verdict.assessment_level,
        evidence_frame_path=assessment.evidence_pack.evidence_frame_path,
        analysis_mode="temporal-evidence-builder-v1",
        assessment_mode="temporal-gemma-v1",
        temporal_summary=assessment.verdict.temporal_summary,
        reasoning_summary=assessment.verdict.reasoning_summary,
        reasoning_steps=json.dumps(assessment.verdict.reasoning_steps, ensure_ascii=True),
        critical_evidence=json.dumps(assessment.verdict.critical_evidence, ensure_ascii=True),
        runner_name=assessment.verdict.runner_name,
        runner_mode=assessment.verdict.runner_mode,
        fallback_used=assessment.verdict.fallback_used,
        artifact_refs=json.dumps(artifact_payload, ensure_ascii=True),
        assessment_artifact_id=artifact.id,
    )

    if image_summary is not None:
        observation.image_description = image_summary.description_es
        observation.image_assessment_model = image_summary.model_name
        observation.image_assessment_confidence = image_summary.confidence
        observation.image_water_visible = image_summary.water_visible
        observation.image_infrastructure_at_risk = image_summary.infrastructure_at_risk

    session.add(observation)
    session.flush()
    enqueue_entity(session, "node_observation", observation)

    alert = recompute_site_alert(session, site_id, llm_client)
    session.flush()
    enqueue_entity(session, "fused_alert", alert)
    if alert.incident_id is not None:
        incident = session.get(Incident, alert.incident_id)
        if incident is not None:
            enqueue_entity(session, "incident", incident)
    for record in session.exec(select(ActuationRecord).where(ActuationRecord.alert_id == alert.id)).all():
        enqueue_entity(session, "actuation_record", record)
    session.commit()
    session.refresh(observation)
    session.refresh(alert)
    return observation, alert


@router.post("/node/analyze")
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
        result = acuifero_engine.assess_video(site, video_path or "", calibration, source_type="video")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Node analysis failed: {exc}") from exc

    observation, alert = create_node_observation(
        session=session,
        site_id=site_id,
        source_type="video",
        video_path=video_path or "",
        assessment=result,
    )

    if alert.local_alarm_triggered:
        print(f"!!! LOCAL ALARM TRIGGERED FOR SITE {site_id} VIA NODE ANALYSIS !!!")

    return {"observation": serialize_observation(observation), "alert": alert}


@router.post("/node/explain-frame")
async def explain_frame(frame: UploadFile = File(...)) -> dict[str, Any]:
    path = persist_upload(frame, "frame")
    if not path:
        raise HTTPException(status_code=400, detail="frame upload failed")
    assessment = image_assessor.assess(path)
    if assessment is None:
        raise HTTPException(status_code=503, detail="Image assessment unavailable (LLM down or invalid output)")
    return {
        "description_es": assessment.description_es,
        "water_visible": assessment.water_visible,
        "infrastructure_at_risk": assessment.infrastructure_at_risk,
        "confidence": assessment.confidence,
        "model_name": assessment.model_name,
        "frame_url": public_asset_url_for_path(path),
    }


@router.post("/sites/{site_id}/sample-node-analysis")
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
        result = acuifero_engine.assess_video(site, str(sample_path), calibration, source_type="sample_video")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Sample node analysis failed: {exc}") from exc

    observation, alert = create_node_observation(
        session=session,
        site_id=site_id,
        source_type="sample_video",
        video_path=str(sample_path),
        assessment=result,
    )

    return {
        "observation": serialize_observation(observation),
        "alert": alert,
        "sample_video_url": public_asset_url_for_path(site.sample_video_path),
        "sample_video_source_url": site.sample_video_source_url,
    }
