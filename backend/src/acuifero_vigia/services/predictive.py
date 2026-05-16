from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Measurement:
    observed_at: datetime
    water_level: float
    rain_mm: float = 0.0
    reports_count: int = 0


@dataclass(frozen=True)
class Forecast:
    horizon_minutes: int
    expected_level: float
    trend_per_hour: float
    risk: str


def forecast_short_term(measurements: list[Measurement], *, horizon_minutes: int = 60) -> Forecast:
    if not measurements:
        return Forecast(horizon_minutes, 0.0, 0.0, "unknown")
    ordered = sorted(measurements, key=lambda item: item.observed_at)
    first, last = ordered[0], ordered[-1]
    hours = max((last.observed_at - first.observed_at).total_seconds() / 3600.0, 1 / 60)
    trend = (last.water_level - first.water_level) / hours
    expected = last.water_level + trend * (horizon_minutes / 60.0)
    rain = sum(item.rain_mm for item in ordered[-6:])
    reports = sum(item.reports_count for item in ordered[-6:])
    risk = "low"
    if expected >= 0.8 or trend >= 0.25 or rain >= 30 or reports >= 3:
        risk = "high"
    elif expected >= 0.55 or trend >= 0.12 or rain >= 15 or reports >= 1:
        risk = "moderate"
    return Forecast(horizon_minutes, round(expected, 4), round(trend, 4), risk)
