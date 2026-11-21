import sys
sys.path.insert(0, '.')
from src.ingestion import live_satellite, live_weather

sat = live_satellite.get_live_satellite_feed()
print("Live Satellite Vision Telemetry:")
for k, v in sat.get("vision_ai_telemetry", {}).items():
    print(f"  {k}: {v}")

print("\nLive Weather Stations:")
weather = live_weather.get_live_weather_feed()
for st in weather.get("stations", []):
    print(f"  {st.get('station')}: wind={st.get('wind_speed_kt')}kt, press={st.get('pressure_hpa')}hpa")

