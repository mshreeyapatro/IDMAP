"""
Resolves the dataset audit's blocking gap: insat3d's numeric base_id has no
confirmed link to a real storm identity, date, or location. It turns out the
`reference/` images (data/raw/insat3d/reference/) are meteorological products
with the real capture date/time and TC-center lat/lon burned into the image as
red text (and sometimes the storm name itself, e.g. "TC LUBAN"). This script
OCRs every reference image, parses out (date, lat, lon, name) fields, and
matches each against the IMD RSMC New Delhi best-track record (fetched via
`imdtrack` -- see fetch_imd_besttrack.py) to assign every base_id a real storm
identity wherever the image carries a legible fix.

Two known burned-in text layouts (see any file in reference/ to compare):
  A) "YYYY-MM-DD-HHMM : TC Center: LAT: XX.XX N LON: XX.XX E"   (e.g. 101.jpeg)
  B) "LAT: XX.XX N  LON: XX.XX E"  +  "DDMMMYYYYHHMM"           (e.g. 25.jpeg)
Some images show two storms side by side (e.g. 59_LUBAN.png: LUBAN + TITLI),
in which case multiple (date, lat, lon) fixes are extracted from one image.
Some large multi-panel products (e.g. the 6400x4800 cluster) repeat only the
date stamp with no single-point fix -- those still give a date-only match.

This is inherently approximate (OCR + nearest-neighbor matching against best
track), so every match is reported with its time/distance error -- always
check match_time_diff_hours and match_dist_km before trusting a row, and treat
this as a strong candidate labeling, not ground truth requiring no review.

Outputs:
  - data/interim/insat3d_reference_ocr.csv     (raw OCR text per reference file, for auditing)
  - data/processed/insat3d_event_identity.csv  (one row per base_id, best storm match)

Usage: python src/data_prep/extract_reference_metadata.py
"""

import re
from datetime import datetime
from pathlib import Path

import easyocr
import imdtrack as imd
import numpy as np
import pandas as pd
from PIL import Image
from shapely.geometry import Point
from shapely.ops import unary_union

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_odisha_district_graph import load_odisha_districts  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = ROOT / "data" / "raw" / "insat3d" / "reference"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"

OCR_CSV_OUT = DATA_INTERIM / "insat3d_reference_ocr.csv"
IDENTITY_CSV_OUT = DATA_PROCESSED / "insat3d_event_identity.csv"

# Downscale very large plot images before OCR -- burned-in text is rendered at
# a fixed font size regardless of overall plot resolution, so this is purely a
# speed optimization and doesn't lose legibility.
MAX_DIM_FOR_OCR = 2000

BASE_ID_RE = re.compile(r"^(\d+)")
DATE_STYLE_A_RE = re.compile(r"(\d{4}-\d{2}-\d{2}-\d{4})")
DATE_STYLE_B_RE = re.compile(r"(\d{2}[A-Z]{3}\d{4}\d{4})")
LAT_RE = re.compile(r"(\d{1,2}\.\d{1,2})\s*[*'\"]?\s*N\b")
LON_RE = re.compile(r"(\d{1,3}\.\d{1,2})\s*[*'\"]?\s*E\b")
NAME_RE = re.compile(r"\bTC\s+([A-Z]{3,})\b")

# Matches worse than this are dropped as unreliable rather than reported.
MAX_MATCH_TIME_DIFF_HOURS = 12
MAX_MATCH_DIST_KM = 300

# A storm counts as "Odisha-relevant" if its full track (not just the single
# snapshot this image happens to show) ever came within this distance of the
# state -- images are pre-landfall, so an approaching storm can be a couple
# hundred km offshore in any one frame even when it later made direct landfall.
ODISHA_RELEVANCE_THRESHOLD_KM = 150


def extract_base_id(filename: str):
    m = BASE_ID_RE.match(filename)
    return int(m.group(1)) if m else None


def parse_style_a_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d-%H%M")


def parse_style_b_date(s: str):
    return datetime.strptime(s, "%d%b%Y%H%M")


def ocr_all_reference_images(reader) -> pd.DataFrame:
    rows = []
    files = sorted(REFERENCE_DIR.iterdir())
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] OCR {f.name}")
        img = Image.open(f).convert("RGB")
        if max(img.size) > MAX_DIM_FOR_OCR:
            scale = MAX_DIM_FOR_OCR / max(img.size)
            img = img.resize((int(img.width * scale), int(img.height * scale)))
        results = reader.readtext(path_or_array_from_pil(img))
        joined = " ".join(text for _, text, _ in results)
        rows.append({
            "filename": f.name,
            "base_id": extract_base_id(f.name),
            "ocr_text": joined,
        })
    return pd.DataFrame(rows)


