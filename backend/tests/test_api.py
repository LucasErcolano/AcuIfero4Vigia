from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import anyio
import cv2
import httpx
import numpy as np
import pytest
from fastapi import UploadFile
from sqlmodel import Session, SQLModel, select

from acuifero_vigia import main as main_module
from acuifero_vigia.core import settings as settings_module
from acuifero_vigia.db.database import central_engine, edge_engine, init_db
from acuifero_vigia.main import analyze_node, app, create_report, flush_sync
from acuifero_vigia.models.domain import FusedAlert, NodeObservation, Site, SiteCalibration, SyncQueueItem, VolunteerReport
from acuifero_vigia.models.domain import HydrometSnapshot
from acuifero_vigia.services.storage import get_upload_dir

init_db()


async def api_request(method: str, url: str, **kwargs) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, url, **kwargs)



def request(method: str, url: str, **kwargs) -> httpx.Response:
    async def _call() -> httpx.Response:
        return await api_request(method, url, **kwargs)

    return anyio.run(_call)


@pytest.fixture(autouse=True)
def reset_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACUIFERO_UPLOAD_DIR", str(tmp_path / "uploads"))
    settings_module.get_settings.cache_clear()
    main_module.is_online = True
    monkeypatch.setattr(main_module.llm_client, "structure_observation", lambda *_args, **_kwargs: None)

    for engine in (edge_engine, central_engine):
        with Session(engine) as session:
            for table in reversed(SQLModel.metadata.sorted_tables):
                session.exec(table.delete())
            session.commit()

    upload_dir = get_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            file_path.unlink()

    with Session(edge_engine) as session:
        session.add(
            Site(
                id="test-site",
                name="Puente Test",
                region="Zona Demo",
                lat=-32.95,
                lng=-60.64,
                description="Sitio usado para pruebas",
                is_active=True,
            )
        )
        session.commit()

    yield

    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            file_path.unlink()



def _build_test_video(path: Path) -> None:
    width, height = 320, 240
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 4.0, (width, height))
    if not writer.isOpened():
        raise RuntimeError("Could not create synthetic test video")

    for index in range(16):
        frame = np.full((height, width, 3), (200, 210, 220), dtype=np.uint8)
        waterline_y = max(70, 210 - index * 9)
        cv2.rectangle(frame, (0, waterline_y), (width - 1, height - 1), (90, 70, 40), -1)
        cv2.line(frame, (0, 100), (width - 1, 100), (245, 245, 245), 2)
        writer.write(frame)

    writer.release()



