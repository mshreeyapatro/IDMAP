"""
Unit and Integration Tests for Dual-Horizon Forecasting Engine (Phase 12).
"""

import pytest
from src.forecasting import predictive_engine


def test_48h_short_range_forecast():
    res = predictive_engine.generate_48h_short_range_forecast()
    assert res["mode"] == "short_range_48h"
    assert "timeline_matrix" in res
    assert len(res["timeline_matrix"]) >= 7
    
    # Verify satellite image analysis integration
    assert "satellite_telemetry" in res
    sat_telemetry = res["satellite_telemetry"].get("vision_ai_telemetry", {})
    assert "eye_latitude" in sat_telemetry
    assert "eye_longitude" in sat_telemetry
    assert "tcir_vmax_proxy_kt" in sat_telemetry
    assert "satellite_landfall_proximity_km" in sat_telemetry

    # Verify dynamic trajectory matrix & probabilistic ensemble
    assert "forecast_trajectory_matrix" in res
    assert len(res["forecast_trajectory_matrix"]) >= 5
    assert "probabilistic_ensemble" in res
    assert "probabilistic_district_matrix" in res["probabilistic_ensemble"]
    t0_coord = res["forecast_trajectory_matrix"][0]["coordinates"]
    assert "lat" in t0_coord and "lon" in t0_coord

    first_step = res["timeline_matrix"][0]
    assert first_step["horizon_hours"] == 0
    assert "district_matrix" in first_step
    assert len(first_step["district_matrix"]) >= 10
    assert "distance_to_storm_center_km" in first_step["district_matrix"][0]


def test_60day_seasonal_outlook():
    res = predictive_engine.generate_60day_seasonal_outlook()
    assert res["mode"] == "seasonal_outlook_60day"
    assert "monthly_cyclonogenesis_probabilities" in res
    assert len(res["monthly_cyclonogenesis_probabilities"]) == 2
    assert "district_vulnerability_rankings" in res
    assert len(res["district_vulnerability_rankings"]) >= 10
    assert "climate_teleconnections" in res
    assert "eight_week_timeline" in res
    assert len(res["eight_week_timeline"]) == 8
    assert "intensity_distribution" in res
    assert "historical_analog_events" in res
    assert "state_resource_plan" in res
    assert "preseason_readiness_checklist" in res


def test_15day_extended_forecast():
    res = predictive_engine.generate_15day_extended_forecast()
    assert res["mode"] == "extended_forecast_15day"
    assert "fifteen_day_matrix" in res
    assert len(res["fifteen_day_matrix"]) == 15
    assert "fifteen_day_trajectory" in res
    assert len(res["fifteen_day_trajectory"]) == 15
    assert "multi_model_ensemble" in res
    assert "models" in res["multi_model_ensemble"]
    
    # Check Day 1 genesis
    day1 = res["fifteen_day_matrix"][0]
    assert day1["day_index"] == 1
    assert "district_matrix" in day1
    assert len(day1["district_matrix"]) >= 10
    assert "coordinates" in res["fifteen_day_trajectory"][0]
    
    # Check Day 8 Landfall Peak
    day8 = res["fifteen_day_matrix"][7]
    assert day8["day_index"] == 8
    assert day8["threat_tier"] == "CRITICAL PEAK"
    assert day8["projected_peak_wind_kmh"] >= 140.0

