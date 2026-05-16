from __future__ import annotations

from datetime import datetime, timedelta

from acuifero_vigia.services.predictive import Measurement, forecast_short_term


def test_short_term_forecast_uses_water_trend():
    now = datetime(2026, 5, 16, 12, 0, 0)
    forecast = forecast_short_term(
        [
            Measurement(now - timedelta(minutes=30), 0.4),
            Measurement(now, 0.6, rain_mm=10, reports_count=1),
        ],
        horizon_minutes=60,
    )
    assert forecast.expected_level > 0.9
    assert forecast.risk == "high"
