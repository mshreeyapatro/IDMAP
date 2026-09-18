"""
Live Satellite Imagery Feed Engine (NASA GIBS / MOSDAC Integration).

Fetches open-access live satellite imagery metadata and tile snapshot URLs for the
Bay of Bengal / Odisha coastal domain.
"""

import sys
import io
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def get_valid_nasa_gibs_date(layer: str = "VIIRS_SNPP_CorrectedReflectance_TrueColor", tile: str = "3/2/5.jpg") -> tuple[str, str]:
    """
    NASA GIBS standard daily imagery mosaics lag real-time by ~24 hours.
    Requests for un-processed dates return a blank black tile (RGB 0,0,0).
    Finds the most recent date with valid non-black satellite imagery.
    """
    for days_back in range(0, 4):
        target_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        url = f"https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/{layer}/default/{target_date}/250m/{tile}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "IDMAP-Ingest/1.0"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = resp.read()
                img = Image.open(io.BytesIO(data))
                if img.getextrema() != ((0, 0), (0, 0), (0, 0)):
                    return url, target_date
        except Exception:
            continue

    # Fallback to yesterday if network check fails
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    fallback_url = f"https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/{layer}/default/{yesterday}/250m/{tile}"
    return fallback_url, yesterday


def get_live_satellite_feed() -> dict:
    """
    Returns NASA GIBS / MOSDAC live satellite layer URLs for Bay of Bengal.
    """
    gibs_layer = "VIIRS_SNPP_CorrectedReflectance_TrueColor"
    tile_url, valid_date = get_valid_nasa_gibs_date(gibs_layer, "3/2/5.jpg")
    today = datetime.now().strftime("%Y-%m-%d")

    # MOSDAC (ISRO) INSAT-3D sector overview link
    mosdac_info = {
        "provider": "ISRO / MOSDAC INSAT-3D",
        "sector": "Indian Ocean / Bay of Bengal Sector",
        "url": "https://www.mosdac.gov.in/gallery/images/INSAT-3D_3DR_Sector.png",
        "satellite": "INSAT-3D / INSAT-3DR",
    }

    return {
        "fetched_at": datetime.now().isoformat() + "Z",
        "nasa_gibs": {
            "provider": "NASA GIBS (Global Imagery Browse Services)",
            "layer": gibs_layer,
            "date": valid_date,
            "requested_date": today,
            "bbox_bay_of_bengal": [15.0, 80.0, 22.5, 92.0],
            "tile_snapshot_url": tile_url
        },
        "mosdac_isro": mosdac_info
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_live_satellite_feed(), indent=2))

