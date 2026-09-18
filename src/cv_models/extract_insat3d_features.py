"""
Phase 3, step 2: apply the TCIR-pretrained backbone to every insat3d image to
produce the "cyclone visual features" that Phase 4 (feature fusion) consumes.

For each image, outputs:
  - a 32-dim embedding vector (Model 10: deep feature extraction, SRS section 5)
  - `tcir_vmax_proxy_kt`: the backbone's regression head output, UNVALIDATED for
    insat3d (Model 2: intensity-related estimation candidate, but with no insat3d
    ground truth to check it against -- treat as an exploratory signal, not a
    calibrated wind-speed estimate).

Usage: python src/cv_models/extract_insat3d_features.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backbone import TinyCNN

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed" / "insat3d"
CHECKPOINT_PATH = ROOT / "src" / "cv_models" / "checkpoints" / "tcir_backbone.pt"
OUT_CSV = ROOT / "data" / "processed" / "insat3d_cv_features.csv"

INPUT_SIZE = (128, 128)  # matches TCIR backbone's expected input


def load_backbone():
    ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu")
    model = TinyCNN(embed_dim=ckpt["embed_dim"])
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model, ckpt


def image_to_tensor(path: Path, x_mean: float, x_std: float):
    with Image.open(path) as im:
        im = im.convert("L").resize(INPUT_SIZE, Image.BILINEAR)
        arr = np.asarray(im, dtype=np.float32)
    arr = (arr - x_mean) / x_std
    return torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)  # (1,1,H,W)


def main():
    model, ckpt = load_backbone()
    x_mean, x_std = ckpt["x_mean"], ckpt["x_std"]
    y_mean, y_std = ckpt["y_mean"], ckpt["y_std"]

    rows = []
    for modality_dir in ["raw", "infrared"]:
        modality_root = PROCESSED_DIR / modality_dir
        if not modality_root.exists():
            continue
        for split_dir in sorted(modality_root.iterdir()):
            if not split_dir.is_dir():
                continue
            split = split_dir.name
            for base_id_dir in sorted(split_dir.iterdir(), key=lambda p: int(p.name)):
                base_id = int(base_id_dir.name)
                for img_path in sorted(base_id_dir.iterdir()):
                    x = image_to_tensor(img_path, x_mean, x_std)
                    with torch.no_grad():
                        pred, embed = model(x)
                    vmax_proxy = float(pred.item()) * y_std + y_mean
                    row = {
                        "base_id": base_id,
                        "split": split,
                        "modality": modality_dir,
                        "filename": img_path.name,
                        "tcir_vmax_proxy_kt": vmax_proxy,
                    }
                    for i, v in enumerate(embed.squeeze(0).tolist()):
                        row[f"embed_{i:02d}"] = v
                    rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"Extracted features for {len(df)} images ({df.modality.value_counts().to_dict()})")
    print(f"Saved: {OUT_CSV}")
    print(f"\ntcir_vmax_proxy_kt summary (exploratory / unvalidated for insat3d):")
    print(df["tcir_vmax_proxy_kt"].describe())


if __name__ == "__main__":
    main()
