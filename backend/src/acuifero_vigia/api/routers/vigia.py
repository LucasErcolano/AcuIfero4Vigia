from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session, select

from acuifero_vigia.api.deps import enqueue_entity, llm_client, text_structurer
from acuifero_vigia.db.database import get_session
from acuifero_vigia.models.domain import ParsedObservation, Site, VolunteerReport
from acuifero_vigia.services.decision_engine import recompute_site_alert
from acuifero_vigia.services.report_structuring import structure_report, structured_result_to_json
from acuifero_vigia.services.storage import persist_upload


router = APIRouter(tags=["vigia"])


@router.post("/reports")
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
    enqueue_entity(session, "volunteer_report", report)

    structured = structure_report(transcript_text, site, text_structurer)
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
    enqueue_entity(session, "parsed_observation", parsed)

    alert = recompute_site_alert(session, site_id, llm_client)
    session.flush()
    enqueue_entity(session, "fused_alert", alert)
    session.commit()
    session.refresh(report)
    session.refresh(parsed)
    session.refresh(alert)

    if alert.local_alarm_triggered:
        print(f"!!! LOCAL ALARM TRIGGERED FOR SITE {site_id} FROM VOLUNTEER REPORT !!!")

    return {"report": report, "parsed": parsed, "alert": alert}


@router.get("/reports")
async def get_reports(session: Session = Depends(get_session)) -> list[VolunteerReport]:
    return session.exec(select(VolunteerReport).order_by(VolunteerReport.created_at.desc())).all()

