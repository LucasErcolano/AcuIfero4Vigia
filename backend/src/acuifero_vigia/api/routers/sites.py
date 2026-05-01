from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from acuifero_vigia.api.deps import enqueue_entity, external_data_service, llm_client
from acuifero_vigia.api.serializers import serialize_external_snapshot, site_payload
from acuifero_vigia.db.database import get_session
from acuifero_vigia.models.domain import FusedAlert, HydrometSnapshot, Site, SiteCalibration
from acuifero_vigia.schemas.api import CalibrationPayload, ExternalSnapshotResponse
from acuifero_vigia.services.calibration import get_latest_site_calibration
from acuifero_vigia.services.decision_engine import recompute_site_alert


router = APIRouter(tags=["sites"])


@router.get("/sites")
async def get_sites(session: Session = Depends(get_session)) -> list[Site]:
    return session.exec(select(Site).order_by(Site.name)).all()


@router.post("/sites")
async def create_site(site: Site, session: Session = Depends(get_session)) -> Site:
    session.add(site)
    session.commit()
    session.refresh(site)
    return site


@router.get("/sites/{site_id}")
async def get_site(site_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    site = session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site_payload(site)


@router.get("/sites/{site_id}/calibration")
async def get_site_calibration(site_id: str, session: Session = Depends(get_session)) -> SiteCalibration | None:
    return get_latest_site_calibration(session, site_id)


@router.post("/sites/{site_id}/calibration")
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


@router.get("/sites/{site_id}/external-snapshot", response_model=ExternalSnapshotResponse)
async def get_latest_external_snapshot(site_id: str, session: Session = Depends(get_session)) -> ExternalSnapshotResponse:
    snapshot = session.exec(
        select(HydrometSnapshot)
        .where(HydrometSnapshot.site_id == site_id)
        .order_by(HydrometSnapshot.created_at.desc())
    ).first()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="No hydromet snapshot stored for site")
    return serialize_external_snapshot(snapshot)


@router.post("/sites/{site_id}/external-snapshot/refresh", response_model=ExternalSnapshotResponse)
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
    enqueue_entity(session, "hydromet_snapshot", snapshot)
    alert: FusedAlert = recompute_site_alert(session, site_id, llm_client)
    session.flush()
    enqueue_entity(session, "fused_alert", alert)
    session.commit()
    session.refresh(snapshot)
    return serialize_external_snapshot(snapshot)

