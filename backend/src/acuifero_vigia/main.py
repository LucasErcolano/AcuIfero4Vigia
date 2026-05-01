from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from acuifero_vigia.api.deps import acuifero_engine, external_data_service, image_assessor, llm_client, text_structurer
from acuifero_vigia.api.routers.acuifero import analyze_node, analyze_site_sample, create_node_observation, explain_frame
from acuifero_vigia.api.routers.alerts import export_alert_sinagir, get_alert, get_alerts, recompute_alerts
from acuifero_vigia.api.routers.runtime import get_connectivity, get_runtime_status, health, set_connectivity
from acuifero_vigia.api.routers.sites import (
    create_calibration,
    create_site,
    get_latest_external_snapshot,
    get_site,
    get_site_calibration,
    get_sites,
    refresh_external_snapshot,
)
from acuifero_vigia.api.routers.sync import flush_sync
from acuifero_vigia.api.routers.vigia import create_report, get_reports
from acuifero_vigia.db.database import init_db
from acuifero_vigia.services.storage import get_fixture_dir, get_upload_dir
from acuifero_vigia.api.routers import acuifero, alerts, runtime, sites, sync, vigia


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

for router in (
    runtime.router,
    sites.router,
    acuifero.router,
    vigia.router,
    alerts.router,
    sync.router,
):
    app.include_router(router, prefix="/api")


# Backward-compatible aliases for older tests/scripts that import from main.py.
is_online = True

