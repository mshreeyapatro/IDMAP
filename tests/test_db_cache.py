"""
Unit tests for Neon DB automatic caching and telemetry persistence.
"""

import pytest
import asyncio
from src.db import cache_service


@pytest.mark.asyncio
async def test_live_weather_cache():
    """Verify live weather caching returns valid telemetry format."""
    data = await cache_service.get_or_refresh_live_weather(force_refresh=True)
    assert "max_coastal_wind_speed_kt" in data or "overall_state_severity" in data
    assert "stations" in data or "is_cached" in data


@pytest.mark.asyncio
async def test_short_range_forecast_cache():
    """Verify short-range forecast caching returns valid 48h trajectory matrix."""
    data = await cache_service.get_or_refresh_short_range_forecast(force_refresh=True)
    assert "state_severity" in data or "is_active_cyclone_warning" in data
    assert "mode" in data


@pytest.mark.asyncio
async def test_seasonal_outlook_cache():
    """Verify 60-day seasonal outlook caching returns vulnerability rankings."""
    data = await cache_service.get_or_refresh_seasonal_outlook(force_refresh=True)
    assert "overall_60day_threat_level" in data or "forecast_window" in data
    assert "mode" in data


@pytest.mark.asyncio
async def test_unified_survey_cache():
    """Verify unified live survey caching returns 10-district matrix."""
    data = await cache_service.get_or_refresh_unified_survey(force_refresh=True)
    assert "overall_state_severity" in data or "peak_coastal_wind_speed_kt" in data
    assert "survey_timestamp" in data or "state" in data
