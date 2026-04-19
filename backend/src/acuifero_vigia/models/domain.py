from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Site(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    region: str
    lat: float
    lng: float
    description: Optional[str] = None
    sample_video_path: Optional[str] = None
    sample_video_source_url: Optional[str] = None
    sample_frame_path: Optional[str] = None
    is_active: bool = True


class SiteCalibration(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: str = Field(index=True)
    roi_polygon: Optional[str] = None
    critical_line: Optional[str] = None
    reference_line: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NodeObservation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: str = Field(index=True)
    source_type: str
    video_path: Optional[str] = None
    started_at: datetime
    ended_at: datetime
    frames_analyzed: int
    waterline_ratio: float
    rise_velocity: float
    crossed_critical_line: bool
    confidence: float
    decision_trace: str
    severity_score: float
    evidence_frame_path: Optional[str] = None
    analysis_mode: str = "temporal-gradient"
    sync_status: str = "pending"


class VolunteerReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reporter_name: str
    reporter_role: str
    photo_path: Optional[str] = None
    audio_path: Optional[str] = None
    transcript_text: str
    offline_created: bool = False
    sync_status: str = "pending"


class ParsedObservation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    volunteer_report_id: int = Field(index=True)
    water_level_category: str
    trend: str
    road_status: str
    bridge_status: str
    homes_affected: bool
    urgency: str
    confidence: float
    structured_json: str
    decision_trace: str
    parser_source: str = "rules"
    severity_score: float = 0.0
    summary: str = ""


class HydrometSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    provider: str = "open-meteo"
    weather_code: Optional[int] = None
    precipitation_mm: float = 0.0
    rain_mm: float = 0.0
    precipitation_probability: float = 0.0
    river_discharge: Optional[float] = None
    river_discharge_max: Optional[float] = None
    river_discharge_trend: Optional[float] = None
    signal_score: float = 0.0
    summary: str = ""
    raw_payload: str = "{}"
    sync_status: str = "pending"


class FusedAlert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    level: str
    score: float
    trigger_source: str
    summary: str
    decision_trace: str
    local_alarm_triggered: bool = False
    sync_status: str = "pending"


class SyncQueueItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str
    entity_id: int
    payload: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"
