"""
Test/demo Fetcher -- NOT a live data source.

Replays events from data/processed/insat3d_event_identity.csv (the real
storm identity/date/lat-lon that src/data_prep/extract_reference_metadata.py
recovered via OCR + IMD best-track matching) as if they were arriving live,
one per storm event, each carrying its own real metadata.

This exists to let pipeline.py be built and exercised end-to-end against
real, already-verified data -- not fabricated images -- while there's no
actual live source connected. It is explicitly NOT what a production Fetcher
should look like: a real one talks to an actual satellite data API/feed and
gets its metadata from that source at request time, not from a CSV this
project already produced by reverse-engineering an archival dataset.
"""

import re
from pathlib import Path

import pandas as pd

from pipeline import Fetcher, FetchedImage

ROOT = Path(__file__).resolve().parents[2]
IDENTITY_CSV = ROOT / "data" / "processed" / "insat3d_event_identity.csv"
RAW_IMAGE_DIR = ROOT / "data" / "raw" / "insat3d" / "raw"

BASE_ID_RE = re.compile(r"^(\d+)")


def _find_raw_image(base_id: int) -> Path | None:
    """The insat3d raw/ folder names files like '101.jpg' or '33(1).jpg' --
    match on the leading integer, same convention as dataset_audit.py."""
    if not RAW_IMAGE_DIR.exists():
        return None
    for f in sorted(RAW_IMAGE_DIR.iterdir()):
        m = BASE_ID_RE.match(f.name)
        if m and int(m.group(1)) == base_id:
            return f
    return None


class ReplayFetcher(Fetcher):
    def __init__(self, identity_csv: Path = IDENTITY_CSV, only_odisha_relevant: bool = False):
        self.identity_csv = identity_csv
        self.only_odisha_relevant = only_odisha_relevant

    def fetch_new(self) -> list[FetchedImage]:
        if not self.identity_csv.exists():
            print(f"No {self.identity_csv.name} found -- run "
                  f"src/data_prep/extract_reference_metadata.py first.")
            return []

        df = pd.read_csv(self.identity_csv, parse_dates=["ocr_date", "matched_time"])
        if self.only_odisha_relevant:
            df = df[df["is_odisha_relevant"]]

        results = []
        for row in df.itertuples():
            img_path = _find_raw_image(int(row.base_id))
            if img_path is None:
                continue
            capture_time = row.ocr_date if pd.notna(row.ocr_date) else row.matched_time
            results.append(FetchedImage(
                image_bytes=img_path.read_bytes(),
                source="replay",
                source_id=str(int(row.base_id)),
                capture_time=capture_time.to_pydatetime() if pd.notna(capture_time) else None,
                lat=float(row.ocr_lat) if pd.notna(row.ocr_lat) else None,
                lon=float(row.ocr_lon) if pd.notna(row.ocr_lon) else None,
                storm_id=str(row.storm_id) if pd.notna(row.storm_id) else None,
                storm_name=str(row.name) if pd.notna(row.name) else None,
            ))
        return results
