"""
Phase 1 dataset audit (SRS section 4 / 22).

Runs entirely on CPU. Produces:
  - data/interim/insat3d_image_index.csv   (every insat3d file, its base id, folder, size)
  - data/interim/insat3d_event_index.csv   (base id -> image count, filenames)
  - docs/dataset_audit_report.md           (human-readable summary)

Usage: python src/data_prep/dataset_audit.py
"""

import re
import json
from pathlib import Path
from collections import defaultdict

import pandas as pd
import numpy as np
from PIL import Image
import h5py

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DOCS = ROOT / "docs"

INSAT3D_DIR = DATA_RAW / "insat3d"
INSAT3D_SUBFOLDERS = ["raw", "infrared", "reference"]
EVENT_LABELS_CSV = INSAT3D_DIR / "event_labels.csv"
TCIR_H5 = DATA_RAW / "tcir_global" / "images.h5"
TCIR_LABELS = DATA_RAW / "tcir_global" / "labels.npy"
HISTORICAL_CSV = DATA_RAW / "historical" / "imd_cyclone_frequency_1891_2016.csv"

BASE_ID_RE = re.compile(r"^(\d+)")


def extract_base_id(filename: str):
    m = BASE_ID_RE.match(filename)
    return int(m.group(1)) if m else None


def audit_insat3d():
    rows = []
    for sub in INSAT3D_SUBFOLDERS:
        folder = INSAT3D_DIR / sub
        if not folder.exists():
            continue
        for f in sorted(folder.iterdir()):
            if not f.is_file():
                continue
            base_id = extract_base_id(f.name)
            width = height = mode = None
            corrupt = False
            try:
                with Image.open(f) as im:
                    width, height = im.size
                    mode = im.mode
            except Exception:
                corrupt = True
            rows.append({
                "folder": sub,
                "filename": f.name,
                "base_id": base_id,
                "width": width,
                "height": height,
                "mode": mode,
                "bytes": f.stat().st_size,
                "corrupt": corrupt,
            })
    df = pd.DataFrame(rows)
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_INTERIM / "insat3d_image_index.csv", index=False)

    # per-folder counts
    folder_counts = df.groupby("folder")["filename"].count().to_dict()

    # base_id presence across folders (leakage / mismatch check)
    presence = defaultdict(set)
    for _, r in df.iterrows():
        if r["base_id"] is not None:
            presence[r["base_id"]].add(r["folder"])
    all_ids = sorted(presence.keys())
    missing = {sub: [i for i in all_ids if sub not in presence[i]] for sub in INSAT3D_SUBFOLDERS}

    # event_labels.csv cross-check
    labels_df = pd.read_csv(EVENT_LABELS_CSV) if EVENT_LABELS_CSV.exists() else pd.DataFrame()
    label_ids = set(labels_df["label"].unique()) if not labels_df.empty else set()
    infrared_ids = set(df[df.folder == "infrared"]["base_id"].dropna().unique())
    labels_not_in_infrared = sorted(label_ids - infrared_ids)
    infrared_not_in_labels = sorted(infrared_ids - label_ids)

    # event size distribution (using base_id as the grouping key = current "event" proxy)
    event_sizes = df[df.folder == "infrared"].groupby("base_id")["filename"].count()
    duplicate_variant_ids = sorted(event_sizes[event_sizes > 1].index.tolist())

    # image dimension consistency
    dims = df.dropna(subset=["width", "height"])
    dim_value_counts = dims.groupby(["folder", "width", "height", "mode"]).size().reset_index(name="count")

    corrupt_files = df[df.corrupt]["filename"].tolist()

    return {
        "folder_counts": folder_counts,
        "total_unique_base_ids": len(all_ids),
        "missing_across_folders": missing,
        "label_count": len(label_ids),
        "labels_not_in_infrared": labels_not_in_infrared,
        "infrared_not_in_labels": infrared_not_in_labels,
        "duplicate_variant_ids": duplicate_variant_ids,
        "n_duplicate_variant_ids": len(duplicate_variant_ids),
        "dim_value_counts": dim_value_counts,
        "corrupt_files": corrupt_files,
        "event_sizes": event_sizes,
    }


def audit_tcir():
    with h5py.File(TCIR_H5, "r") as f:
        images = f["Images"]
        shape = images.shape
        dtype = str(images.dtype)
        # sample-based channel stats (avoid loading all 21k images into RAM)
        rng = np.random.default_rng(42)
        idx = np.sort(rng.choice(shape[0], size=min(200, shape[0]), replace=False))
        sample = images[idx]  # h5py requires sorted indices for fancy indexing
        channel_mean = sample.mean(axis=(0, 1, 2)).tolist()
        channel_std = sample.std(axis=(0, 1, 2)).tolist()
        channel_min = sample.min(axis=(0, 1, 2)).tolist()
        channel_max = sample.max(axis=(0, 1, 2)).tolist()

    labels = np.load(TCIR_LABELS, allow_pickle=True)
    cols = ["basin", "storm_id", "lon", "lat", "time", "vmax", "r35", "mslp"]
    lab_df = pd.DataFrame(labels, columns=cols)
    basin_counts = lab_df["basin"].value_counts().to_dict()
    storm_count = lab_df["storm_id"].nunique()
    vmax_stats = lab_df["vmax"].astype(float).describe().to_dict()
    mslp_stats = lab_df["mslp"].astype(float).describe().to_dict()

    return {
        "shape": shape,
        "dtype": dtype,
        "channel_mean": channel_mean,
        "channel_std": channel_std,
        "channel_min": channel_min,
        "channel_max": channel_max,
        "basin_counts": basin_counts,
        "unique_storms": storm_count,
        "vmax_stats": vmax_stats,
        "mslp_stats": mslp_stats,
    }


