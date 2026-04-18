import json
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, String
from datetime import datetime

class Site(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    region: str
    lat: float
    lng: float
    description: Optional[str] = None
    is_active: bool = True

class SiteCalibration(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: str = Field(index=True)
    roi_polygon: Optional[str] = None # JSON string e.g. "[[10, 20], [30, 40]]"
    critical_line: Optional[str] = None # JSON string
    reference_line: Optional[str] = None # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NodeObservation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: str = Field(index=True)
    source_type: str # "video", "webcam"
    video_path: Optional[str] = None
    started_at: datetime
    ended_at: datetime
    frames_analyzed: int
    waterline_ratio: float
    rise_velocity: float
    crossed_critical_line: bool
    confidence: float
    decision_trace: str # JSON string
    severity_score: float
    evidence_frame_path: Optional[str] = None

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
    sync_status: str = "pending" # "pending", "synced"

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
    structured_json: str # JSON string
    decision_trace: str # JSON string

class FusedAlert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    level: str # "green", "yellow", "orange", "red"
    score: float
    trigger_source: str # "node", "volunteer", "fused"
    summary: str
    decision_trace: str # JSON string
    local_alarm_triggered: bool = False
    sync_status: str = "pending"

class SyncQueueItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str # "volunteer_report", "fused_alert"
    entity_id: int
    payload: str # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending" # "pending", "failed", "synced"
