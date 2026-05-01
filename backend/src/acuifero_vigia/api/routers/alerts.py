from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from acuifero_vigia.api.deps import enqueue_entity, llm_client
from acuifero_vigia.db.database import get_session
from acuifero_vigia.models.domain import FusedAlert, Site
from acuifero_vigia.schemas.api import RecomputeRequest
from acuifero_vigia.services.decision_engine import recompute_site_alert


router = APIRouter(tags=["alerts"])


@router.get("/alerts")
async def get_alerts(session: Session = Depends(get_session)) -> list[FusedAlert]:
    return session.exec(select(FusedAlert).order_by(FusedAlert.created_at.desc())).all()


@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    alert = session.get(FusedAlert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    payload = alert.model_dump(mode="json")
    try:
        payload["reasoning_chain_parsed"] = json.loads(alert.reasoning_chain) if alert.reasoning_chain else []
    except json.JSONDecodeError:
        payload["reasoning_chain_parsed"] = []
    try:
        payload["decision_trace_parsed"] = json.loads(alert.decision_trace) if alert.decision_trace else []
    except json.JSONDecodeError:
        payload["decision_trace_parsed"] = []
    return payload


@router.post("/alerts/{alert_id}/export-sinagir")
async def export_alert_sinagir(alert_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    alert = session.get(FusedAlert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    site = session.get(Site, alert.site_id)
    try:
        trace = json.loads(alert.decision_trace) if alert.decision_trace else []
    except json.JSONDecodeError:
        trace = []
    try:
        chain = json.loads(alert.reasoning_chain) if alert.reasoning_chain else []
    except json.JSONDecodeError:
        chain = []
    return {
        "schema": "sinagir-ready-v1",
        "disclaimer": "Schema export only. Not submitted to SINAGIR production endpoints.",
        "event": {
            "external_id": f"acuifero-alert-{alert.id}",
            "observed_at": alert.created_at.isoformat() if alert.created_at else None,
            "site": {
                "id": alert.site_id,
                "name": site.name if site else alert.site_id,
                "region": site.region if site else None,
                "lat": site.lat if site else None,
                "lng": site.lng if site else None,
            },
            "hazard_type": "inundacion",
            "severity": {
                "level": alert.level,
                "score": alert.score,
            },
            "trigger_source": alert.trigger_source,
            "summary": alert.summary,
            "explanation": trace,
            "reasoning": {
                "summary": alert.reasoning_summary,
                "chain": chain,
                "model": alert.reasoning_model,
            },
            "local_actuation": {
                "siren_triggered": alert.local_alarm_triggered,
            },
            "origin_system": "Acuifero 4 + Vigia (edge)",
        },
    }


@router.post("/alerts/recompute")
async def recompute_alerts(
    payload: RecomputeRequest,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    site_ids = [payload.site_id] if payload.site_id else [site.id for site in session.exec(select(Site)).all()]
    results: list[dict[str, object]] = []
    for site_id in site_ids:
        alert = recompute_site_alert(session, site_id, llm_client)
        session.flush()
        enqueue_entity(session, "fused_alert", alert)
        results.append({"site_id": site_id, "score": alert.score, "level": alert.level})
    session.commit()
    return {"recomputed": len(results), "items": results}