def path_or_array_from_pil(img: Image.Image):
    return np.array(img)


def parse_fixes(ocr_text: str) -> list[dict]:
    """Extract every (date, lat, lon) fix this image's OCR text yields, paired
    positionally when multiple appear (e.g. a two-storm comparison panel)."""
    dates = []
    for s in DATE_STYLE_A_RE.findall(ocr_text):
        try:
            dates.append(parse_style_a_date(s))
        except ValueError:
            pass
    for s in DATE_STYLE_B_RE.findall(ocr_text):
        try:
            dates.append(parse_style_b_date(s))
        except ValueError:
            pass
    # de-dupe while preserving order (a date stamp often repeats many times
    # across a multi-panel image)
    seen = set()
    dates = [d for d in dates if not (d in seen or seen.add(d))]

    lats = [float(x) for x in LAT_RE.findall(ocr_text)]
    lons = [float(x) for x in LON_RE.findall(ocr_text)]
    names = [n for n in NAME_RE.findall(ocr_text) if n != "CENTER"]

    n_fixes = max(len(lats), len(lons), 1)
    fixes = []
    for i in range(n_fixes):
        fixes.append({
            "date": dates[i] if i < len(dates) else (dates[0] if dates else None),
            "lat": lats[i] if i < len(lats) else None,
            "lon": lons[i] if i < len(lons) else None,
            "name": names[i] if i < len(names) else None,
        })
    return [f for f in fixes if f["date"] or (f["lat"] is not None and f["lon"] is not None)]


def match_against_besttrack(fix: dict, observations: pd.DataFrame):
    """Nearest-neighbor match: smallest combined time+space distance among all
    IMD best-track observations (all basins/years -- some reference images
    turned out to show Arabian Sea storms, not just Bay of Bengal)."""
    candidates = observations.dropna(subset=["lat", "lon", "time"]).copy()
    if fix["date"] is not None:
        candidates = candidates[
            (candidates["time"] - fix["date"]).abs() <= pd.Timedelta(hours=MAX_MATCH_TIME_DIFF_HOURS)
        ]
    if candidates.empty:
        return None

    if fix["lat"] is not None and fix["lon"] is not None:
        # Regional flat-km approximation, consistent with build_odisha_district_graph.py
        dlat = (candidates["lat"] - fix["lat"]) * 111.0
        dlon = (candidates["lon"] - fix["lon"]) * 111.32
        dist_km = (dlat ** 2 + dlon ** 2) ** 0.5
        candidates = candidates.assign(_dist_km=dist_km)
        candidates = candidates[candidates["_dist_km"] <= MAX_MATCH_DIST_KM]
        if candidates.empty:
            return None
        best = candidates.loc[candidates["_dist_km"].idxmin()]
        dist_km = best["_dist_km"]
    else:
        best = candidates.iloc[(candidates["time"] - fix["date"]).abs().argmin()]
        dist_km = None

    time_diff_hours = abs((best["time"] - fix["date"]).total_seconds()) / 3600 if fix["date"] else None
    return {
        "storm_id": best["storm_id"],
        "name": best["name"],
        "basin": best["basin"],
        "matched_time": best["time"],
        "matched_lat": best["lat"],
        "matched_lon": best["lon"],
        "wind_speed_kt": best["wind"],
        "pressure_hpa": best["pressure"],
        "match_time_diff_hours": round(time_diff_hours, 2) if time_diff_hours is not None else None,
        "match_dist_km": round(dist_km, 1) if dist_km is not None else None,
    }


def find_containing_district(lat, lon, districts):
    p = Point(lon, lat)
    for d in districts:
        if d["geometry"].contains(p):
            return d["district"]
    return None


