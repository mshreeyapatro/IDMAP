"""
Live Weather Ingestion Engine (Open-Meteo Integration).

Fetches real-time and 24-hour forecast weather metrics (10m wind speed, gusts,
surface pressure, precipitation, temperature) across key Odisha coastal & inland stations.
"""

import sys
from pathlib import Path
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ODISHA_STATIONS = {
    "Puri": {"lat": 19.8136, "lon": 85.8312, "type": "Coastal"},
    "Paradip": {"lat": 20.3164, "lon": 86.6115, "type": "Coastal"},
    "Gopalpur": {"lat": 19.2568, "lon": 84.9080, "type": "Coastal"},
    "Balasore": {"lat": 21.4942, "lon": 86.9317, "type": "Coastal"},
    "Chandbali": {"lat": 20.7744, "lon": 86.7380, "type": "Coastal"},
    "Bhubaneswar": {"lat": 20.2961, "lon": 85.8245, "type": "Inland Capital"},
}


def ms_to_knots(ms: float) -> float:
    return round(ms * 1.94384, 1)


def derive_live_severity(wind_kt: float) -> str:
    if wind_kt < 28:
        return "Normal / Light Breeze"
    elif wind_kt < 34:
        return "Depression"
    elif wind_kt < 48:
        return "Deep Depression"
    elif wind_kt < 64:
        return "Cyclonic Storm"
    elif wind_kt < 90:
        return "Severe Cyclonic Storm"
    else:
        return "Super Cyclonic Storm"


def fetch_station_weather(station_name: str, coords: dict) -> dict:
    """
    Calls Open-Meteo API for a single station.
    """
    lat = coords["lat"]
    lon = coords["lon"]
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation&"
        f"hourly=temperature_2m,surface_pressure,wind_speed_10m,precipitation&wind_speed_unit=ms&forecast_days=1"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "IDMAP-Disaster-Intelligence/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    curr = data.get("current", {})
    wind_ms = curr.get("wind_speed_10m", 0.0)
    gust_ms = curr.get("wind_gusts_10m", 0.0)
    wind_kt = ms_to_knots(wind_ms)
    gust_kt = ms_to_knots(gust_ms)
    pressure = curr.get("surface_pressure", 1013.25)
    temp = curr.get("temperature_2m", 28.0)
    precip = curr.get("precipitation", 0.0)

    severity = derive_live_severity(wind_kt)

    return {
        "station": station_name,
        "type": coords["type"],
        "latitude": lat,
        "longitude": lon,
        "timestamp": curr.get("time", datetime.now(timezone.utc).isoformat()),
        "wind_speed_kt": wind_kt,
        "wind_gusts_kt": gust_kt,
        "surface_pressure_hpa": pressure,
        "temperature_c": temp,
        "precipitation_mm": precip,
        "severity_status": severity,
        "is_alert": wind_kt >= 34 or pressure < 1000.0
    }


def get_live_weather_feed() -> dict:
    """
    Fetches real-time weather feed across all 6 Odisha stations.
    """
    stations_data = []
    max_wind = 0.0
    min_pressure = 2000.0

    for name, coords in ODISHA_STATIONS.items():
        try:
            st = fetch_station_weather(name, coords)
            stations_data.append(st)
            if st["wind_speed_kt"] > max_wind:
                max_wind = st["wind_speed_kt"]
            if st["surface_pressure_hpa"] < min_pressure:
                min_pressure = st["surface_pressure_hpa"]
        except Exception as e:
            stations_data.append({
                "station": name,
                "type": coords["type"],
                "latitude": coords["lat"],
                "longitude": coords["lon"],
                "error": str(e),
                "wind_speed_kt": 15.0,
                "surface_pressure_hpa": 1008.0,
                "severity_status": "Normal / Fallback Data",
                "is_alert": False
            })

    overall_severity = derive_live_severity(max_wind)
    coastal_alert = any(s.get("is_alert", False) for s in stations_data)

    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "data_source": "Open-Meteo Live API",
        "max_coastal_wind_speed_kt": max_wind,
        "min_coastal_pressure_hpa": min_pressure,
        "overall_state_severity": overall_severity,
        "coastal_cyclone_alert": coastal_alert,
        "stations": stations_data
    }


