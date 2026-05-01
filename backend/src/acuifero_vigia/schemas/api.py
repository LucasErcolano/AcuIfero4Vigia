from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ConnectivityStatus(BaseModel):
    is_online: bool


class CalibrationPayload(BaseModel):
    roi_polygon: list[list[int]] | None = None
    critical_line: list[list[int]] | None = None
    reference_line: list[list[int]] | None = None
    notes: str | None = None


class RuntimeStatus(BaseModel):
    is_online: bool
    llm: dict[str, Any]
    acuifero: dict[str, Any]
    hydromet: dict[str, Any]


class RecomputeRequest(BaseModel):
    site_id: str | None = None


class ExternalSnapshotResponse(BaseModel):
    site_id: str
    signal_score: float
    summary: str
    precipitation_mm: float = Field(default=0.0)
    precipitation_probability: float = Field(default=0.0)
    river_discharge: float | None = None
    river_discharge_max: float | None = None
    river_discharge_trend: float | None = None