def enrich_with_odisha_context(df: pd.DataFrame, observations: pd.DataFrame) -> pd.DataFrame:
    """Adds columns answering: how relevant is this storm to Odisha at all
    (judged by its FULL track, not just this one snapshot -- a storm captured
    pre-landfall can be a couple hundred km offshore in a single frame even
    when it later made direct Odisha landfall), and where exactly is this
    specific fix relative to Odisha (coastal distance, containing district)."""
    districts = load_odisha_districts()
    odisha = unary_union([d["geometry"] for d in districts])

    obs = observations.dropna(subset=["lat", "lon"])
    track_min_dist_km = {}
    closest_approach_time = {}
    for storm_id, sobs in obs.groupby("storm_id"):
        dists = [(odisha.distance(Point(r.lon, r.lat)) * 111.0, r.time) for r in sobs.itertuples()]
        min_dist, min_time = min(dists, key=lambda t: t[0])
        track_min_dist_km[storm_id] = min_dist
        closest_approach_time[storm_id] = min_time

    df = df.copy()
    df["storm_min_dist_to_odisha_km"] = df["storm_id"].map(track_min_dist_km).round(1)
    df["is_odisha_relevant"] = df["storm_min_dist_to_odisha_km"] <= ODISHA_RELEVANCE_THRESHOLD_KM
    df["odisha_closest_approach_time"] = df["storm_id"].map(closest_approach_time)
    df.loc[~df["is_odisha_relevant"], "odisha_closest_approach_time"] = pd.NaT

    df["coastal_distance_km"] = df.apply(
        lambda r: round(odisha.distance(Point(r["ocr_lon"], r["ocr_lat"])) * 111.0, 1)
        if pd.notna(r["ocr_lat"]) and pd.notna(r["ocr_lon"]) else None,
        axis=1,
    )
    df["district"] = df.apply(
        lambda r: find_containing_district(r["ocr_lat"], r["ocr_lon"], districts)
        if pd.notna(r["ocr_lat"]) and pd.notna(r["ocr_lon"]) else None,
        axis=1,
    )
    return df


def main():
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    print("Loading IMD best-track record...")
    bt = imd.load()
    observations = bt.observations

    print("Loading OCR reader (first run downloads model weights)...")
    reader = easyocr.Reader(["en"], gpu=False)

    ocr_df = ocr_all_reference_images(reader)
    ocr_df.to_csv(OCR_CSV_OUT, index=False)
    print(f"Wrote {OCR_CSV_OUT.relative_to(ROOT)}")

    match_rows = []
    for row in ocr_df.itertuples():
        fixes = parse_fixes(row.ocr_text)
        for fix in fixes:
            m = match_against_besttrack(fix, observations)
            if m is None:
                continue
            match_rows.append({
                "filename": row.filename,
                "base_id": row.base_id,
                "ocr_name": fix["name"],
                "ocr_date": fix["date"],
                "ocr_lat": fix["lat"],
                "ocr_lon": fix["lon"],
                **m,
            })
    matches_df = pd.DataFrame(match_rows)

    if matches_df.empty:
        print("No matches found -- nothing to write for insat3d_event_identity.csv")
        return

    # Best match per base_id: prefer the fix with the smallest time+distance error.
    # NOTE: groupby(...).first() would pick the first *non-null value per column*
    # independently, not the first whole row -- that silently mixes fields from
    # different candidate rows (e.g. taking `name` from a worse-scoring row just
    # because the best-scoring row's name happened to be null). Sort + drop_duplicates
    # keeps each kept row intact.
    matches_df["_score"] = matches_df["match_time_diff_hours"].fillna(999) + \
        matches_df["match_dist_km"].fillna(999) / 10
    best_per_base = (
        matches_df.sort_values("_score")
        .drop_duplicates(subset="base_id", keep="first")
        .drop(columns="_score")
    )
    n_files_per_base = matches_df.groupby("base_id")["filename"].nunique().rename("n_reference_files_matched")
    best_per_base = best_per_base.merge(n_files_per_base, on="base_id")

    print("Computing Odisha relevance/coastal-distance/district context...")
    best_per_base = enrich_with_odisha_context(best_per_base, observations)
    best_per_base = best_per_base.sort_values(
        ["is_odisha_relevant", "storm_min_dist_to_odisha_km"], ascending=[False, True]
    )
    best_per_base.to_csv(IDENTITY_CSV_OUT, index=False)

    n_ids_total = ocr_df["base_id"].nunique()
    n_ids_matched = best_per_base["base_id"].nunique()
    n_named = best_per_base["name"].notna().sum()
    n_odisha = best_per_base["is_odisha_relevant"].sum()
    print(f"Matched {n_ids_matched}/{n_ids_total} unique base_ids to a best-track observation "
          f"({n_named} to a named storm, {n_odisha} Odisha-relevant)")
    print(f"Wrote {IDENTITY_CSV_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
