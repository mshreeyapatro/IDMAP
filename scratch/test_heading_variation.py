import sys
sys.path.insert(0, '.')
from src.forecasting import predictive_engine
import math

print("=== TESTING TRAJECTORY ADVECTION ===")
# Let's test with initial point in Bay of Bengal
# For example, lat0 = 17.8, lon0 = 86.1, heading = 315 (NW)
# Let's test different headings: 300, 315, 330, 345, 360
for h_deg in [295, 305, 315, 325, 335, 345, 355]:
    target, sector, etl = predictive_engine.calculate_dynamic_landfall_eta_and_target(
        lat0=17.8, lon0=86.1, heading_deg=h_deg, trans_speed_kmh=15.0
    )
    print(f"Heading {h_deg}° -> Target: {target} ({sector}), ETL: {etl}h")

print("\n=== TESTING WITH NWP STEERING FLOW ===")
# Check with steering flow
from src.ingestion import live_weather
steering = live_weather.get_nwp_vertical_steering_flow(17.8, 86.1)
print("Live steering flow from Open-Meteo:", steering)
target, sector, etl = predictive_engine.calculate_dynamic_landfall_eta_and_target(
    lat0=17.8, lon0=86.1, heading_deg=315.0, trans_speed_kmh=15.0, steering_flow=steering
)
print(f"With Live Steering -> Target: {target} ({sector}), ETL: {etl}h")

