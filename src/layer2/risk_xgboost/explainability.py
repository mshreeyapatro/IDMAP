"""
Phase 8: SHAP Explainability Engine (SRS Section 11).

Calculates SHAP (SHapley Additive exPlanations) values for cyclone risk predictions
to provide transparent, feature-level evidence explaining model outputs.
Includes Dual-Regime Meteorological Scaling (Baseline Coastal Marine Exposure in calm weather
vs. Dynamic Vortex Hazard & Eye Proximity during active storm alerts).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pickle
import numpy as np
import pandas as pd
import shap

CHECKPOINT_PATH = ROOT / "src" / "layer2" / "risk_xgboost" / "checkpoints" / "risk_model.pkl"
MASTER_CSV = ROOT / "data" / "processed" / "master_cyclone_dataset.csv"
ANOMALY_CSV = ROOT / "data" / "processed" / "insat3d_anomaly_scores.csv"


_CACHED_MODEL_DATA = None
_CACHED_EXPLAINER = None


def load_model_and_data():
    global _CACHED_MODEL_DATA
    if _CACHED_MODEL_DATA is not None:
        return _CACHED_MODEL_DATA

    if not CHECKPOINT_PATH.exists():
        from src.layer2.risk_xgboost.train_risk_model import train
        train()

    with open(CHECKPOINT_PATH, "rb") as f:
        data = pickle.load(f)
    model = data["model"]
    feature_cols = data["feature_cols"]

    # Re-build row features
    from src.layer2.risk_xgboost.train_risk_model import prepare_features
    df, X, _, _, _ = prepare_features()

    _CACHED_MODEL_DATA = (model, df, X, feature_cols)
    return _CACHED_MODEL_DATA


def get_explainer(model):
    global _CACHED_EXPLAINER
    if _CACHED_EXPLAINER is None:
        _CACHED_EXPLAINER = shap.TreeExplainer(model)
    return _CACHED_EXPLAINER


def explain_event(base_id: int) -> dict:
    """
    Computes SHAP feature importance attribution for a specific cyclone base_id.
    """
    model, df, X, feature_cols = load_model_and_data()

    match = df[df["cyclone_id"] == base_id]
    if match.empty:
        return {"error": f"Event {base_id} not found."}

    idx = match.index[0]
    row_X = X.loc[[idx]]

    # SHAP Explainer
    explainer = get_explainer(model)
    shap_values = explainer.shap_values(row_X)

    if isinstance(shap_values, list):
        sv = shap_values[0][0]
    elif len(shap_values.shape) == 2:
        sv = shap_values[0]
    else:
        sv = shap_values

    base_value = float(explainer.expected_value) if hasattr(explainer, "expected_value") else 0.5
    predicted_value = float(model.predict(row_X)[0])

    contributions = []
    for col, val, shap_val in zip(feature_cols, row_X.iloc[0], sv):
        contributions.append({
            "feature": col,
            "feature_value": float(val) if not pd.isna(val) else 0.0,
            "shap_value": float(shap_val),
            "impact": "increases_risk" if shap_val > 0 else "decreases_risk"
        })

    # Sort contributions by magnitude of SHAP value
    contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

    return {
        "base_id": base_id,
        "storm_name": match.iloc[0].get("matched_storm_name") or f"Cyclone #{base_id}",
        "predicted_risk_score": float(round(predicted_value, 4)),
        "base_value": float(round(base_value, 4)),
        "top_feature_contributions": contributions
    }


def explain_custom_features(
    wind_speed_kt: float = 65.0,
    coastal_distance_km: float = 85.0,
    district_population: float = 1250000.0,
    pressure_hpa: float = 998.0,
    anomaly_error: float = 0.08,
    distance_to_eye_km: float | None = None,
    is_storm_alert: bool = True
) -> dict:
    """
    Computes SHAP feature importance attributions for LIVE telemetry or forecast scenario inputs
    with Dual-Regime Meteorological Scaling:
    - Mode 1 (Calm Weather): Distance to coast (d_coast) governs baseline marine exposure (1% - 10%).
    - Mode 2 (Active Cyclone Alert): Actual wind hazard (v^2) & Distance to moving eye (d_eye) govern dynamic risk (15% - 95%).
    """
    model, df, X, feature_cols = load_model_and_data()

    # Zero out template row embeddings to avoid historical event bias
    template_row = pd.Series(0.0, index=feature_cols)

    if "raw_tcir_vmax_proxy_kt_mean" in feature_cols:
        template_row["raw_tcir_vmax_proxy_kt_mean"] = float(wind_speed_kt)
    if "infrared_tcir_vmax_proxy_kt_mean" in feature_cols:
        template_row["infrared_tcir_vmax_proxy_kt_mean"] = float(wind_speed_kt)
    if "coastal_distance_km" in feature_cols:
        template_row["coastal_distance_km"] = float(coastal_distance_km)
    if "district_population" in feature_cols:
        template_row["district_population"] = float(district_population)
    if "mean_anomaly_reconstruction_error" in feature_cols:
        template_row["mean_anomaly_reconstruction_error"] = float(anomaly_error)

    row_df = pd.DataFrame([template_row], columns=feature_cols)

    # SHAP Explainer
    explainer = get_explainer(model)
    shap_values = explainer.shap_values(row_df)

    if isinstance(shap_values, list):
        sv = shap_values[0][0]
    elif len(shap_values.shape) == 2:
        sv = shap_values[0]
    else:
        sv = shap_values

    base_value = float(explainer.expected_value) if hasattr(explainer, "expected_value") else 0.5
    raw_pred = float(model.predict(row_df)[0])

    # Determine effective distance to storm center
    effective_eye_dist = float(distance_to_eye_km) if distance_to_eye_km is not None else float(coastal_distance_km)

    # Dual-Regime Meteorological Risk Scaling
    if not is_storm_alert and wind_speed_kt < 28.0:
        # MODE 1: Baseline Coastal Marine Exposure (Calm Weather)
        # Risk scales with proximity to the shoreline (d_coast)
        coastal_decay = max(0.10, np.exp(-coastal_distance_km / 120.0))
        phys_risk = (wind_speed_kt / 28.0) * 0.08 * coastal_decay
        predicted_value = max(0.01, min(0.10, phys_risk))
    else:
        # MODE 2: Dynamic Vortex Hazard (Active Cyclone Alert / Forecast Tracking)
        # Risk is driven by actual wind kinetic energy (v^1.4 / v^2) calibrated to IMD gale thresholds
        # 64+ kt (VSCS/Eyewall) -> 65-95% (Critical Evacuation)
        # 45-63 kt (SCS/Gale) -> 40-64% (High Warning)
        # 28-44 kt (CS/Squall) -> 22-39% (Advisory Watch)
        # < 28 kt (Depression/Breeze) -> < 22% (Normal/Low Risk)
        hazard_score = min(1.0, (wind_speed_kt / 64.0) ** 1.35)
        eye_decay = max(0.15, np.exp(-effective_eye_dist / 140.0))
        exposure_score = min(1.0, max(0.15, float(district_population) / 3500000.0))

        # Dynamic fusion: 72% Wind Kinetic Hazard, 16% XGBoost Satellite Model, 12% Population Exposure
        fused_risk = (
            0.72 * hazard_score +
            0.16 * (raw_pred * eye_decay) +
            0.12 * (exposure_score * eye_decay)
        )
        predicted_value = max(0.04, min(0.98, fused_risk))

    contributions = []
    for col, val, shap_val in zip(feature_cols, row_df.iloc[0], sv):
        if col.startswith("embed_"):
            continue
        contributions.append({
            "feature": col,
            "feature_value": float(val) if not pd.isna(val) else 0.0,
            "shap_value": float(shap_val),
            "impact": "increases_risk" if shap_val > 0 else "decreases_risk"
        })

    contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

    return {
        "mode": "live_forecast",
        "predicted_risk_score": float(round(predicted_value, 4)),
        "base_value": float(round(base_value, 4)),
        "input_summary": {
            "wind_speed_kt": wind_speed_kt,
            "coastal_distance_km": coastal_distance_km,
            "distance_to_eye_km": effective_eye_dist,
            "district_population": district_population,
            "pressure_hpa": pressure_hpa
        },
        "top_feature_contributions": contributions
    }


if __name__ == "__main__":
    import sys
    base_id = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    res = explain_event(base_id)
    print("Event Explain:", res)
    print("Live Explain (Active Storm):", explain_custom_features(wind_speed_kt=48.1, coastal_distance_km=116.7, distance_to_eye_km=85.9, is_storm_alert=True))
    print("Live Explain (Calm Weather):", explain_custom_features(wind_speed_kt=14.0, coastal_distance_km=2.5, is_storm_alert=False))
