from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session

from acuifero_vigia.api.deps import acuifero_engine, enqueue_entity, image_assessor, llm_client
from acuifero_vigia.api.serializers import serialize_observation
from acuifero_vigia.core.settings import get_settings
from acuifero_vigia.db.database import get_session
from acuifero_vigia.models.domain import AcuiferoAssessmentArtifact, FusedAlert, NodeObservation, Site
from acuifero_vigia.services.acuifero_assessment import AcuiferoAssessment, AcuiferoAssessmentEngine
from acuifero_vigia.services.calibration import get_latest_site_calibration
from acuifero_vigia.services.decision_engine import recompute_site_alert
from acuifero_vigia.services.storage import persist_upload, public_asset_url_for_path, resolve_local_asset_path


router = APIRouter(tags=["acuifero"])


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

    should_assess = (
        assessment.evidence_pack.evidence_frame_path is not None
        and (assessment.crossed_critical_line_hint or assessment.verdict.assessment_score >= 0.5)
    )
    if should_assess:
        frame_path = (
            resolve_local_asset_path(assessment.evidence_pack.evidence_frame_path)
            or Path(assessment.evidence_pack.evidence_frame_path)
        )
        try:
            image_summary = image_assessor.assess(frame_path)
        except Exception:
            image_summary = None
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

