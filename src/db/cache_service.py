"""
Automatic Cache & Telemetry Persistence Engine for Neon DB.

Guarantees:
1. Instant zero-blank UI loads by returning stored cache snapshots from Neon DB instantly.
2. Auto-rewrites cache records in Neon DB whenever fresh weather or forecast data is calculated.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("idmap.cache")


async def _safe_prisma_op(coro, timeout: float = 2.0):
    """Executes a Prisma query with a strict timeout so idle serverless poolers never hang the API."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except (asyncio.TimeoutError, Exception, BaseException) as e:
        logger.warning(f"Prisma DB operation failed or timed out ({e}); proceeding with fast fallback.")
        return None


def is_cache_expired(updated_at: Optional[datetime], max_age_seconds: int = 180) -> bool:
    """Returns True if the cache entry is older than max_age_seconds (default 3 minutes)."""
    if not updated_at:
        return True
    try:
        now = datetime.now(timezone.utc)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        age = (now - updated_at).total_seconds()
        return age > max_age_seconds
    except Exception as e:
        logger.debug(f"Error checking cache expiration: {e}")
        return False


async def get_or_refresh_live_weather(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Returns latest cached live weather telemetry from Neon DB.
    If no cache exists, cache is older than 3 minutes, or force_refresh is True,
    fetches fresh telemetry from Open-Meteo and updates Neon DB.
    """
    try:
        from src.db.db import prisma
        if prisma is not None and prisma.is_connected() and not force_refresh:
            cached = await _safe_prisma_op(prisma.liveweathercache.find_first(order={"updatedAt": "desc"}), timeout=1.5)
            if cached and not is_cache_expired(cached.updatedAt, max_age_seconds=180):
                payload = json.loads(cached.stationDataJson) if isinstance(cached.stationDataJson, str) else cached.stationDataJson
                if isinstance(payload, dict):
                    stations = payload.get("stations", [])
                    has_stale_multiplier = any(s.get("station") == "Gopalpur" and s.get("wind_speed_kt", 0) > 40.0 for s in stations)
                    if not has_stale_multiplier:
                        payload["is_cached"] = True
                        payload["last_updated"] = cached.updatedAt.isoformat() if isinstance(cached.updatedAt, datetime) else str(cached.updatedAt)
                        return payload
                    else:
                        logger.info("Stale uncalibrated live weather cache detected in Neon DB. Forcing cache refresh...")
            elif cached:
                logger.info("Live weather cache expired (>3m). Fetching fresh Open-Meteo telemetry...")
    except Exception as e:
        logger.warning(f"Failed to read live weather cache from Neon DB: {e}")

    # Fetch fresh live weather from Open-Meteo
    from src.ingestion import live_weather
    fresh_data = live_weather.get_live_weather_feed()

    # Auto-rewrite into Neon DB
    try:
        from src.db.db import prisma
        if prisma is not None and prisma.is_connected():
            await _safe_prisma_op(
                prisma.liveweathercache.create(
                    data={
                        "maxCoastalWindSpeedKt": float(fresh_data.get("max_coastal_wind_speed_kt", 0.0)),
                        "minCoastalPressureHpa": float(fresh_data.get("min_coastal_pressure_hpa", 1010.0)),
                        "overallStateSeverity": fresh_data.get("overall_state_severity", "Normal"),
                        "stationDataJson": json.dumps(fresh_data),
                    }
                ),
                timeout=1.5
            )
            logger.info("Successfully updated LiveWeatherCache in Neon DB.")
    except Exception as e:
        logger.warning(f"Failed to update LiveWeatherCache in Neon DB: {e}")

    fresh_data["is_cached"] = False
    fresh_data["last_updated"] = datetime.now().isoformat()
    return fresh_data


async def get_or_refresh_short_range_forecast(force_refresh: bool = False, mode: str = "simulated") -> Dict[str, Any]:
    """
    Returns latest cached 48-Hour Short-Range Track Forecast matrix from Neon DB.
    If cache is older than 3 minutes or force_refresh is True, auto-recomputes fresh live forecast.
    Supports mode='simulated' and mode='live'.
    """
    from src.forecasting import predictive_engine

    if mode == "live":
        fresh_data = predictive_engine.generate_48h_short_range_forecast(mode="live")
        fresh_data["is_cached"] = False
        fresh_data["last_updated"] = datetime.now().isoformat()
        return fresh_data

    try:
        from src.db.db import prisma
        if prisma is not None and prisma.is_connected() and not force_refresh:
            cached = await _safe_prisma_op(prisma.shortrangeforecastcache.find_first(order={"updatedAt": "desc"}), timeout=1.5)
            if cached and not is_cache_expired(cached.updatedAt, max_age_seconds=180):
                payload = json.loads(cached.forecastMatrixJson) if isinstance(cached.forecastMatrixJson, str) else cached.forecastMatrixJson
                if isinstance(payload, dict):
                    # Check if cached forecast payload contains old uncalibrated 0.0km proximity records
                    timeline = payload.get("timeline_matrix", [])
                    first_horizon_districts = timeline[0].get("district_matrix", []) if timeline else []
                    has_stale_zero_dist = any(d.get("district") == "Puri" and d.get("coastal_distance_km") == 0.0 for d in first_horizon_districts)
                    has_stale_utc = any("UTC" in str(t.get("timestamp_formatted", "")) for t in timeline)
                    has_stale_evac = any(t.get("horizon_hours") == 12 and t.get("total_state_evacuation_target", 0) == 0 for t in timeline)
                    if not has_stale_zero_dist and not has_stale_utc and not has_stale_evac:
                        payload["is_cached"] = True
                        payload["last_updated"] = cached.updatedAt.isoformat() if isinstance(cached.updatedAt, datetime) else str(cached.updatedAt)
                        return payload
                    else:
                        logger.info("Stale forecast cache detected in Neon DB. Forcing cache refresh...")
            elif cached:
                logger.info("Short-range forecast cache expired (>3m). Auto-refreshing live forecast...")
    except Exception as e:
        logger.warning(f"Failed to read short range forecast cache from Neon DB: {e}")

    fresh_data = predictive_engine.generate_48h_short_range_forecast(mode="simulated")

    try:
        from src.db.db import prisma
        if prisma is not None and prisma.is_connected():
            max_wind = fresh_data.get("projected_peak_landfall_wind_kt") or fresh_data.get("max_projected_wind_kt", 0.0)
            min_pressure = fresh_data.get("projected_min_landfall_pressure_hpa") or fresh_data.get("min_projected_pressure_hpa", 1000.0)
            etl_h = fresh_data.get("estimated_time_to_landfall_hours") if fresh_data.get("estimated_time_to_landfall_hours") is not None else fresh_data.get("landfall_est_hours")

            await _safe_prisma_op(
                prisma.shortrangeforecastcache.create(
                    data={
                        "warningStage": fresh_data.get("warning_stage", fresh_data.get("state_severity", "Normal Watch")),
                        "maxProjectedWindKt": float(max_wind),
                        "minProjectedPressureHpa": float(min_pressure),
                        "landfallEstHours": float(etl_h) if etl_h is not None else None,
                        "forecastMatrixJson": json.dumps(fresh_data),
                        "districtCurvesJson": json.dumps(fresh_data.get("district_risk_curves", [])),
                    }
                ),
                timeout=1.5
            )
            logger.info("Successfully updated ShortRangeForecastCache in Neon DB.")
    except Exception as e:
        logger.warning(f"Failed to update ShortRangeForecastCache in Neon DB: {e}")

    fresh_data["is_cached"] = False
    fresh_data["last_updated"] = datetime.now().isoformat()
    return fresh_data


async def get_or_refresh_15day_forecast(force_refresh: bool = False, mode: str = "simulated") -> Dict[str, Any]:
    """
    Returns latest cached 15-Day Extended Horizon Forecast from Neon DB.
    Auto-computes and rewrites Neon DB cache on refresh (TTL: 1 hour).
    """
    try:
        from src.db.db import prisma
        if prisma is not None and prisma.is_connected() and not force_refresh:
            cached = await _safe_prisma_op(prisma.seasonaloutlookcache.find_first(order={"updatedAt": "desc"}), timeout=1.5)
            if cached and not is_cache_expired(cached.updatedAt, max_age_seconds=3600):
                payload = json.loads(cached.districtRankingsJson) if isinstance(cached.districtRankingsJson, str) else cached.districtRankingsJson
                if isinstance(payload, dict) and "fifteen_day_matrix" in payload:
                    cached_mode = payload.get("operational_telemetry_mode", "simulated")
                    if cached_mode == mode:
                        payload["is_cached"] = True
                        payload["last_updated"] = cached.updatedAt.isoformat() if isinstance(cached.updatedAt, datetime) else str(cached.updatedAt)
                        return payload
            elif cached:
                logger.info("15-day forecast cache expired (>1h). Auto-refreshing...")
    except Exception as e:
        logger.warning(f"Failed to read 15-day forecast cache from Neon DB: {e}")

    from src.forecasting import predictive_engine
    fresh_data = predictive_engine.generate_15day_extended_forecast(mode=mode)
    fresh_data["operational_telemetry_mode"] = mode

    try:
        from src.db.db import prisma
        if prisma is not None and prisma.is_connected():
            await _safe_prisma_op(
                prisma.seasonaloutlookcache.create(
                    data={
                        "overallBasinActivityRisk": fresh_data.get("overall_15day_threat_level", "Critical"),
                        "districtRankingsJson": json.dumps(fresh_data),
                        "peakRiskWindowsJson": json.dumps(fresh_data.get("fifteen_day_readiness_phases", [])),
                    }
                ),
                timeout=1.5
            )
            logger.info("Successfully updated 15-Day Extended Forecast Cache in Neon DB.")
    except Exception as e:
        logger.warning(f"Failed to update 15-day forecast in Neon DB: {e}")

    fresh_data["is_cached"] = False
    fresh_data["last_updated"] = datetime.now().isoformat()
    return fresh_data


async def get_or_refresh_seasonal_outlook(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Backward-compatible wrapper returning the 15-Day Extended Forecast / Seasonal Outlook.
    """
    return await get_or_refresh_15day_forecast(force_refresh=force_refresh)



async def get_or_refresh_unified_survey(force_refresh: bool = False, mode: str = "simulated") -> Dict[str, Any]:
    """
    Returns latest cached Unified 5-Model Disaster Survey from Neon DB.
    If cache is older than 3 minutes or force_refresh is True, auto-recomputes fresh survey.
    Supports mode='simulated' and mode='live'.
    """
    from src.agent import unified_survey

    if mode == "live":
        fresh_data = unified_survey.generate_unified_live_survey(mode="live")
        fresh_data["is_cached"] = False
        fresh_data["last_updated"] = datetime.now().isoformat()
        return fresh_data

    try:
        from src.db.db import prisma
        if prisma is not None and prisma.is_connected() and not force_refresh:
            cached = await _safe_prisma_op(prisma.unifiedsurveycache.find_first(order={"updatedAt": "desc"}), timeout=1.5)
            if cached and not is_cache_expired(cached.updatedAt, max_age_seconds=180):
                payload = json.loads(cached.surveyMatrixJson) if isinstance(cached.surveyMatrixJson, str) else cached.surveyMatrixJson
                if isinstance(payload, dict):
                    # Check if cached payload contains old uncalibrated 0.0km proximity records
                    matrix = payload.get("district_survey_matrix", [])
                    has_stale_zero_dist = any(d.get("district") == "Puri" and d.get("coastal_distance_km") == 0.0 for d in matrix)
                    if not has_stale_zero_dist:
                        payload["is_cached"] = True
                        payload["last_updated"] = cached.updatedAt.isoformat() if isinstance(cached.updatedAt, datetime) else str(cached.updatedAt)
                        return payload
                    else:
                        logger.info("Stale cache with 0km coastal distances detected. Forcing Neon DB cache refresh...")
            elif cached:
                logger.info("Unified survey cache expired (>3m). Auto-refreshing live survey...")
    except Exception as e:
        logger.warning(f"Failed to read unified survey cache from Neon DB: {e}")

    fresh_data = unified_survey.generate_unified_live_survey(mode="simulated")

    try:
        from src.db.db import prisma
        if prisma is not None and prisma.is_connected():
            await _safe_prisma_op(
                prisma.unifiedsurveycache.create(
                    data={
                        "stateSeverity": fresh_data.get("overall_state_severity", "Normal"),
                        "maxWindSpeedKt": float(fresh_data.get("peak_coastal_wind_speed_kt", 0.0)),
                        "minPressureHpa": float(fresh_data.get("min_coastal_pressure_hpa", 1010.0)),
                        "surveyMatrixJson": json.dumps(fresh_data),
                    }
                ),
                timeout=1.5
            )
            logger.info("Successfully updated UnifiedSurveyCache in Neon DB.")
    except Exception as e:
        logger.warning(f"Failed to update UnifiedSurveyCache in Neon DB: {e}")

    fresh_data["is_cached"] = False
    fresh_data["last_updated"] = datetime.now().isoformat()
    return fresh_data
