import sys
sys.path.insert(0, '.')
from src.forecasting import predictive_engine

fc = predictive_engine.generate_48h_short_range_forecast(mode="simulated")
print("Keys in fc:", list(fc.keys()))
for k in ["landfall_target_district", "landfall_sector", "estimated_etl_hours", "estimated_landfall_timestamp_formatted", "primary_landfall_target"]:
    print(f"  {k}: {fc.get(k)}")

if "forecast_trajectory" in fc:
    traj = fc["forecast_trajectory"]
    print("forecast_trajectory length:", len(traj))
    if traj:
        print("First point:", traj[0])
        print("Middle point:", traj[len(traj)//2])
        print("Last point:", traj[-1])

