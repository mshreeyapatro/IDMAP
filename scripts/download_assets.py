"""
IDMAP Asset & Dataset Download Utility.

Downloads heavy model weights and training datasets on-demand from remote cloud
storage (Hugging Face / AWS S3 / Cloudflare R2 / Google Drive) into local caches.
"""

import os
import sys
import argparse
from pathlib import Path
import urllib.request

ROOT_DIR = Path(__file__).resolve().parents[1]

# Registry of remote dataset / weight mirrors
ASSET_REGISTRY = {
    "tc_ir_subset": {
        "dest": ROOT_DIR / "data" / "raw" / "tcir_subset",
        "url": os.getenv("TCIR_SUBSET_URL", ""),
        "desc": "TCIR Infrared Hurricane Satellite image subset",
    },
    "census_odisha": {
        "dest": ROOT_DIR / "data" / "raw" / "census",
        "url": os.getenv("CENSUS_DATA_URL", ""),
        "desc": "Odisha District Census & Vulnerability statistics",
    },
    "cnn_cyclone_weights": {
        "dest": ROOT_DIR / "src" / "cv_models" / "checkpoints" / "cyclone_cnn_v1.pt",
        "url": os.getenv("MODEL_WEIGHTS_URL", ""),
        "desc": "Pretrained PyTorch Cyclone Intensity ResNet Checkpoint",
    }
}


def download_file(url: str, dest_path: Path):
    if not url:
        print(f"[-] No URL provided for asset destination: {dest_path}")
        return False
        
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[*] Downloading {url} -> {dest_path}...")
    try:
        urllib.request.urlretrieve(url, str(dest_path))
        print(f"[+] Download complete: {dest_path} ({dest_path.stat().st_size / (1024*1024):.2f} MB)")
        return True
    except Exception as e:
        print(f"[!] Error downloading {url}: {e}")
        return False


def verify_or_download_all():
    print("=== IDMAP Asset Verification ===")
    for key, info in ASSET_REGISTRY.items():
        dest = info["dest"]
        if dest.exists():
            print(f"[OK] {key} exists at: {dest}")
        else:
            print(f"[MISSING] {key} ({info['desc']}) not found at: {dest}")
            if info["url"]:
                download_file(info["url"], dest)
            else:
                print(f"      To download automatically, set environment variable or copy manually.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download IDMAP dataset and model assets")
    parser.add_argument("--verify", action="store_true", help="Verify existence of key assets")
    args = parser.parse_args()
    verify_or_download_all()
