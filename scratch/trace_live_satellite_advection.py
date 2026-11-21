import sys
sys.path.insert(0, '.')
from src.forecasting import predictive_engine

target, sector, etl = predictive_engine.calculate_dynamic_landfall_eta_and_target(
    lat0=15.0, lon0=87.0, heading_deg=315.0, trans_speed_kmh=14.8
)
print("=== DYNAMIC LANDFALL CALCULATION WITH LIVE SATELLITE INPUTS ===")
print(f"Target District: {target}")
print(f"Sector: {sector}")
print(f"ETL Hours: {etl} hours")

for h in range(0, 49, 4):
    lat_h, lon_h, head_h = predictive_engine.advect_eye_position(15.0, 87.0, 315.0, 14.8, h)
    closest = min(predictive_engine.ODISHA_BAY_OF_BENGAL_COASTLINE, key=lambda p: predictive_engine.haversine_distance(lat_h, lon_h, p[0], p[1]))
    d = predictive_engine.haversine_distance(lat_h, lon_h, closest[0], closest[1])
    print(f"T+{h:02d}h: Eye=({lat_h:.2f}, {lon_h:.2f}), Heading={head_h:.1f}°, Closest={closest[2]} ({closest[3]}), Dist={d:.1f}km")

