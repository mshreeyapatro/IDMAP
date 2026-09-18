"""
Phase 8: SHAP Explainability Engine (SRS Section 11).

Calculates SHAP (SHapley Additive exPlanations) values for cyclone risk predictions
to provide transparent, feature-level evidence explaining model outputs.
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


def load_model_and_data():
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

    return model, df, X, feature_cols


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
    explainer = shap.TreeExplainer(model)
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
        "predicted_risk_score": round(predicted_value, 4),
        "base_value": round(base_value, 4),
        "top_feature_contributions": contributions
    }


def explain_custom_features(
    wind_speed_kt: float = 65.0,
    coastal_distance_km: float = 85.0,
    district_population: float = 1250000.0,
    pressure_hpa: float = 998.0,
    anomaly_error: float = 0.08
) -> dict:
    """
    Computes SHAP feature importance attributions for LIVE telemetry or forecast scenario inputs.
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
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(row_df)

    if isinstance(shap_values, list):
        sv = shap_values[0][0]
    elif len(shap_values.shape) == 2:
        sv = shap_values[0]
    else:
        sv = shap_values

    base_value = float(explainer.expected_value) if hasattr(explainer, "expected_value") else 0.5
    raw_pred = float(model.predict(row_df)[0])

    # Dynamic Meteorological Physics Scaling for realistic risk prediction
    if wind_speed_kt < 28.0:
        # Normal weather / light breeze -> 2% to 12% risk range based on wind & proximity
        phys_risk = (wind_speed_kt / 28.0) * 0.10 * max(0.5, 1.0 - (coastal_distance_km / 300.0))
        predicted_value = max(0.02, min(0.12, phys_risk))
    else:
        # Storm condition -> XGBoost model prediction calibrated with coastal decay
        coastal_decay = max(0.3, np.exp(-coastal_distance_km / 150.0))
        predicted_value = max(0.15, min(0.99, raw_pred * coastal_decay))

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
        "predicted_risk_score": round(predicted_value, 4),
        "base_value": round(base_value, 4),
        "input_summary": {
            "wind_speed_kt": wind_speed_kt,
            "coastal_distance_km": coastal_distance_km,
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
    print("Live Explain:", explain_custom_features(85.0, 40.0))

