import sys
sys.path.insert(0, '.')
from src.forecasting import predictive_engine

print("=== CHECKING ADVECTION TO BHADRAK ===")
# What initial positions and headings hit Bhadrak?
for lat in [14.0, 15.0, 16.0, 17.0, 18.0]:
    for lon in [85.0, 86.0, 87.0, 88.0, 89.0]:
        for heading in [320.0, 330.0, 340.0, 350.0, 5.0, 15.0]:
            target, sector, etl = predictive_engine.calculate_dynamic_landfall_eta_and_target(
                lat0=lat, lon0=lon, heading_deg=heading, trans_speed_kmh=12.0
            )
            if "Bhadrak" in target or "Kendrapara" in target or "Baleshwar" in target:
                print(f"Lat={lat}, Lon={lon}, Heading={heading} -> Target: {target} ({sector}), ETL: {etl}h")
                break

