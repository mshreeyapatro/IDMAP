import sys
sys.path.insert(0, '.')
import json
from src.forecasting import predictive_engine

print("=== RUNNING SIMULATED FORECAST ===")
fc = predictive_engine.generate_48h_short_range_forecast(mode="simulated")
print("Target District:", fc.get("landfall_target_district"))
print("Landfall Sector:", fc.get("landfall_sector"))
print("Estimated ETL Hours:", fc.get("estimated_etl_hours"))
print("Landfall Timestamp IST:", fc.get("estimated_landfall_timestamp_formatted"))
print("Initial Lat0, Lon0:", fc.get("initial_state", {}))
print("Steering / Heading:", fc.get("effective_heading"), "Speed:", fc.get("effective_speed"))

trajectory = fc.get("trajectory", [])
print(f"Total trajectory points: {len(trajectory)}")
for pt in trajectory[::6]:
    print(f"  T+{pt.get('lead_time_hours')}h: Lat={pt.get('lat')}, Lon={pt.get('lon')}, Heading={pt.get('heading')}, Wind={pt.get('vmax_kt')}kt, CoastDist={pt.get('min_dist_to_coast_km')}km, Closest={pt.get('closest_district')}")

print("\n=== RUNNING LIVE FORECAST ===")
fc_live = predictive_engine.generate_48h_short_range_forecast(mode="live")
print("Live Target District:", fc_live.get("landfall_target_district"))
print("Live Landfall Sector:", fc_live.get("landfall_sector"))
print("Live Estimated ETL Hours:", fc_live.get("estimated_etl_hours"))
print("Live Landfall Timestamp IST:", fc_live.get("estimated_landfall_timestamp_formatted"))
