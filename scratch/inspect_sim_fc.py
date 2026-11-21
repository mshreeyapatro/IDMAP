import sys
sys.path.insert(0, '.')
from src.forecasting import predictive_engine

fc = predictive_engine.generate_48h_short_range_forecast(mode="simulated")
print("predicted_landfall_target_district:", fc.get("predicted_landfall_target_district"))
print("landfall_sector:", fc.get("landfall_sector"))
print("estimated_time_to_landfall_hours:", fc.get("estimated_time_to_landfall_hours"))
print("estimated_landfall_timestamp_formatted:", fc.get("estimated_landfall_timestamp_formatted"))
print("projected_peak_landfall_wind_kt:", fc.get("projected_peak_landfall_wind_kt"))
print("projected_min_landfall_pressure_hpa:", fc.get("projected_min_landfall_pressure_hpa"))

traj = fc.get("trajectory_48h_matrix", [])
print(f"Total trajectory points: {len(traj)}")
for pt in traj[::6]:
    print(f"  T+{pt.get('lead_time_hours')}h: Lat={pt.get('eye_latitude')}, Lon={pt.get('eye_longitude')}, Heading={pt.get('heading_deg')}, Wind={pt.get('max_sustained_wind_kt')}kt, CoastDist={pt.get('coastal_distance_km')}km, Closest={pt.get('closest_district')}")

if traj:
    last = traj[-1]
    print(f"  T+{last.get('lead_time_hours')}h: Lat={last.get('eye_latitude')}, Lon={last.get('eye_longitude')}, Closest={last.get('closest_district')}")

