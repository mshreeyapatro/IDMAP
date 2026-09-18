"""
Phase 9: What-if Simulation Engine (SRS Section 12).

Simulates dynamic cyclone scenario modifications (e.g., changes in wind speed,
coastal distance, landfall trajectory) and predicts shifted risk profiles.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.layer2.risk_xgboost.train_risk_model import derive_risk_score, derive_intensity_category
from src.layer2.risk_xgboost.explainability import explain_event
from src.agent.tools import get_event_summary


def simulate_whatif(
    base_id: int,
    delta_wind_speed_kt: float = 0.0,
    new_coastal_distance_km: float | None = None,
    new_district: str | None = None
) -> dict:
    """
    Simulates modifications to a cyclone event and evaluates risk changes.
    """
    event = get_event_summary(base_id)
    if "error" in event:
        return {"error": event["error"]}

    # Baseline values
    orig_wind = event.get("wind_speed_kt") or event.get("raw_tcir_vmax_proxy_kt") or 45.0
    orig_dist = event.get("coastal_distance_km") if event.get("coastal_distance_km") is not None else 350.0
    orig_pop = event.get("district_population") or 1500000.0

    # Simulated values
    sim_wind = max(10.0, orig_wind + delta_wind_speed_kt)
    sim_dist = new_coastal_distance_km if new_coastal_distance_km is not None else orig_dist

    # Compute baseline and simulated risk scores
    baseline_row = {
        "wind_speed_kt": orig_wind,
        "coastal_distance_km": orig_dist,
        "district_population": orig_pop,
    }
    simulated_row = {
        "wind_speed_kt": sim_wind,
        "coastal_distance_km": sim_dist,
        "district_population": orig_pop,
    }

    baseline_risk = derive_risk_score(pd.Series(baseline_row))
    simulated_risk = derive_risk_score(pd.Series(simulated_row))

    risk_delta = simulated_risk - baseline_risk

    orig_category = derive_intensity_category(orig_wind)
    sim_category = derive_intensity_category(sim_wind)

    return {
        "base_id": base_id,
        "storm_name": event.get("matched_storm_name") or f"Cyclone #{base_id}",
        "baseline": {
            "wind_speed_kt": orig_wind,
            "coastal_distance_km": orig_dist,
            "intensity_category": orig_category,
            "risk_score": round(baseline_risk, 4),
        },
        "simulation": {
            "delta_wind_speed_kt": delta_wind_speed_kt,
            "simulated_wind_speed_kt": sim_wind,
            "simulated_coastal_distance_km": sim_dist,
            "simulated_intensity_category": sim_category,
            "simulated_risk_score": round(simulated_risk, 4),
            "risk_score_delta": round(risk_delta, 4),
        },
        "risk_trend": "Increased Risk" if risk_delta > 0.02 else ("Decreased Risk" if risk_delta < -0.02 else "Stable Risk"),
        "advisory_summary": (
            f"Scenario simulation shows a {abs(round(risk_delta * 100, 1))}% "
            f"{'increase' if risk_delta > 0 else 'decrease'} in risk. "
            f"Intensity category shifted from '{orig_category}' to '{sim_category}'."
        )
    }


import pandas as pd

if __name__ == "__main__":
    res = simulate_whatif(1, delta_wind_speed_kt=20.0, new_coastal_distance_km=50.0)
    print(res)