def audit_historical():
    df = pd.read_csv(HISTORICAL_CSV)
    year_col = df.columns[0]
    total_col = [c for c in df.columns if c.strip().lower().startswith("january - december (whole year): total")]
    total_col = total_col[0] if total_col else None
    summary = {
        "n_years": len(df),
        "year_range": [int(df[year_col].min()), int(df[year_col].max())],
        "n_columns": len(df.columns),
    }
    if total_col:
        summary["total_cyclones_per_year_stats"] = df[total_col].describe().to_dict()
    return summary


def write_report(insat3d_result, tcir_result, historical_result):
    lines = []
    lines.append("# IDMAP-Cyclone — Dataset Audit Report (Phase 1)\n")
    lines.append("Auto-generated by `src/data_prep/dataset_audit.py`. Runs on CPU only.\n")

    lines.append("## 1. INSAT3D imagery (`data/raw/insat3d/`)\n")
    lines.append(f"- Folder counts: {insat3d_result['folder_counts']}")
    lines.append(f"- Unique numeric base IDs across all folders: {insat3d_result['total_unique_base_ids']}")
    lines.append(f"- IDs missing from at least one folder (raw/infrared/reference mismatch):")
    for sub, missing_ids in insat3d_result["missing_across_folders"].items():
        lines.append(f"  - missing from **{sub}**: {missing_ids if missing_ids else 'none'}")
    lines.append(f"- `event_labels.csv` has {insat3d_result['label_count']} unique labels")
    lines.append(f"  - labels with no matching infrared file: {insat3d_result['labels_not_in_infrared'] or 'none'}")
    lines.append(f"  - infrared files with no matching label row: {insat3d_result['infrared_not_in_labels'] or 'none'}")
    lines.append(
        f"- base IDs with more than one image variant (e.g. `35.jpg`, `35(1).jpg`, `35(2).jpg`): "
        f"{insat3d_result['n_duplicate_variant_ids']} ids -> {insat3d_result['duplicate_variant_ids']}"
    )
    lines.append(f"- corrupt / unreadable files: {insat3d_result['corrupt_files'] or 'none'}")
    lines.append("\n**Image dimension / mode breakdown (folder, width, height, mode, count):**\n")
    lines.append("```")
    lines.append(insat3d_result["dim_value_counts"].to_string(index=False))
    lines.append("```")
    lines.append(
        "\n**Important open question:** the numeric filename prefix (e.g. `35`) is currently the only "
        "grouping key available, and it is what `event_labels.csv`'s `label` column reproduces. It is "
        "unclear from the data alone whether this numeric ID identifies a distinct **cyclone event** "
        "(storm) or just a **photo/sequence number** with duplicate quality variants. This must be "
        "confirmed (with the mentor or original data source) before doing event-wise train/val/test "
        "splitting, since the SRS's leakage-mitigation strategy depends on splitting by real cyclone "
        "identity, not by image-sequence number.\n"
    )

    lines.append("## 2. TCIR global dataset (`data/raw/tcir_global/`)\n")
    lines.append(f"- Images shape: {tcir_result['shape']} , dtype: {tcir_result['dtype']}")
    lines.append(f"- Per-channel mean (sample of 200 images): {tcir_result['channel_mean']}")
    lines.append(f"- Per-channel std: {tcir_result['channel_std']}")
    lines.append(f"- Per-channel min/max: {tcir_result['channel_min']} / {tcir_result['channel_max']}")
    lines.append(f"- Basin distribution: {tcir_result['basin_counts']}")
    lines.append(f"- Unique storms: {tcir_result['unique_storms']}")
    lines.append(f"- Vmax (knots) stats: {tcir_result['vmax_stats']}")
    lines.append(f"- MSLP (hPa) stats: {tcir_result['mslp_stats']}")
    lines.append(
        "\n**Scope note:** this is a *global* tropical-cyclone dataset (basin codes like `ATLN`, not "
        "North Indian Ocean / Odisha-specific), 4-channel 128x128 imagery with tabular intensity labels "
        "(Vmax, MSLP). Per the SRS's Odisha-only scope, this is best used for **pretraining / transfer "
        "learning** of the lightweight CV backbones (large sample size, clean numeric labels), not as "
        "the primary Odisha risk-modeling source. Flagging for a scope decision.\n"
    )

    lines.append("## 3. Historical IMD cyclone frequency (`data/raw/historical/`)\n")
    lines.append(f"- Years covered: {historical_result['year_range'][0]}–{historical_result['year_range'][1]} "
                  f"({historical_result['n_years']} rows)")
    lines.append(f"- Columns: {historical_result['n_columns']} (monthly/seasonal counts by BOB/AS/Land/Total)")
    if "total_cyclones_per_year_stats" in historical_result:
        lines.append(f"- Whole-year total cyclone count stats: {historical_result['total_cyclones_per_year_stats']}")
    lines.append(
        "\nUsable directly as a historical-context feature source (e.g. seasonal base rate by basin) "
        "for the XGBoost current-risk model, per SRS section 7/8.\n"
    )

    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "dataset_audit_report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    print("Auditing INSAT3D imagery...")
    insat3d_result = audit_insat3d()

    print("Auditing TCIR global dataset (sampled, CPU-only)...")
    tcir_result = audit_tcir()

    print("Auditing historical IMD cyclone frequency data...")
    historical_result = audit_historical()

    write_report(insat3d_result, tcir_result, historical_result)

    print("\nDone.")
    print(f"- Report: {DOCS / 'dataset_audit_report.md'}")
    print(f"- Image index: {DATA_INTERIM / 'insat3d_image_index.csv'}")


if __name__ == "__main__":
    main()