def test_health():
    response = request("GET", "/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"



def test_connectivity():
    response = request("POST", "/api/settings/connectivity", json={"is_online": False})
    assert response.status_code == 200
    assert response.json() == {"is_online": False}

    response = request("POST", "/api/settings/connectivity", json={"is_online": True})
    assert response.status_code == 200
    assert response.json() == {"is_online": True}



def test_report_and_sync():
    async def run_flow():
        with Session(edge_engine) as edge_session:
            payload = await create_report(
                site_id="test-site",
                reporter_name="Test User",
                reporter_role="Tester",
                transcript_text="El agua paso la marca critica y la calle esta cortada",
                offline_created=True,
                photo=None,
                audio=None,
                session=edge_session,
            )
            report_id = payload["report"].id
            assert payload["parsed"].parser_source == "rules"
            assert payload["alert"].level in {"orange", "red"}

        with Session(edge_engine) as edge_session, Session(central_engine) as central_session:
            sync_payload = await flush_sync(edge_session=edge_session, central_session=central_session)
            return report_id, sync_payload

    report_id, sync_payload = anyio.run(run_flow)
    assert sync_payload["queued"] == 3
    assert sync_payload["flushed"] == 3
    assert sync_payload["failed"] == 0

    with Session(edge_engine) as session:
        queue_items = session.exec(select(SyncQueueItem)).all()
        assert len(queue_items) == 3
        assert all(item.status == "synced" for item in queue_items)

        edge_report = session.get(VolunteerReport, report_id)
        assert edge_report is not None
        assert edge_report.sync_status == "synced"

    with Session(central_engine) as session:
        central_report = session.get(VolunteerReport, report_id)
        assert central_report is not None
        assert central_report.sync_status == "synced"
        central_alert = session.exec(select(FusedAlert)).first()
        assert central_alert is not None
        assert central_alert.sync_status == "synced"



def test_report_uploads_are_persisted():
    async def run_flow():
        photo = UploadFile(filename="river.jpg", file=BytesIO(b"fake-image-bytes"))
        audio = UploadFile(filename="note.wav", file=BytesIO(b"fake-audio-bytes"))
        with Session(edge_engine) as edge_session:
            return await create_report(
                site_id="test-site",
                reporter_name="Upload User",
                reporter_role="Tester",
                transcript_text="Foto y audio cargados",
                offline_created=False,
                photo=photo,
                audio=audio,
                session=edge_session,
            )

    payload = anyio.run(run_flow)["report"]
    photo_path = Path(payload.photo_path)
    audio_path = Path(payload.audio_path)
    assert photo_path.exists()
    assert audio_path.exists()
    assert photo_path.parent == get_upload_dir()
    assert audio_path.parent == get_upload_dir()



def test_node_analysis_with_video(tmp_path: Path):
    video_path = tmp_path / "synthetic.avi"
    _build_test_video(video_path)

    async def run_flow():
        with video_path.open("rb") as handle:
            upload = UploadFile(filename=video_path.name, file=handle)
            with Session(edge_engine) as edge_session:
                return await analyze_node(site_id="test-site", video=upload, session=edge_session)

    payload = anyio.run(run_flow)
    assert payload["observation"]["frames_analyzed"] >= 3
    assert payload["observation"]["confidence"] > 0
    assert payload["observation"]["evidence_frame_url"].startswith("/uploads/")
    assert payload["alert"].level in {"yellow", "orange", "red"}

    with Session(edge_engine) as session:
        observation = session.exec(select(NodeObservation)).first()
        assert observation is not None
        assert observation.video_path is not None
        assert observation.sync_status == "pending"


def test_sample_node_analysis_endpoint(tmp_path: Path):
    video_path = tmp_path / "sample.avi"
    _build_test_video(video_path)

    with Session(edge_engine) as session:
        session.add(
            Site(
                id="sample-site",
                name="Site with bundled clip",
                region="Zona Demo",
                lat=-32.96,
                lng=-60.65,
                description="Sitio con sample video",
                sample_video_path=str(video_path),
                sample_video_source_url="https://example.com/fixed-cam",
                sample_frame_path=None,
                is_active=True,
            )
        )
        session.add(
            SiteCalibration(
                site_id="sample-site",
                roi_polygon=json.dumps([[0, 40], [320, 40], [320, 220], [0, 220]], ensure_ascii=True),
                critical_line=json.dumps([[0, 95], [320, 95]], ensure_ascii=True),
                reference_line=json.dumps([[0, 155], [320, 155]], ensure_ascii=True),
                notes="synthetic calibration",
            )
        )
        session.commit()

    response = request("POST", "/api/sites/sample-site/sample-node-analysis")
    assert response.status_code == 200
    payload = response.json()
    assert payload["observation"]["frames_analyzed"] >= 3
    assert payload["observation"]["evidence_frame_url"].startswith("/uploads/")
    assert payload["sample_video_source_url"] == "https://example.com/fixed-cam"


def test_external_snapshot_refresh_serializes_response(monkeypatch: pytest.MonkeyPatch):
    snapshot = HydrometSnapshot(
        site_id="test-site",
        signal_score=0.42,
        summary="rain now 2.0 mm, 12h precip prob 60%",
        precipitation_mm=2.0,
        precipitation_probability=60.0,
        river_discharge=12.0,
        river_discharge_max=18.0,
        river_discharge_trend=1.5,
    )

    monkeypatch.setattr(main_module.external_data_service, "fetch_snapshot", lambda _site: snapshot)

    response = request("POST", "/api/sites/test-site/external-snapshot/refresh")
    assert response.status_code == 200
    payload = response.json()
    assert payload["site_id"] == "test-site"
    assert payload["signal_score"] == 0.42
    assert payload["summary"] == "rain now 2.0 mm, 12h precip prob 60%"
