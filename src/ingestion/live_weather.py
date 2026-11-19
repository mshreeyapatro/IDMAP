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
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# In-Memory Fast TTL Cache for high-performance sub-second recalculation
_WEATHER_CACHE = {
    "data": None,
    "timestamp": 0.0,
    "ttl": 300.0  # 5 minutes in-memory TTL
}

_STEERING_CACHE = {}  # key: (lat_round, lon_round) -> {"data": ..., "timestamp": ...}

ODISHA_STATIONS = {
    # Coastal Odisha Reference Observation Network
    "Puri": {"lat": 19.8136, "lon": 85.8312, "type": "Coastal"},
    "Paradip": {"lat": 20.3164, "lon": 86.6115, "type": "Coastal"},
    "Gopalpur": {"lat": 19.2568, "lon": 84.9080, "type": "Coastal"},
    "Balasore": {"lat": 21.4942, "lon": 86.9317, "type": "Coastal"},
    "Chandbali": {"lat": 20.7744, "lon": 86.7380, "type": "Coastal"},
    "Bhubaneswar": {"lat": 20.2961, "lon": 85.8245, "type": "Inland Capital"},
    # Bay of Bengal Maritime & Cyclonogenesis Observation Grid
    "Central Bay (Marine)": {"lat": 15.0, "lon": 87.0, "type": "Offshore Marine"},
    "North-Central Bay (Marine)": {"lat": 18.0, "lon": 86.5, "type": "Offshore Marine"},
    "East-Central Bay (Marine)": {"lat": 16.5, "lon": 89.0, "type": "Offshore Marine"},
    "Andhra-Odisha Deep Sea": {"lat": 17.5, "lon": 84.5, "type": "Offshore Marine"},
}


def ms_to_knots(ms: float) -> float:
    return round(ms * 1.94384, 1)


def derive_live_severity(wind_kt: float, pressure_hpa: float = 1013.25) -> str:
    """
    IMD Official Cyclone & Low-Pressure Intensity Classification Scale.
    """
    if wind_kt >= 120 or pressure_hpa <= 940.0:
        return "Super Cyclonic Storm (SuCS)"
    elif wind_kt >= 90 or pressure_hpa <= 965.0:
        return "Very Severe Cyclonic Storm (VSCS)"
    elif wind_kt >= 64 or pressure_hpa <= 980.0:
        return "Severe Cyclonic Storm (SCS)"
    elif wind_kt >= 48 or pressure_hpa <= 992.0:
        return "Cyclonic Storm (CS)"
    elif wind_kt >= 34 or pressure_hpa <= 998.0:
        return "Deep Depression (DD)"
    elif wind_kt >= 28 or pressure_hpa <= 1004.0:
        return "Depression (D)"
    elif wind_kt >= 17 or pressure_hpa <= 1008.0:
        return "Well-Marked Low Pressure Area (WML)"
    elif wind_kt >= 14 or pressure_hpa <= 1009.5:
        return "Low Pressure Area (LPA)"
    else:
        return "Normal / Light Breeze"


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
    with urllib.request.urlopen(req, timeout=2.5) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    curr = data.get("current", {})
    wind_ms = curr.get("wind_speed_10m", 0.0)
    gust_ms = curr.get("wind_gusts_10m", 0.0)
    wind_kt = ms_to_knots(wind_ms)
    gust_kt = ms_to_knots(gust_ms)
    pressure = curr.get("surface_pressure", 1013.25)
    temp = curr.get("temperature_2m", 28.0)
    precip = curr.get("precipitation", 0.0)

    severity = derive_live_severity(wind_kt, pressure)

    return {
        "station": station_name,
        "type": coords["type"],
        "latitude": lat,
        "longitude": lon,
        "timestamp": curr.get("time", datetime.now(timezone.utc).isoformat()),
        "wind_speed_kt": wind_kt,
        "wind_gusts_kt": gust_kt,
        "surface_pressure_hpa": pressure,
        "pressure_hpa": pressure,
        "temperature_c": temp,
        "precipitation_mm": precip,
        "severity_status": severity,
        "is_alert": wind_kt >= 28 or pressure <= 1004.0
    }


