from __future__ import annotations

from typing import Type

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import SQLModel, Session, select

from acuifero_vigia.db.database import get_central_session, get_session
from acuifero_vigia.models.domain import (
    AcuiferoAssessmentArtifact,
    FusedAlert,
    HydrometSnapshot,
    NodeObservation,
    ParsedObservation,
    SyncQueueItem,
    VolunteerReport,
)


router = APIRouter(tags=["sync"])


@router.post("/sync/flush")
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
        "acuifero_assessment_artifact": AcuiferoAssessmentArtifact,
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

