"""Real-time weather from Open-Meteo (free, no API key) - the same source your IDMAP dashboard uses."""
import csv
import json
import re
import urllib.parse
import urllib.request
from . import config

STATIONS = {  # the six IDMAP stations + two big cities
    "puri": (19.8135, 85.8312), "paradip": (20.3166, 86.6085), "gopalpur": (19.2667, 84.9000),
    "balasore": (21.4934, 86.9135), "chandbali": (20.7833, 86.7333), "bhubaneswar": (20.2961, 85.8245),
    "berhampur": (19.3150, 84.7941), "cuttack": (20.4625, 85.8828),
}
OVERVIEW = ["puri", "paradip", "gopalpur", "balasore", "chandbali", "bhubaneswar"]

WEATHER_RE = re.compile(r"\b(weather|rain|raining|rainfall|temperature|temp|wind|winds|forecast|humidity|humid|"
                        r"pressure|gust|gusts|sunny|cloudy|hot|cold|thunderstorm|storm today)\b", re.I)
TIME_RE = re.compile(r"\b(today|now|current|currently|right now|tonight|tomorrow|this (morning|evening|week)|live|latest)\b", re.I)

CODES = {0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "fog",
         51: "light drizzle", 53: "drizzle", 55: "heavy drizzle", 61: "light rain", 63: "moderate rain",
         65: "heavy rain", 80: "light showers", 81: "showers", 82: "violent showers", 95: "thunderstorm",
         96: "thunderstorm with hail", 99: "thunderstorm with heavy hail"}

_centroids = None


def _load_centroids() -> dict:
    global _centroids
    if _centroids is None:
        _centroids = {}
        path = config.DATA_DIR / "processed" / "odisha_district_nodes.csv"
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    _centroids[row["district"].strip().lower()] = (float(row["centroid_lat"]), float(row["centroid_lon"]))
        except Exception:
            pass
    return _centroids


def find_places(question: str) -> list[tuple[str, float, float]]:
    q, out, seen = question.lower(), [], set()
    for name, (lat, lon) in STATIONS.items():
        if re.search(rf"\b{name}\b", q):
            out.append((name.title(), lat, lon)); seen.add(name)
    for d in config.find_districts(question):
        c = _load_centroids().get(d.lower())
        if c and d.lower() not in seen:
            out.append((d, c[0], c[1])); seen.add(d.lower())
    return out[:3]


def wants_weather(question: str) -> bool:
    if not WEATHER_RE.search(question):
        return False
    return bool(find_places(question) or TIME_RE.search(question) or re.search(r"\bweather\b", question, re.I))


def _fmt(name: str, d: dict) -> str:
    c, dl = d.get("current") or {}, d.get("daily") or {}
    wind, gust = c.get("wind_speed_10m"), c.get("wind_gusts_10m")
    kt = lambda v: f"{v / 1.852:.0f} kt" if isinstance(v, (int, float)) else "n/a"
    lines = [f"{name} ({d.get('latitude', 0):.2f}N, {d.get('longitude', 0):.2f}E) - observed {c.get('time', '?')} IST:",
             f"  Now: {c.get('temperature_2m', 'n/a')}°C (feels {c.get('apparent_temperature', 'n/a')}°C), "
             f"humidity {c.get('relative_humidity_2m', 'n/a')}%, wind {wind} km/h ({kt(wind)}), gusts {gust} km/h ({kt(gust)}), "
             f"pressure {c.get('pressure_msl', 'n/a')} hPa, rain {c.get('precipitation', 0)} mm, "
             f"{CODES.get(c.get('weather_code'), 'conditions n/a')}"]
    for i, day in enumerate((dl.get("time") or [])[:3]):
        g = lambda k: (dl.get(k) or [None] * 3)[i]
        lines.append(f"  {day}: {g('temperature_2m_min')}-{g('temperature_2m_max')}°C, rain {g('precipitation_sum')} mm, "
                     f"max wind {g('wind_speed_10m_max')} km/h, max gust {g('wind_gusts_10m_max')} km/h, "
                     f"{CODES.get(g('weather_code'), 'n/a')}")
    return "\n".join(lines)


def weather_for_question(question: str) -> tuple[str, bool]:
    """Returns (text for the prompt, success). Empty text if the question is not about weather."""
    if not wants_weather(question):
        return "", False
    places = find_places(question) or [(n.title(), *STATIONS[n]) for n in OVERVIEW]
    params = {
        "latitude": ",".join(str(p[1]) for p in places), "longitude": ",".join(str(p[2]) for p in places),
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,"
                   "wind_speed_10m,wind_gusts_10m,pressure_msl",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max",
        "forecast_days": 3, "timezone": "Asia/Kolkata",
    }
    try:
        url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.load(r)
        data = data if isinstance(data, list) else [data]
        body = "\n".join(_fmt(p[0], d) for p, d in zip(places, data))
        return ("LIVE WEATHER from Open-Meteo (model/observation blend, NOT an official IMD bulletin):\n" + body), True
    except Exception as e:
        return f"LIVE WEATHER service could not be reached right now ({str(e)[:80]}). Do not guess weather values.", False