def get_live_weather_feed(force_refresh: bool = False) -> dict:
    """
    Fetches real-time weather feed across coastal Odisha and Bay of Bengal maritime stations.
    Implements 5-minute in-memory TTL caching for instant sub-second recalculation.
    """
    global _WEATHER_CACHE
    now_ts = time.time()
    if not force_refresh and _WEATHER_CACHE["data"] is not None:
        if (now_ts - _WEATHER_CACHE["timestamp"]) < _WEATHER_CACHE["ttl"]:
            return _WEATHER_CACHE["data"]

    stations_data = []
    max_wind = 0.0
    min_pressure = 2000.0
    deepest_station = None

    for name, coords in ODISHA_STATIONS.items():
        try:
            st = fetch_station_weather(name, coords)
            stations_data.append(st)
            if st["wind_speed_kt"] > max_wind:
                max_wind = st["wind_speed_kt"]
            if st["surface_pressure_hpa"] < min_pressure:
                min_pressure = st["surface_pressure_hpa"]
                deepest_station = st
        except Exception as e:
            fallback_pressure = 1008.0
            stations_data.append({
                "station": name,
                "type": coords["type"],
                "latitude": coords["lat"],
                "longitude": coords["lon"],
                "error": str(e),
                "wind_speed_kt": 15.0,
                "surface_pressure_hpa": fallback_pressure,
                "pressure_hpa": fallback_pressure,
                "severity_status": "Normal / Fallback Data",
                "is_alert": False
            })

    onshore_stations = [s for s in stations_data if s.get("type") != "Offshore Marine"]
    max_onshore_wind = max((s["wind_speed_kt"] for s in onshore_stations), default=max_wind)
    min_onshore_pressure = min((s["surface_pressure_hpa"] for s in onshore_stations), default=min_pressure)

    overall_severity = derive_live_severity(max_wind, min_pressure)
    coastal_alert = any(s.get("is_alert", False) for s in stations_data)

    detected_lat = deepest_station["latitude"] if deepest_station else 15.0
    detected_lon = deepest_station["longitude"] if deepest_station else 87.0

    weather_result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "data_source": "Open-Meteo Live API",
        "max_coastal_wind_speed_kt": max_wind,
        "max_onshore_wind_speed_kt": max_onshore_wind,
        "min_coastal_pressure_hpa": min_pressure,
        "min_onshore_pressure_hpa": min_onshore_pressure,
        "overall_state_severity": overall_severity,
        "coastal_cyclone_alert": coastal_alert or max_wind >= 28.0 or min_pressure <= 1004.0,
        "detected_vortex_center": {"lat": detected_lat, "lon": detected_lon},
        "stations": stations_data
    }

    _WEATHER_CACHE["data"] = weather_result
    _WEATHER_CACHE["timestamp"] = now_ts
    return weather_result


def get_nwp_vertical_steering_flow(lat: float = 19.5, lon: float = 86.2, force_refresh: bool = False) -> dict:
    """
    Ingests vertical pressure-level wind components (850, 700, 500, 300, 200 hPa)
    from Open-Meteo NWP Pressure Levels API and computes the deep-layer mass-weighted
    environmental steering vector V_steer = (u_steer, v_steer).
    Implements 5-minute in-memory caching for instant recalculation.

    Weights:
    - 850 hPa: 0.15 (boundary layer coupling)
    - 700 hPa: 0.25 (lower troposphere steering)
    - 500 hPa: 0.35 (mid-troposphere subtropical ridge steering - primary)
    - 300 hPa: 0.15 (upper-troposphere outflow interaction)
    - 200 hPa: 0.10 (cirrus outflow layer)
    """
    global _STEERING_CACHE
    cache_key = (round(lat, 1), round(lon, 1))
    now_ts = time.time()
    if not force_refresh and cache_key in _STEERING_CACHE:
        entry = _STEERING_CACHE[cache_key]
        if (now_ts - entry["timestamp"]) < 300.0:
            return entry["data"]

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

            # Calculate Deep-Layer Vertical Wind Shear (200 hPa minus 850 hPa)
            if "200hPa" in layer_breakdown and "850hPa" in layer_breakdown:
                rad_200 = math.radians(layer_breakdown["200hPa"]["direction_deg"])
                u_200 = -layer_breakdown["200hPa"]["speed_ms"] * math.sin(rad_200)
                v_200 = -layer_breakdown["200hPa"]["speed_ms"] * math.cos(rad_200)

                rad_850 = math.radians(layer_breakdown["850hPa"]["direction_deg"])
                u_850 = -layer_breakdown["850hPa"]["speed_ms"] * math.sin(rad_850)
                v_850 = -layer_breakdown["850hPa"]["speed_ms"] * math.cos(rad_850)

                vws_ms = math.sqrt((u_200 - u_850) ** 2 + (v_200 - v_850) ** 2)
                vws_kt = round(vws_ms * 1.94384, 1)
            else:
                vws_kt = 9.5

            res = {
                "source": "Open-Meteo NWP Pressure Levels API (Deep Layer 850-200 hPa)",
                "coordinates": {"lat": lat, "lon": lon},
                "u_steering_ms": round(u_steer_ms, 2),
                "v_steering_ms": round(v_steer_ms, 2),
                "steering_speed_kmh": max(6.0, speed_kmh),
                "steering_speed_kt": max(3.5, speed_kt),
                "steering_heading_deg": heading_deg,
                "vertical_wind_shear_kt": vws_kt,
                "pressure_levels": layer_breakdown,
                "is_fallback": False
            }
            _STEERING_CACHE[cache_key] = {"data": res, "timestamp": now_ts}
            return res

    except Exception as e:
        pass

    # Clean Fallback
    fallback_res = {
        "source": "Climatological Deep-Layer Steering (Fallback)",
        "coordinates": {"lat": lat, "lon": lon},
        "u_steering_ms": round(u_default, 2),
        "v_steering_ms": round(v_default, 2),
        "steering_speed_kmh": default_speed_kmh,
        "steering_speed_kt": round(default_speed_kmh / 1.852, 1),
        "steering_heading_deg": default_heading_deg,
        "vertical_wind_shear_kt": 9.5,
        "pressure_levels": {},
        "is_fallback": True
    }
    _STEERING_CACHE[cache_key] = {"data": fallback_res, "timestamp": now_ts}
    return fallback_res


