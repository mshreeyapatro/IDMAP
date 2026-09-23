"""
Unit and Integration Tests for Advanced Cyclone Physics & Data Assimilation Sub-Engines.
Covers:
1. Deep-Layer NWP Environmental Steering Flow Ingestion & Advection.
2. Double-Rankine Eyewall Replacement Cycle (ERC) Concentric Vortex Profile.
3. 1D Subsurface Ocean Cold-Wake Dynamics & Emanuel MPI Limit.
4. Coastal Doppler Weather Radar (DWR) Assimilation & Kalman Nudging.
"""

import pytest
import math
from src.ingestion import live_weather
from src.forecasting import predictive_engine


def test_nwp_vertical_steering_flow():
    steering = live_weather.get_nwp_vertical_steering_flow(lat=19.5, lon=86.2)
    assert "steering_heading_deg" in steering
    assert "steering_speed_kmh" in steering
    assert "u_steering_ms" in steering
    assert "v_steering_ms" in steering
    assert 0.0 <= steering["steering_heading_deg"] <= 360.0
    assert steering["steering_speed_kmh"] >= 4.0


def test_advect_eye_position_with_steering():
    lat0, lon0 = 19.5, 86.2
    heading0 = 315.0
    speed0 = 15.0

    mock_steering = {
        "steering_heading_deg": 320.0,
        "steering_speed_kmh": 18.0,
        "is_fallback": False
    }

    lat_h, lon_h, heading_h = predictive_engine.advect_eye_position(
        lat0=lat0, lon0=lon0, heading_deg=heading0, speed_kmh=speed0,
        hours=6.0, enable_recurvature=True, steering_flow=mock_steering
    )

    assert lat_h > lat0
    assert lon_h < lon0
    assert 0.0 <= heading_h <= 360.0


def test_double_rankine_erc_vortex():
    vmax = 90.0
    r_core = 25.0
    r_outer = 70.0

    # At inner core maximum, wind should be near peak
    v_inner = predictive_engine.double_rankine_vortex_wind_speed(
        vmax_kt=vmax, r_eye_km=r_core, r_max1_km=25.0, r_max2_km=70.0, w_erc=0.30
    )
    assert v_inner >= 70.0

    # At secondary outer eyewall (70 km), Double-Rankine should produce significantly
    # higher gale winds than a standard decaying single-Rankine vortex profile
    v_erc_outer = predictive_engine.double_rankine_vortex_wind_speed(
        vmax_kt=vmax, r_eye_km=r_outer, r_max1_km=25.0, r_max2_km=70.0, w_erc=0.50
    )
    v_single_outer = predictive_engine.rankine_vortex_wind_speed(
        vmax_kt=vmax, r_eye_km=r_outer, r_max_km=25.0
    )

    assert v_erc_outer > v_single_outer
    assert v_erc_outer >= 50.0  # Demonstrating outer wind field expansion


def test_ocean_cold_wake_dynamics():
    # Fast moving storm (18 km/h): small cooling drop
    fast_wake = predictive_engine.compute_ocean_cold_wake_attenuation(
        vmax_kt=85.0, trans_speed_kmh=18.0, mixed_layer_depth_m=50.0, sst_c=30.5
    )
    assert fast_wake["cold_wake_cooling_drop_c"] > -1.5
    assert not fast_wake["is_cold_wake_suppression_active"]
    assert fast_wake["capped_vmax_kt"] == 85.0

    # Stalling storm (6 km/h) over shallow mixed layer (25 m): intense cold wake
    slow_wake = predictive_engine.compute_ocean_cold_wake_attenuation(
        vmax_kt=110.0, trans_speed_kmh=6.0, mixed_layer_depth_m=20.0, sst_c=29.0
    )
    assert slow_wake["cold_wake_cooling_drop_c"] <= -1.2
    assert slow_wake["is_cold_wake_suppression_active"]
    assert slow_wake["sst_effective_c"] < 28.0


def test_dwr_radar_assimilation():
    # Out of radar range (> 350 km)
    out_range = predictive_engine.assimilate_dwr_radar_fix(lat_eye=15.0, lon_eye=88.0, coastal_dist_km=450.0)
    assert not out_range["is_radar_in_range"]
    assert out_range["position_uncertainty_km"] == 25.0

    # In coastal radar range near Gopalpur DWR (19.31N, 84.97E)
    in_range = predictive_engine.assimilate_dwr_radar_fix(lat_eye=19.45, lon_eye=85.20, coastal_dist_km=35.0)
    assert in_range["is_radar_in_range"]
    assert in_range["radar_site_active"] == "Gopalpur_DWR"
    assert in_range["position_uncertainty_km"] == 4.0
    assert abs(in_range["assimilated_lat"] - 19.45) < 0.10


def test_short_range_forecast_with_advanced_physics():
    res = predictive_engine.generate_48h_short_range_forecast()
    assert res["mode"] == "short_range_48h"
    assert "ocean_cold_wake_dynamics" in res
    assert "nwp_environmental_steering" in res
    assert "probabilistic_ensemble" in res
    assert "predicted_landfall_target_district" in res
    assert res["predicted_landfall_target_district"] in ["Puri", "Ganjam", "Jagatsinghapur", "Kendrapara", "Bhadrak", "Baleshwar"]
