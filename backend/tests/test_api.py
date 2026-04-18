from io import BytesIO
from pathlib import Path
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select
import pytest

from src.acuifero_vigia import main as main_module
from src.acuifero_vigia.main import app, get_upload_dir
from src.acuifero_vigia.db.database import edge_engine, central_engine, init_db
from src.acuifero_vigia.models.domain import VolunteerReport, SyncQueueItem, FusedAlert

init_db()
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACUIFERO_UPLOAD_DIR", str(tmp_path / "uploads"))
    main_module.is_online = True

    for engine in (edge_engine, central_engine):
        with Session(engine) as session:
            for table in reversed(SQLModel.metadata.sorted_tables):
                session.exec(table.delete())
            session.commit()

    upload_dir = get_upload_dir()
    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            file_path.unlink()

    yield

    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            file_path.unlink()

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_connectivity():
    # Set to false
    response = client.post("/api/settings/connectivity", json={"is_online": False})
    assert response.status_code == 200
    assert response.json() == {"is_online": False}
    
    # Set to true
    response = client.post("/api/settings/connectivity", json={"is_online": True})
    assert response.status_code == 200
    assert response.json() == {"is_online": True}

def test_report_and_sync():
    response = client.post(
        "/api/reports",
        data={
            "site_id": "test-site",
            "reporter_name": "Test User",
            "reporter_role": "Tester",
            "transcript_text": "El agua paso la marca",
            "offline_created": "true",
        }
    )
    assert response.status_code == 200
    report_data = response.json()
    assert report_data["site_id"] == "test-site"
    assert report_data["sync_status"] == "pending"
    assert report_data["offline_created"] is True

    report_id = report_data["id"]

    sync_response = client.post("/api/sync/flush")
    assert sync_response.status_code == 200
    sync_data = sync_response.json()
    assert sync_data["queued"] == 2
    assert sync_data["flushed"] == 2
    assert sync_data["failed"] == 0

    with Session(edge_engine) as session:
        queue_items = session.exec(select(SyncQueueItem)).all()
        assert len(queue_items) == 2
        assert all(item.status == "synced" for item in queue_items)

        edge_report = session.get(VolunteerReport, report_id)
        assert edge_report is not None
        assert edge_report.sync_status == "synced"

    with Session(central_engine) as session:
        central_report = session.get(VolunteerReport, report_id)
        assert central_report is not None
        assert central_report.sync_status == "synced"
        assert central_report.transcript_text == "El agua paso la marca"
        central_alert = session.exec(select(FusedAlert)).first()
        assert central_alert is not None
        assert central_alert.sync_status == "synced"


def test_report_uploads_are_persisted():
    response = client.post(
        "/api/reports",
        data={
            "site_id": "test-site",
            "reporter_name": "Upload User",
            "reporter_role": "Tester",
            "transcript_text": "Foto y audio cargados",
        },
        files={
            "photo": ("river.jpg", BytesIO(b"fake-image-bytes"), "image/jpeg"),
            "audio": ("note.wav", BytesIO(b"fake-audio-bytes"), "audio/wav"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["photo_path"]
    assert payload["audio_path"]

    photo_path = Path(payload["photo_path"])
    audio_path = Path(payload["audio_path"])
    assert photo_path.exists()
    assert audio_path.exists()
    assert photo_path.parent == get_upload_dir()
    assert audio_path.parent == get_upload_dir()