def get_nwp_vertical_steering_flow(lat: float = 19.5, lon: float = 86.2) -> dict:
    """
    Ingests vertical pressure-level wind components (850, 700, 500, 300, 200 hPa)
    from Open-Meteo NWP Pressure Levels API and computes the deep-layer mass-weighted
    environmental steering vector V_steer = (u_steer, v_steer).

    Weights:
    - 850 hPa: 0.15 (boundary layer coupling)
    - 700 hPa: 0.25 (lower troposphere steering)
    - 500 hPa: 0.35 (mid-troposphere subtropical ridge steering - primary)
    - 300 hPa: 0.15 (upper-troposphere outflow interaction)
    - 200 hPa: 0.10 (cirrus outflow layer)
    """
    import math

    weights = {
        "850": 0.15,
        "700": 0.25,
        "500": 0.35,
        "300": 0.15,
        "200": 0.10
    }

    # Default fallback: 315° NW at 14.8 km/h (8.0 kt)
    default_heading_deg = 315.0
    default_speed_kmh = 14.8
    rad = math.radians(default_heading_deg)
    # Meteorological direction: wind moving towards heading
    u_default = (default_speed_kmh / 3.6) * math.sin(rad)
    v_default = (default_speed_kmh / 3.6) * math.cos(rad)

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"hourly=wind_speed_850hPa,wind_direction_850hPa,"
        f"wind_speed_700hPa,wind_direction_700hPa,"
        f"wind_speed_500hPa,wind_direction_500hPa,"
        f"wind_speed_300hPa,wind_direction_300hPa,"
        f"wind_speed_200hPa,wind_direction_200hPa&"
        f"wind_speed_unit=ms&forecast_days=1"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "IDMAP-Steering-Ingest/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        hourly = data.get("hourly", {})
        u_weighted = 0.0
        v_weighted = 0.0
        total_w = 0.0
        layer_breakdown = {}

        for level, w in weights.items():
            spd_arr = hourly.get(f"wind_speed_{level}hPa", [])
            dir_arr = hourly.get(f"wind_direction_{level}hPa", [])
            if spd_arr and dir_arr:
                spd_ms = float(spd_arr[0])
                dir_deg = float(dir_arr[0])
                # Meteorological wind blows from dir_deg, so cyclone is steered towards (dir_deg + 180) % 360
                # or motion vector u = -spd * sin(dir), v = -spd * cos(dir)
                rad_d = math.radians(dir_deg)
                u_level = -spd_ms * math.sin(rad_d)
                v_level = -spd_ms * math.cos(rad_d)

                u_weighted += u_level * w
                v_weighted += v_level * w
                total_w += w
                layer_breakdown[f"{level}hPa"] = {
                    "speed_ms": spd_ms,
                    "direction_deg": dir_deg,
                    "weight": w
                }

        if total_w > 0:
            u_steer_ms = u_weighted / total_w
            v_steer_ms = v_weighted / total_w
            speed_ms = math.sqrt(u_steer_ms ** 2 + v_steer_ms ** 2)
            speed_kmh = round(speed_ms * 3.6, 1)
            speed_kt = round(speed_ms * 1.94384, 1)
            # Motion heading angle
            heading_deg = round((math.degrees(math.atan2(u_steer_ms, v_steer_ms)) + 360.0) % 360.0, 1)

            return {
                "source": "Open-Meteo NWP Pressure Levels API (Deep Layer 850-200 hPa)",
                "coordinates": {"lat": lat, "lon": lon},
                "u_steering_ms": round(u_steer_ms, 2),
                "v_steering_ms": round(v_steer_ms, 2),
                "steering_speed_kmh": max(6.0, speed_kmh),
                "steering_speed_kt": max(3.5, speed_kt),
                "steering_heading_deg": heading_deg,
                "pressure_levels": layer_breakdown,
                "is_fallback": False
            }

    except Exception as e:
        pass

    # Clean Fallback
    return {
        "source": "Climatological Deep-Layer Steering (Fallback)",
        "coordinates": {"lat": lat, "lon": lon},
        "u_steering_ms": round(u_default, 2),
        "v_steering_ms": round(v_default, 2),
        "steering_speed_kmh": default_speed_kmh,
        "steering_speed_kt": round(default_speed_kmh / 1.852, 1),
        "steering_heading_deg": default_heading_deg,
        "pressure_levels": {},
        "is_fallback": True
    }


if __name__ == "__main__":
    feed = get_live_weather_feed()
    print(json.dumps(feed, indent=2))
    print("\n--- Deep Layer Steering ---")
    print(json.dumps(get_nwp_vertical_steering_flow(), indent=2))

