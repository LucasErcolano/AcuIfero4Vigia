import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select

from src.acuifero_vigia.db.database import get_session, get_central_session, init_db
from src.acuifero_vigia.models.domain import (
    Site, SiteCalibration, NodeObservation, VolunteerReport,
    ParsedObservation, FusedAlert, SyncQueueItem
)

app = FastAPI(title="Acuifero 4 + Vigia API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    get_upload_dir()

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/sites")
def get_sites(session: Session = Depends(get_session)):
    return session.exec(select(Site)).all()

@app.post("/api/sites")
def create_site(site: Site, session: Session = Depends(get_session)):
    session.add(site)
    session.commit()
    session.refresh(site)
    return site

@app.get("/api/sites/{site_id}")
def get_site(site_id: str, session: Session = Depends(get_session)):
    site = session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site

@app.post("/api/sites/{site_id}/calibration")
def create_calibration(site_id: str, cal: SiteCalibration, session: Session = Depends(get_session)):
    cal.site_id = site_id
    session.add(cal)
    session.commit()
    session.refresh(cal)
    return cal

def get_upload_dir() -> Path:
    backend_root = Path(__file__).resolve().parents[2]
    default_upload_dir = backend_root / "data" / "uploads"
    upload_dir = Path(os.environ.get("ACUIFERO_UPLOAD_DIR", str(default_upload_dir)))
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def persist_upload(file: UploadFile | None, prefix: str) -> str | None:
    if not file or not file.filename:
        return None

    safe_name = Path(file.filename).name
    extension = Path(safe_name).suffix
    stored_name = f"{prefix}-{uuid4().hex}{extension}"
    target_path = get_upload_dir() / stored_name
    file.file.seek(0)
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return str(target_path)


def infer_report_severity(transcript_text: str) -> tuple[float, str]:
    transcript = transcript_text.lower()
    if "paso la marca" in transcript or "marca critica" in transcript:
        return 0.8, "red"
    if "subiendo" in transcript or "crecida" in transcript:
        return 0.6, "orange"
    return 0.3, "green"


@app.post("/api/node/analyze")
def analyze_node(site_id: str = Form(...), video: UploadFile = File(None), session: Session = Depends(get_session)):
    # Mock video analysis
    obs = NodeObservation(
        site_id=site_id,
        source_type="video" if video else "webcam",
        video_path=persist_upload(video, "video"),
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        frames_analyzed=60,
        waterline_ratio=0.8,
        rise_velocity=0.1,
        crossed_critical_line=True,
        confidence=0.85,
        decision_trace=json.dumps(["Waterline above reference", "Motion smooth"]),
        severity_score=0.8
    )
    session.add(obs)
    
    # Fused alert mock
    alert = FusedAlert(
        site_id=site_id,
        level="red",
        score=0.8,
        trigger_source="node",
        summary="Critical waterline crossed",
        decision_trace=json.dumps(["node waterline_ratio=0.8 > 0.75"]),
        local_alarm_triggered=True
    )
    session.add(alert)
    session.commit()
    session.refresh(obs)
    session.refresh(alert)
    
    # Print local alarm
    print(f"!!! LOCAL ALARM TRIGGERED FOR SITE {site_id} !!!")
    
    return {"observation": obs, "alert": alert}

@app.post("/api/reports")
def create_report(
    site_id: str = Form(...),
    reporter_name: str = Form(...),
    reporter_role: str = Form(...),
    transcript_text: str = Form(""),
    offline_created: bool = Form(False),
    photo: UploadFile = File(None),
    audio: UploadFile = File(None),
    session: Session = Depends(get_session)
):
    photo_path = persist_upload(photo, "photo")
    audio_path = persist_upload(audio, "audio")

    report = VolunteerReport(
        site_id=site_id,
        reporter_name=reporter_name,
        reporter_role=reporter_role,
        photo_path=photo_path,
        audio_path=audio_path,
        transcript_text=transcript_text,
        offline_created=offline_created,
        sync_status="pending"
    )
    session.add(report)
    session.flush()

    severity, level = infer_report_severity(transcript_text)
    parsed = ParsedObservation(
        volunteer_report_id=report.id or 0,
        water_level_category="unknown",
        trend="unknown",
        road_status="unknown",
        bridge_status="unknown",
        homes_affected=False,
        urgency="normal",
        confidence=0.9,
        structured_json="{}",
        decision_trace=json.dumps(["Parsed transcript"])
    )
    session.add(parsed)
    
    alert = FusedAlert(
        site_id=site_id,
        level=level,
        score=severity,
        trigger_source="volunteer",
        summary=f"Report summary: {level}",
        decision_trace=json.dumps([f"Volunteer report text: {transcript_text} -> score {severity}"]),
        local_alarm_triggered=(level == "red")
    )
    session.add(alert)
    session.flush()
    
    # Add to sync queue
    queue_item = SyncQueueItem(
        entity_type="volunteer_report",
        entity_id=report.id or 0,
        payload=json.dumps(report.model_dump(mode="json"))
    )
    session.add(queue_item)
    alert_queue_item = SyncQueueItem(
        entity_type="fused_alert",
        entity_id=alert.id or 0,
        payload=json.dumps(alert.model_dump(mode="json"))
    )
    session.add(alert_queue_item)
    
    session.commit()
    session.refresh(report)
    if level == "red":
        print(f"!!! LOCAL ALARM TRIGGERED FOR SITE {site_id} FROM VOLUNTEER REPORT !!!")
    return report

@app.get("/api/reports")
def get_reports(session: Session = Depends(get_session)):
    return session.exec(select(VolunteerReport)).all()

@app.post("/api/alerts/recompute")
def recompute_alerts():
    return {"status": "not implemented"}

@app.get("/api/alerts")
def get_alerts(session: Session = Depends(get_session)):
    return session.exec(select(FusedAlert)).all()

@app.post("/api/sync/flush")
def flush_sync(
    edge_session: Session = Depends(get_session),
    central_session: Session = Depends(get_central_session)
):
    items = edge_session.exec(select(SyncQueueItem).where(SyncQueueItem.status == "pending")).all()
    flushed = 0
    failed = 0

    try:
        for item in items:
            synced = False

            if item.entity_type == "volunteer_report":
                report = edge_session.get(VolunteerReport, item.entity_id)
                if report:
                    report.sync_status = "synced"
                    central_session.merge(VolunteerReport(**report.model_dump()))
                    synced = True
            elif item.entity_type == "fused_alert":
                alert = edge_session.get(FusedAlert, item.entity_id)
                if alert:
                    alert.sync_status = "synced"
                    central_session.merge(FusedAlert(**alert.model_dump()))
                    synced = True

            item.status = "synced" if synced else "failed"
            if synced:
                flushed += 1
            else:
                failed += 1

        central_session.commit()
        edge_session.commit()
    except Exception as exc:
        central_session.rollback()
        edge_session.rollback()
        raise HTTPException(status_code=500, detail=f"Sync failed: {exc}") from exc

    return {"queued": len(items), "flushed": flushed, "failed": failed}

is_online = True

@app.get("/api/settings/connectivity")
def get_connectivity():
    return {"is_online": is_online}

class ConnectivityStatus(BaseModel):
    is_online: bool

@app.post("/api/settings/connectivity")
def set_connectivity(payload: ConnectivityStatus):
    global is_online
    is_online = payload.is_online
    return {"is_online": is_online}