def fetch_bay_of_bengal_sst() -> dict:
    """
    Fetches real-time Sea Surface Temperature (SST) and wave telemetry across
    the central Bay of Bengal marine domain (17.5°N, 87.5°E) from Open-Meteo Marine API,
    comparing against the 30-year IMD/NOAA climatological baseline.
    """
    lat, lon = 17.5, 87.5
    now_dt = datetime.now(timezone.utc)
    # 30-year Climatological Baseline SST for Central Bay of Bengal (°C) by month
    climatological_baselines = {
        1: 26.2, 2: 26.8, 3: 27.8, 4: 29.2, 5: 29.8, 6: 29.2,
        7: 28.8, 8: 28.6, 9: 28.8, 10: 28.8, 11: 28.2, 12: 27.0
    }
    base_m = climatological_baselines.get(now_dt.month, 28.5)

    try:
        url = (
            f"https://marine-api.open-meteo.com/v1/marine?"
            f"latitude={lat}&longitude={lon}&"
            f"current=sea_surface_temperature,wave_height&"
            f"timezone=UTC"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "IDMAP-Disaster-Intelligence/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        curr = data.get("current", {})
        live_sst = float(curr.get("sea_surface_temperature") or base_m)
        wave_h = float(curr.get("wave_height") or 1.0)
        anomaly_c = round(live_sst - base_m, 2)

        return {
            "source": "Open-Meteo Live Marine API (Central Bay of Bengal)",
            "latitude": lat,
            "longitude": lon,
            "timestamp": curr.get("time", now_dt.isoformat()),
            "sea_surface_temp_c": round(live_sst, 1),
            "climatological_baseline_c": round(base_m, 1),
            "sst_anomaly_c": anomaly_c,
            "wave_height_m": round(wave_h, 2),
            "is_thermal_favorable_for_ri": live_sst >= 28.5,
            "is_fallback": False
        }
    except Exception:
        # Fallback to climatological baseline
        return {
            "source": "IMD 30-Year Climatological Baseline (Fallback)",
            "latitude": lat,
            "longitude": lon,
            "timestamp": now_dt.isoformat(),
            "sea_surface_temp_c": round(base_m, 1),
            "climatological_baseline_c": round(base_m, 1),
            "sst_anomaly_c": 0.0,
            "wave_height_m": 1.2,
            "is_thermal_favorable_for_ri": base_m >= 28.5,
            "is_fallback": True
        }


if __name__ == "__main__":
    feed = get_live_weather_feed()
    print(json.dumps(feed, indent=2))
    print("\n--- Deep Layer Steering ---")
    print(json.dumps(get_nwp_vertical_steering_flow(), indent=2))
    print("\n--- Live Marine SST ---")
    print(json.dumps(fetch_bay_of_bengal_sst(), indent=2))

