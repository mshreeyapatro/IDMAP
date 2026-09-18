"""
Phase 2: data preparation (SRS roadmap phase 2 / section 4 "event-wise splitting").

Runs entirely on CPU. Reads the Phase 1 audit index and produces:
  - data/processed/insat3d/{raw,infrared}/<split>/<base_id>/<filename>.jpg
        resized to a canonical size, split-assigned, leakage-safe.
  - data/interim/insat3d_manifest.csv
        one row per base_id: split assignment, available raw/infrared files,
        best-effort raw<->infrared pairing.
  - data/interim/insat3d_manifest.json
        same info, machine-readable, plus the cleanup flags.

IMPORTANT CAVEAT (see docs/dataset_audit_report.md section 1): the "base_id" grouping
used here is the numeric filename prefix, which is the only grouping key available.
It has NOT been confirmed to correspond to a real distinct cyclone/storm identity.
Until that is confirmed, this script's split is a leakage-safe *image-group* split
(duplicate-quality variants of the same photo never cross splits), not a guaranteed
leakage-safe *storm* split. Re-run once real storm IDs are available.

Usage: python src/data_prep/prepare_dataset.py
"""

import json
import re
from pathlib import Path

import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw" / "insat3d"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed" / "insat3d"

IMAGE_INDEX_CSV = DATA_INTERIM / "insat3d_image_index.csv"
CANONICAL_SIZE = (224, 224)  # standard lightweight-CNN input size
SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
SEED = 42

KNOWN_RAW_INFRARED_MISMATCHES = {
    # filename in raw/ -> best-guess corresponding filename in infrared/
    # left here from the Phase 1 audit; not auto-corrected, flagged for manual review.
    "34(!).jpg": "34(1).jpg",
    "55.JPEG": "55.jpg",
    "59_LUBAN.jpg": "59(3).jpg",
    "59_LUBAN 2.jpg": None,
    "67 2.jpg": None,
    "68(1).jpg": None,
    "81 2.jpg": "81(1).jpg",
    "84 2.jpg": "84(1).jpg",
    "54 2.jpg": None,
}


def balanced_group_split(group_sizes: dict, ratios: dict, seed: int):
    """Greedy bin-packing: assign each base_id (group) whole to one split,
    always to whichever split is furthest below its target share of TOTAL IMAGES.
    Keeps splits balanced by image count even though group sizes vary (1-6 images)."""
    import random

    rng = random.Random(seed)
    groups = list(group_sizes.items())
    rng.shuffle(groups)
    groups.sort(key=lambda kv: kv[1], reverse=True)  # largest groups first

    total = sum(group_sizes.values())
    targets = {k: v * total for k, v in ratios.items()}
    assigned_count = {k: 0 for k in ratios}
    assignment = {}

    for base_id, size in groups:
        # pick split with the largest remaining deficit (target - assigned)
        deficits = {k: targets[k] - assigned_count[k] for k in ratios}
        chosen = max(deficits, key=deficits.get)
        assignment[base_id] = chosen
        assigned_count[chosen] += size

    return assignment, assigned_count


def clean_and_resize(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = im.convert("RGB")
        im = im.resize(CANONICAL_SIZE, Image.BILINEAR)
        im.save(dst, "JPEG", quality=95)


def main():
    df = pd.read_csv(IMAGE_INDEX_CSV)
    df = df[df.folder.isin(["raw", "infrared"])].copy()
    df = df.dropna(subset=["base_id"])
    df["base_id"] = df["base_id"].astype(int)

    # one group per base_id, sized by total (raw + infrared) image count
    group_sizes = df.groupby("base_id")["filename"].count().to_dict()
    assignment, assigned_count = balanced_group_split(group_sizes, SPLIT_RATIOS, SEED)

    print("Split image-count balance:", assigned_count,
          f"(target ratios {SPLIT_RATIOS})")

    manifest_rows = []
    for base_id, group_df in df.groupby("base_id"):
        split = assignment[base_id]
        raw_files = sorted(group_df[group_df.folder == "raw"]["filename"].tolist())
        ir_files = sorted(group_df[group_df.folder == "infrared"]["filename"].tolist())

        # best-effort pairing: exact filename match first, then positional pairing
        # for whatever's left, so single-modality-only files are still usable
        # (just unpaired) rather than dropped.
        paired = []
        remaining_raw = list(raw_files)
        remaining_ir = list(ir_files)
        for fn in list(remaining_raw):
            if fn in remaining_ir:
                paired.append((fn, fn))
                remaining_raw.remove(fn)
                remaining_ir.remove(fn)
        for rfn in list(remaining_raw):
            guess = KNOWN_RAW_INFRARED_MISMATCHES.get(rfn)
            if guess and guess in remaining_ir:
                paired.append((rfn, guess))
                remaining_raw.remove(rfn)
                remaining_ir.remove(guess)

        # copy + resize everything into data/processed, split-partitioned
        for fn in raw_files:
            clean_and_resize(
                DATA_RAW / "raw" / fn,
                DATA_PROCESSED / "raw" / split / str(base_id) / fn,
            )
        for fn in ir_files:
            clean_and_resize(
                DATA_RAW / "infrared" / fn,
                DATA_PROCESSED / "infrared" / split / str(base_id) / fn,
            )

        manifest_rows.append({
            "base_id": base_id,
            "split": split,
            "n_raw": len(raw_files),
            "n_infrared": len(ir_files),
            "raw_files": raw_files,
            "infrared_files": ir_files,
            "paired_files": paired,
            "unpaired_raw": remaining_raw,
            "unpaired_infrared": remaining_ir,
        })

    manifest_df = pd.DataFrame(manifest_rows)
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    manifest_df.to_csv(DATA_INTERIM / "insat3d_manifest.csv", index=False)
    with open(DATA_INTERIM / "insat3d_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_rows, f, indent=2)

    split_counts = manifest_df.groupby("split")["base_id"].count().to_dict()
    n_unpaired = sum(len(r["unpaired_raw"]) + len(r["unpaired_infrared"]) for r in manifest_rows)

    print("\nDone.")
    print(f"- Groups (base_ids) per split: {split_counts}")
    print(f"- Images left unpaired (single-modality only, still usable): {n_unpaired}")
    print(f"- Cleaned images: {DATA_PROCESSED}")
    print(f"- Manifest: {DATA_INTERIM / 'insat3d_manifest.csv'}")


if __name__ == "__main__":
    main()
