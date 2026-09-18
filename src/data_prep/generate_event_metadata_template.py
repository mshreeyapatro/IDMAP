"""
Fill-in template for the single biggest data gap: real storm identity + dates
per insat3d event (see docs/dataset_audit_report.md section 1 and the chat
history -- the numeric base_id is currently just a photo-group number, not a
confirmed cyclone identity).

Pre-populated with the real 66 base_ids from the Phase 2 manifest so there's
nothing to transcribe by hand. Fill in storm_name / approx_date / basin_region
/ pre_landfall_confirmed / source_notes per row -- from your mentor, the
dataset's original source, or manual research -- then hand the completed file
back for ingestion into the master dataset.

One row (base_id 59) is pre-filled as a worked example: `data/raw/insat3d/raw/
59_LUBAN.jpg` already names the storm in the filename -- Cyclone Luban, Oct
2018, Arabian Sea (not Bay of Bengal / Odisha, which is itself a useful data
point -- some images in this set may not even be Odisha-relevant storms).

Usage: python src/data_prep/generate_event_metadata_template.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_CSV = ROOT / "data" / "interim" / "insat3d_manifest.csv"
OUT_CSV = ROOT / "data" / "raw" / "insat3d" / "event_metadata_template.csv"

WORKED_EXAMPLE = {
    59: {
        "storm_name": "Luban",
        "year": 2018,
        "approx_date_or_range": "2018-10-06 to 2018-10-14",
        "basin_region": "Arabian Sea (NOT Bay of Bengal / Odisha)",
        "pre_landfall_confirmed": "Unknown",
        "source_notes": "Inferred from filename data/raw/insat3d/raw/59_LUBAN.jpg -- "
                         "verify against IBTrACS/IMD before trusting.",
    }
}

COLUMNS = [
    "base_id", "n_images", "storm_name", "year", "approx_date_or_range",
    "basin_region", "pre_landfall_confirmed", "source_notes",
]


def main():
    manifest = pd.read_csv(MANIFEST_CSV)

    rows = []
    for _, r in manifest.sort_values("base_id").iterrows():
        base_id = int(r["base_id"])
        n_images = int(r["n_raw"]) + int(r["n_infrared"])
        example = WORKED_EXAMPLE.get(base_id, {})
        rows.append({
            "base_id": base_id,
            "n_images": n_images,
            "storm_name": example.get("storm_name", ""),
            "year": example.get("year", ""),
            "approx_date_or_range": example.get("approx_date_or_range", ""),
            "basin_region": example.get("basin_region", ""),
            "pre_landfall_confirmed": example.get("pre_landfall_confirmed", ""),
            "source_notes": example.get("source_notes", ""),
        })

    df = pd.DataFrame(rows, columns=COLUMNS)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    print(f"Wrote {len(df)} rows (one per event) to {OUT_CSV}")
    print(f"1 row pre-filled as a worked example (base_id 59). {len(df) - 1} rows to fill in.")


if __name__ == "__main__":
    main()
