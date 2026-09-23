"""
Phase 9: Resource Planning & Evacuation Allocation Engine (SRS Section 13).

Calculates district-level evacuation capacity, shelter requirements, food/water supply
units, and medical team allocations based on Census 2011 population metadata,
district coastal proximity, literacy rates, and cyclone severity.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DISTRICT_NODES_CSV = ROOT / "data" / "processed" / "odisha_district_nodes.csv"
POPULATION_CSV = ROOT / "data" / "processed" / "odisha_district_population.csv"


def get_resource_plan(
    district_name: str | None = None,
    severity_level: str = "High",
    wind_speed_kt: float = 35.0
) -> dict:
    """
    Computes emergency resource allocation and shelter priorities for Odisha districts.
    """
    if not POPULATION_CSV.exists():
        return {"error": "Odisha district population database not found."}

    df_pop = pd.read_csv(POPULATION_CSV)
    df_nodes = pd.read_csv(DISTRICT_NODES_CSV) if DISTRICT_NODES_CSV.exists() else None

    # Merge nodes for coastal distance if available
    if df_nodes is not None and "coastal_distance_km" in df_nodes.columns:
        df = pd.merge(df_pop, df_nodes[["district", "coastal_distance_km"]], on="district", how="left")
    else:
        df = df_pop.copy()
        if "coastal_distance_km" not in df.columns:
            df["coastal_distance_km"] = 150.0

    # If wind speed is below Depression threshold (28 kt), no emergency evacuation is needed
    if wind_speed_kt < 28.0:
        mult = 0.0
    elif wind_speed_kt < 34.0:
        mult = 0.03
    elif wind_speed_kt < 48.0:
        mult = 0.10
    elif wind_speed_kt < 64.0:
        mult = 0.20
    elif wind_speed_kt < 90.0:
        mult = 0.35
    else:
        mult = 0.50

    # Calculate evacuation metrics per district
    records = []
    for _, row in df.iterrows():
        d_name = row["district"]
        pop = row.get("population", 1000000)
        raw_dist = row.get("coastal_distance_km")
        coastal_dist = float(raw_dist) if (pd.notna(raw_dist) and raw_dist is not None) else 100.0

        # Coastal risk decay factor
        if mult == 0.0:
            target_evac_pct = 0.0
            people_to_evacuate = 0
            shelters_needed = 0
            ndrf_teams_needed = 0
            medical_units_needed = 0
            food_packets_daily = 0
        else:
            coastal_factor = np.exp(-coastal_dist / 100.0)
            target_evac_pct = min(0.95, mult * coastal_factor)
            people_to_evacuate = int(pop * target_evac_pct)
            shelters_needed = int(np.ceil(people_to_evacuate / 1000)) if people_to_evacuate > 0 else 0
            ndrf_teams_needed = int(np.ceil(people_to_evacuate / 50000)) if people_to_evacuate > 0 else 0
            medical_units_needed = int(np.ceil(people_to_evacuate / 25000)) if people_to_evacuate > 0 else 0
            food_packets_daily = people_to_evacuate * 2

        records.append({
            "district": d_name,
            "total_population": pop,
            "coastal_distance_km": round(coastal_dist, 1),
            "evacuation_target_pct": round(target_evac_pct * 100, 1),
            "people_to_evacuate": people_to_evacuate,
            "multipurpose_shelters_required": shelters_needed,
            "ndrf_teams_required": ndrf_teams_needed,
            "medical_mobile_units": medical_units_needed,
            "daily_food_water_packets": food_packets_daily,
            "priority_tier": "Critical Tier-1" if coastal_dist <= 50 else ("High Tier-2" if coastal_dist <= 150 else "Standard Tier-3")
        })

    df_result = pd.DataFrame(records)
    df_result.sort_values(by=["coastal_distance_km"], inplace=True)

    if district_name:
        match = df_result[df_result["district"].str.lower() == district_name.lower()]
        if match.empty:
            return {"error": f"District {district_name!r} not found in Odisha district database."}
        return {"district_plan": match.to_dict(orient="records")[0]}

    total_evac = int(df_result["people_to_evacuate"].sum())
    total_shelters = int(df_result["multipurpose_shelters_required"].sum())
    total_ndrf = int(df_result["ndrf_teams_required"].sum())

    return {
        "severity_level": severity_level,
        "total_state_evacuation_target": total_evac,
        "total_multipurpose_shelters_required": total_shelters,
        "total_ndrf_teams_required": total_ndrf,
        "district_breakdown": df_result.to_dict(orient="records")
    }


if __name__ == "__main__":
    res = get_resource_plan(district_name="Puri", severity_level="High")
    print(res)
