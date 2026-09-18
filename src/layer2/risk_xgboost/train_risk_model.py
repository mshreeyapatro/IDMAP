"""
Phase 5: XGBoost Risk Model & Intensity Classification (SRS Section 8).

Trains a Risk Prediction and Cyclone Severity Classifier using fused TCIR satellite
embeddings, meteorological proxies, coastal proximity, and district exposure features.

Output:
- Saved checkpoint in src/layer2/risk_xgboost/checkpoints/risk_model.pkl
- Risk evaluation summary saved in reports/risk_model_metrics.json
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor
from sklearn.metrics import classification_report, mean_squared_error, r2_score

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

ROOT = Path(__file__).resolve().parents[3]
MASTER_CSV = ROOT / "data" / "processed" / "master_cyclone_dataset.csv"
ANOMALY_CSV = ROOT / "data" / "processed" / "insat3d_anomaly_scores.csv"
CHECKPOINT_DIR = ROOT / "src" / "layer2" / "risk_xgboost" / "checkpoints"
REPORTS_DIR = ROOT / "reports"


def derive_risk_score(row: pd.Series) -> float:
    """
    Computes ground-truth risk proxy (0.0 to 1.0) combining:
    - Wind speed intensity (vmax proxy or best track wind speed)
    - Coastal proximity factor (closer to coast = higher vulnerability)
    - District population exposure index
    """
    wind = row.get("wind_speed_kt")
    if pd.isna(wind):
        wind = max(row.get("raw_tcir_vmax_proxy_kt_mean", 30), row.get("infrared_tcir_vmax_proxy_kt_mean", 30))
    
    # Wind risk score normalized [0, 150kt]
    wind_score = min(1.0, max(0.0, wind / 150.0))

    # Coastal proximity score (1.0 at coast, 0.0 at 1000km away)
    dist = row.get("coastal_distance_km")
    if pd.isna(dist):
        dist = 500.0
    coastal_score = max(0.0, 1.0 - (dist / 1000.0))

    # Exposure score from population
    pop = row.get("district_population")
    if pd.isna(pop):
        pop_score = 0.5
    else:
        pop_score = min(1.0, pop / 3000000.0)

    # Risk weights: 55% Wind Intensity, 30% Coastal Distance, 15% Population Exposure
    risk = 0.55 * wind_score + 0.30 * coastal_score + 0.15 * pop_score
    return float(np.clip(risk, 0.0, 1.0))


def derive_intensity_category(wind_kt: float) -> str:
    if wind_kt < 34:
        return "Depression"
    elif wind_kt < 48:
        return "Deep Depression"
    elif wind_kt < 64:
        return "Cyclonic Storm"
    elif wind_kt < 90:
        return "Severe Cyclonic Storm"
    else:
        return "Super Cyclonic Storm"


def prepare_features():
    df_master = pd.read_csv(MASTER_CSV)
    df_anomaly = pd.read_csv(ANOMALY_CSV)

    # Average anomaly score per base_id
    anom_summary = df_anomaly.groupby("base_id")["reconstruction_error"].mean().reset_index()
    anom_summary.rename(columns={"reconstruction_error": "mean_anomaly_reconstruction_error"}, inplace=True)

    df = pd.merge(df_master, anom_summary, left_on="cyclone_id", right_on="base_id", how="left")

    # Target continuous risk & categorical intensity
    df["risk_score"] = df.apply(derive_risk_score, axis=1)
    
    def get_effective_wind(row):
        w = row.get("wind_speed_kt")
        if pd.isna(w):
            w = max(row.get("raw_tcir_vmax_proxy_kt_mean", 30), row.get("infrared_tcir_vmax_proxy_kt_mean", 30))
        return w

    df["effective_wind_kt"] = df.apply(get_effective_wind, axis=1)
    df["intensity_category"] = df["effective_wind_kt"].apply(derive_intensity_category)

    # Extract feature columns
    embed_cols = sorted([c for c in df.columns if c.startswith("embed_")])
    feature_cols = embed_cols + [
        "raw_tcir_vmax_proxy_kt_mean",
        "infrared_tcir_vmax_proxy_kt_mean",
        "mean_anomaly_reconstruction_error",
        "coastal_distance_km",
        "district_population",
    ]

    X = df[feature_cols].copy()
    # Fill missing values cleanly
    X.fillna(X.median(numeric_only=True), inplace=True)
    X.fillna(0.0, inplace=True)

    y_risk = df["risk_score"].values
    y_cat = df["intensity_category"].values

    return df, X, feature_cols, y_risk, y_cat


def train():
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df, X, feature_cols, y_risk, y_cat = prepare_features()

    print(f"Dataset shape: {X.shape}, Features: {len(feature_cols)}")

    if HAS_XGB:
        print("Using XGBoost Regressor...")
        model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
    else:
        print("XGBoost not available; using RandomForestRegressor fallback...")
        model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)

    model.fit(X, y_risk)
    y_pred = model.predict(X)

    r2 = float(r2_score(y_risk, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_risk, y_pred)))

    print(f"Risk Model Trained -- R2 Score: {r2:.4f}, RMSE: {rmse:.4f}")

    # Feature Importance
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    else:
        importances = np.ones(len(feature_cols)) / len(feature_cols)

    feat_imp = sorted(zip(feature_cols, [float(x) for x in importances]), key=lambda x: x[1], reverse=True)

    # Save Checkpoint
    checkpoint_path = CHECKPOINT_DIR / "risk_model.pkl"
    with open(checkpoint_path, "wb") as f:
        pickle.dump({
            "model": model,
            "feature_cols": feature_cols,
            "r2_score": r2,
            "rmse": rmse,
            "has_xgb": HAS_XGB
        }, f)

    # Save Metrics Report
    metrics = {
        "r2_score": r2,
        "rmse": rmse,
        "n_samples": len(X),
        "has_xgb": HAS_XGB,
        "top_features": feat_imp[:10]
    }
    with open(REPORTS_DIR / "risk_model_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Checkpoint saved to {checkpoint_path}")
    return metrics


if __name__ == "__main__":
    train()
