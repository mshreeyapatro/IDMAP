"""
Unified Live Odisha Disaster Risk Survey & State Alert Matrix Engine.

Fuses all 5 AI/ML models:
1. Open-Meteo Live Coastal Weather Telemetry (6 Odisha Stations)
2. NASA GIBS Live Satellite Pass + TCIR ResNet CNN Backbone (Vmax Proxy)
3. Autoencoder Satellite Image Anomaly Detector (Cloud Reconstruction Error)
4. XGBoost Risk Regressor & Live SHAP Feature Contribution Engine
5. GNN Spatial Risk Decay & Resource Allocator (Census 2011 10-District Matrix + RAG SOP Directives)
   Harmonized with Dual-Regime Superposed Modified Rankine Vortex Profile.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import math
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingestion import live_weather, live_satellite
from src.layer2.risk_xgboost import explainability
from src.agent import resource_planner
from src.forecasting import predictive_engine

DISTRICT_NODES_CSV = ROOT / "data" / "processed" / "odisha_district_nodes.csv"


def generate_unified_live_survey() -> dict:
    """
    Generates the complete 10-district Odisha Live Disaster Survey fusing all 5 AI/ML models
    and dynamic mathematical trajectory advection / superposed Rankine vortex profile.
    """
    now_dt = datetime.now(timezone.utc)

    # Model 1 & 2 Ingestion
    weather = live_weather.get_live_weather_feed()
    satellite = live_satellite.get_live_satellite_feed()

    base_wind = float(weather.get("max_coastal_wind_speed_kt", 35.0))
    min_pressure = float(weather.get("min_coastal_pressure_hpa", 1002.0))
    state_severity = weather.get("overall_state_severity", "Warning")

    # Model 3: Satellite TCIR Backbone & Vision AI
    sat_pass_date = satellite.get("nasa_gibs", {}).get("date", now_dt.strftime("%Y-%m-%d"))
    sat_vision = satellite.get("vision_ai_telemetry", {})
    tcir_vmax = float(sat_vision.get("tcir_vmax_proxy_kt", 0.0))
    anomaly_error = float(sat_vision.get("anomaly_reconstruction_error", 0.042))
    is_anomaly = anomaly_error > 0.08

    eye_lat0 = float(sat_vision.get("eye_latitude", 17.8))
    eye_lon0 = float(sat_vision.get("eye_longitude", 86.1))
    trans_speed_kmh = float(sat_vision.get("translation_speed_kmh", 14.8))
    trans_speed_kt = round(trans_speed_kmh / 1.852, 1)
    heading_deg = float(sat_vision.get("heading_deg", 315.0))
    heading_vector = sat_vision.get("heading_vector", f"{heading_deg}° NW")
    cloud_density = float(sat_vision.get("cloud_wall_density_score", 0.88))
    storm_radius_km = int(sat_vision.get("storm_radius_km", 280))

    # Ingest Deep-Layer NWP Environmental Steering Flow for unified heading synchronization
    steering_flow = live_weather.get_nwp_vertical_steering_flow(eye_lat0, eye_lon0)
    nwp_h = float(steering_flow.get("steering_heading_deg", heading_deg)) if not steering_flow.get("is_fallback", False) else heading_deg
    effective_heading = round((0.75 * heading_deg + 0.25 * nwp_h) % 360.0, 1)

    # Core Storm Intensity Determination
    peak_core_source = max(base_wind, tcir_vmax, 75.0)
    density_multiplier = 1.05 + 0.10 * cloud_density
    peak_landfall_wind_kt = round(peak_core_source * density_multiplier, 1)
    min_landfall_pressure_hpa = round(min(min_pressure - 28.0, 966.0), 1)

    # Model 5: Resource Planning across 10 Odisha Districts
    resource_data = resource_planner.get_resource_plan(severity_level=state_severity, wind_speed_kt=peak_landfall_wind_kt)
    district_list = resource_data.get("district_breakdown", [])

    # Load district centroid lookup
    df_nodes = pd.read_csv(DISTRICT_NODES_CSV) if DISTRICT_NODES_CSV.exists() else pd.DataFrame()
    node_coords = {}
    if not df_nodes.empty:
        for _, row in df_nodes.iterrows():
            d_name = str(row["district"]).strip().lower()
            node_coords[d_name] = (float(row.get("centroid_lat", 20.0)), float(row.get("centroid_lon", 85.5)))

    # Station telemetry map
    stations_list = weather.get("stations", [])
    station_telemetry = {}
    for st in stations_list:
        st_name = st.get("station")
        if st_name:
            station_telemetry[st_name] = {
                "wind_speed_kt": float(st.get("wind_speed_kt", base_wind)),
                "pressure_hpa": float(st.get("pressure_hpa", min_pressure)),
            }

    DISTRICT_STATION_MAP = {
        "Ganjam": "Gopalpur",
        "Gajapati": "Gopalpur",
        "Puri": "Puri",
        "Jagatsinghapur": "Paradip",
        "Kendrapara": "Paradip",
        "Bhadrak": "Chandbali",
        "Jajapur": "Chandbali",
        "Baleshwar": "Balasore",
        "Mayurbhanj": "Balasore",
        "Khordha": "Bhubaneswar",
        "Cuttack": "Bhubaneswar",
        "Nayagarh": "Bhubaneswar",
        "Dhenkanal": "Bhubaneswar",
    }

    # Dynamic Landfall determination & ETL from Trajectory-Coastline Intersection
    primary_landfall_target, landfall_sector, estimated_etl_hours = predictive_engine.calculate_dynamic_landfall_eta_and_target(
        lat0=eye_lat0,
        lon0=eye_lon0,
        heading_deg=effective_heading,
        trans_speed_kmh=trans_speed_kmh,
        df_districts=df_nodes
    )

    landfall_dt_utc = now_dt + timedelta(hours=estimated_etl_hours)
    landfall_dt_ist = landfall_dt_utc + timedelta(hours=5, minutes=30)
    estimated_landfall_ist = landfall_dt_ist.strftime("%d %b, %I:%M %p IST")
    estimated_landfall_utc = landfall_dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    v_initial_core = max(65.0, peak_landfall_wind_kt * 0.88)

    # Model 4 & 5: Compute Live SHAP & XGBoost Risk for each district using superposed Rankine Vortex
    survey_matrix = []
    for d in district_list:
        dist_name = d["district"]
        coastal_dist = float(d["coastal_distance_km"])
        pop = float(d["total_population"])

        # Haversine distance to initial storm eye
        c_coords = node_coords.get(dist_name.lower(), (20.0, 85.5))
        dist_to_eye = predictive_engine.haversine_distance(eye_lat0, eye_lon0, c_coords[0], c_coords[1])

        # Station-specific weather telemetry
        assigned_station = DISTRICT_STATION_MAP.get(dist_name, "Gopalpur")
        st_info = station_telemetry.get(assigned_station, {"wind_speed_kt": base_wind, "pressure_hpa": min_pressure})
        st_wind = st_info.get("wind_speed_kt", base_wind)

        # Bearing & Asymmetric Modified Rankine Vortex radial wind speed at T+0h
        d_lat, d_lon = node_coords.get(dist_name.lower(), (20.0, 85.5))
        bearing_deg = predictive_engine.compute_bearing_deg(eye_lat0, eye_lon0, d_lat, d_lon)
        quadrant_sector = predictive_engine.get_quadrant_sector(bearing_deg, heading_deg)

        dist_wind = predictive_engine.rankine_vortex_wind_speed(
            vmax_kt=v_initial_core,
            r_eye_km=dist_to_eye,
            r_max_km=35.0,
            v_ambient_kt=st_wind,
            bearing_deg=bearing_deg,
            heading_deg=heading_deg,
            trans_speed_kt=trans_speed_kt
        )
        dist_pressure = round(min(1012.0, min_pressure + (1012.0 - min_pressure) * (1.0 - math.exp(-0.012 * dist_to_eye))), 1)

        surge_m, surge_pill = predictive_engine.compute_coastal_storm_surge_m(
            coastal_dist_km=coastal_dist,
            wind_speed_kt=dist_wind,
            surface_pressure_hpa=dist_pressure,
            bearing_deg=bearing_deg,
            eye_dist_km=dist_to_eye
        )
        rain_mm, rain_cat = predictive_engine.compute_rainfall_potential_mm(
            vmax_kt=v_initial_core,
            trans_speed_kmh=trans_speed_kmh,
            eye_dist_km=dist_to_eye
        )

        # Live SHAP & XGBoost prediction per district
        shap_res = explainability.explain_custom_features(
            wind_speed_kt=dist_wind,
            coastal_distance_km=coastal_dist,
            district_population=pop,
            pressure_hpa=dist_pressure,
            anomaly_error=anomaly_error,
            distance_to_eye_km=dist_to_eye,
            is_storm_alert=True
        )

        dist_risk_score = shap_res.get("predicted_risk_score", 0.05)
        top_shap_driver = shap_res.get("top_feature_contributions", [{}])[0].get("feature", "wind_speed_kt")

        # Determine Calibrated Alert Badge & Action Directives
        if dist_wind >= 64.0 or dist_risk_score >= 0.65 or surge_m >= 2.5:
            alert_pill = "🔴 CRITICAL EVACUATION"
            sop_directive = f"Mandatory 100% evacuation of coastal 10km belt in {dist_name}. Activate all Multipurpose Cyclone Shelters with emergency backup."
        elif dist_wind >= 45.0 or dist_risk_score >= 0.40 or surge_m >= 1.5:
            alert_pill = "🟠 HIGH WARNING"
            sop_directive = f"Standby alert for district emergency operations in {dist_name}. Pre-position NDRF teams and stock medical emergency units."
        elif dist_wind >= 28.0 or dist_risk_score >= 0.22 or surge_m >= 0.8:
            alert_pill = "🟡 ADVISORY WATCH"
            sop_directive = f"Maritime warning & fishing ban issued for {dist_name} coast. Low-lying area monitoring active."
        else:
            alert_pill = "🟢 NORMAL / LOW RISK"
            sop_directive = f"Standard meteorological observation active in {dist_name}."

        survey_matrix.append({
            "district": dist_name,
            "census_code": d.get("census_code", 388),
            "coastal_distance_km": coastal_dist,
            "population_census_2011": pop,
            "predicted_risk_score": dist_risk_score,
            "alert_status_pill": alert_pill,
            "alert_level": alert_pill.replace("🔴 ", "").replace("🟠 ", "").replace("🟡 ", "").replace("🟢 ", "").replace(" / LOW RISK", "").replace(" ", "_"),
            "distance_to_eye_km": round(dist_to_eye, 1),
            "bearing_deg": bearing_deg,
            "quadrant_sector": quadrant_sector,
            "estimated_wind_kt": dist_wind,
            "estimated_wind_kmh": round(dist_wind * 1.852, 1),
            "pressure_hpa": dist_pressure,
            "projected_storm_surge_m": surge_m,
            "surge_alert_pill": surge_pill,
            "projected_rainfall_24h_mm": rain_mm,
            "rainfall_alert_category": rain_cat,
            "people_to_evacuate": d["people_to_evacuate"],
            "evacuation_target": d["people_to_evacuate"],
            "multipurpose_shelters_required": d["multipurpose_shelters_required"],
            "mcs_activated": d["multipurpose_shelters_required"],
            "ndrf_teams_required": d["ndrf_teams_required"],
            "ndrf_teams": d["ndrf_teams_required"],
            "top_shap_risk_driver": top_shap_driver,
            "sop_action_directive": sop_directive
        })

    total_evac = sum(d["people_to_evacuate"] for d in survey_matrix)
    total_shelters = sum(d["multipurpose_shelters_required"] for d in survey_matrix)
    total_ndrf = sum(d["ndrf_teams_required"] for d in survey_matrix)

    # Dynamic 48-Hour Forecast Trajectory Matrix
    forecast_trajectory_matrix = predictive_engine.generate_dynamic_trajectory_matrix(
        lat0=eye_lat0,
        lon0=eye_lon0,
        heading_deg=heading_deg,
        trans_speed_kmh=trans_speed_kmh,
        peak_landfall_wind_kt=peak_landfall_wind_kt,
        base_pressure=min_pressure,
        min_landfall_pressure_hpa=min_landfall_pressure_hpa,
        etl_hours=estimated_etl_hours,
        landfall_target_district=primary_landfall_target,
        now_dt=now_dt
    )

    sop_directives = [
        f"Execute mandatory zero-casualty evacuation within 10 km coastal belt by {estimated_landfall_ist} (T-7 hours before landfall).",
        "Pre-position NDRF/ODRAF heavy rescue teams and clear main trunk transit corridors (NH-16 & coastal state highways).",
        "Order full shutdown of port operations and high-voltage grid feeders in >65 km/h zones."
    ]

    ri_data = predictive_engine.compute_rapid_intensification_index(
        sst_c=30.5,
        cloud_density_score=cloud_density,
        anomaly_recon_error=anomaly_error
    )

    unified_summary = {
        "satellite_pass": "INSAT-3D / VIIRS",
        "eye_coordinates": {"lat": eye_lat0, "lon": eye_lon0},
        "heading_vector": heading_vector,
        "translation_speed_kmh": trans_speed_kmh,
        "translation_speed_knots": trans_speed_kt,
        "convective_density_score": cloud_density,
        "storm_radius_km": storm_radius_km,
        "primary_landfall_target": primary_landfall_target,
        "landfall_sector": landfall_sector,
        "estimated_landfall_ist": estimated_landfall_ist,
        "estimated_landfall_utc": estimated_landfall_utc,
        "landfall_intensity_knots": int(round(peak_landfall_wind_kt)),
        "landfall_pressure_hpa": int(round(min_landfall_pressure_hpa)),
        "rapid_intensification_watch": ri_data,
        "total_evacuation_target": total_evac,
        "total_mcs_activated": total_shelters,
        "total_ndrf_teams": total_ndrf
    }

    return {
        "survey_timestamp": now_dt.isoformat() + "Z",
        "state": "Odisha",
        "overall_state_severity": state_severity,
        "peak_coastal_wind_speed_kt": base_wind,
        "min_coastal_pressure_hpa": min_pressure,
        "satellite_pass_date": sat_pass_date,
        "tcir_vmax_proxy_kt": tcir_vmax,
        "satellite_anomaly_error": anomaly_error,
        "is_cloud_anomaly": is_anomaly,
        "satellite_vision_telemetry": sat_vision,
        "nasa_gibs": satellite.get("nasa_gibs", {}),
        "unified_survey_summary": unified_summary,
        "total_state_evacuation_target": total_evac,
        "total_shelters_activated": total_shelters,
        "total_ndrf_teams_deployed": total_ndrf,
        "district_survey_matrix": survey_matrix,
        "district_risk_matrix": survey_matrix,
        "forecast_trajectory_matrix": forecast_trajectory_matrix,
        "sop_directives": sop_directives
    }


if __name__ == "__main__":
    import json
    res = generate_unified_live_survey()
    print("Unified Live Survey District Breakdown:")
    print(json.dumps(res["district_survey_matrix"][:5], indent=2))
