"""
Live-ingestion scaffold (forward work, per chat: "will .h5 help once we have
live data?" -- no, but the pretrained backbone does, and this is the pipeline
shape a live feed should land in instead).

The core idea this solves for in advance: every problem this project's Phase 1
audit hit with insat3d -- no capture timestamp, no storm identity, no lat/lon,
having to OCR it back out of old images after the fact (see
src/data_prep/extract_reference_metadata.py) -- goes away if new images are
tagged with that metadata AT INGESTION TIME instead of relying on the source
to have embedded it in the pixels. That's the one hard requirement a real
`Fetcher` implementation must satisfy: return capture_time (and lat/lon/storm
identity when the source provides it, which live feeds usually do and this
archival dataset didn't).

Architecture:
  Fetcher.fetch_new() -> list[FetchedImage]   (swap this per data source)
        |
        v
  ingest_one()  -- save raw bytes, preprocess, run through the trained
                   backbone (same TinyCNN + checkpoint as
                   extract_insat3d_features.py, so live embeddings live in
                   the same space as the historical ones), store the record
        |
        v
  SQLite (data/live/live_events.db) -- append-only event log, NOT another
  static HDF5 blob (HDF5 doesn't suit concurrently-arriving data -- see chat).
  Deduplicated on (source, source_id) so re-running a fetch is always safe.

No real Fetcher exists yet (no live source is connected -- see
replay_fetcher.py for how this is tested honestly in the meantime, using
already-verified historical events instead of fabricated data). Implementing
a real one (e.g. for MOSDAC/INSAT-3D) means writing a Fetcher subclass that
downloads new imagery and returns FetchedImage records with real
capture_time/lat/lon/storm identity from that source's own metadata --
everything below this point does not change.

Usage (with the replay fetcher, to exercise the whole pipeline end-to-end):
  python src/ingestion/pipeline.py
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cv_models"))
from backbone import TinyCNN

ROOT = Path(__file__).resolve().parents[2]
LIVE_DIR = ROOT / "data" / "live"
RAW_DIR = LIVE_DIR / "raw"
DB_PATH = LIVE_DIR / "live_events.db"
CHECKPOINT_PATH = ROOT / "src" / "cv_models" / "checkpoints" / "tcir_backbone.pt"
INPUT_SIZE = (128, 128)  # matches the trained backbone, same as extract_insat3d_features.py

SCHEMA = """
CREATE TABLE IF NOT EXISTS live_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    capture_time TEXT,
    lat REAL,
    lon REAL,
    storm_id TEXT,
    storm_name TEXT,
    image_path TEXT NOT NULL,
    vmax_proxy_kt REAL,
    embedding_json TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    UNIQUE(source, source_id)
);
"""


@dataclass
class FetchedImage:
    """What every Fetcher implementation must produce per new image. Only
    `image_bytes`, `source`, and `source_id` are hard requirements -- the
    rest should be filled in whenever the source provides it (a real live
    feed usually does; that's the whole point of this design)."""
    image_bytes: bytes
    source: str                    # e.g. "mosdac_insat3d", "replay"
    source_id: str                 # unique within `source`, used for dedup
    capture_time: datetime | None = None
    lat: float | None = None
    lon: float | None = None
    storm_id: str | None = None
    storm_name: str | None = None


class Fetcher(ABC):
    """Swap this per real data source. See replay_fetcher.py for the only
    implementation that exists right now (test/demo, not live)."""

    @abstractmethod
    def fetch_new(self) -> list[FetchedImage]:
        ...


def load_backbone():
    ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
    model = TinyCNN(embed_dim=ckpt["embed_dim"])
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model, ckpt


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def _embed_image(image_bytes: bytes, model, x_mean: float, x_std: float):
    from io import BytesIO
    with Image.open(BytesIO(image_bytes)) as im:
        im = im.convert("L").resize(INPUT_SIZE, Image.BILINEAR)
        arr = np.asarray(im, dtype=np.float32)
    arr = (arr - x_mean) / x_std
    x = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)
    with torch.no_grad():
        pred, embed = model(x)
    return pred.item(), embed.squeeze(0).tolist()


def ingest_one(fetched: FetchedImage, model, ckpt, raw_dir: Path = RAW_DIR) -> dict:
    """Saves the raw image, extracts a feature embedding with the trained
    backbone, and returns the full record ready to insert into the DB."""
    vmax_norm, embedding = _embed_image(fetched.image_bytes, model, ckpt["x_mean"], ckpt["x_std"])
    vmax_proxy_kt = vmax_norm * ckpt["y_std"] + ckpt["y_mean"]

    storm_label = fetched.storm_id or fetched.storm_name or "unknown"
    time_label = fetched.capture_time.strftime("%Y%m%dT%H%M%S") if fetched.capture_time else "unknown_time"
    image_dir = raw_dir / storm_label
    image_dir.mkdir(parents=True, exist_ok=True)
    image_path = image_dir / f"{fetched.source}_{fetched.source_id}_{time_label}.jpg"
    image_path.write_bytes(fetched.image_bytes)

    return {
        "source": fetched.source,
        "source_id": fetched.source_id,
        "capture_time": fetched.capture_time.isoformat() if fetched.capture_time else None,
        "lat": fetched.lat,
        "lon": fetched.lon,
        "storm_id": fetched.storm_id,
        "storm_name": fetched.storm_name,
        "image_path": str(image_path.relative_to(ROOT)),
        "vmax_proxy_kt": float(vmax_proxy_kt),
        "embedding_json": json.dumps(embedding),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


def run_ingestion_cycle(fetcher: Fetcher, conn: sqlite3.Connection | None = None,
                         model=None, ckpt=None, raw_dir: Path = RAW_DIR) -> int:
    """Fetch whatever's new, ingest each, insert (deduped) into the DB.
    Returns the number of genuinely new rows inserted."""
    own_conn = conn is None
    conn = conn or init_db()
    if model is None:
        model, ckpt = load_backbone()

    fetched_images = fetcher.fetch_new()
    inserted = 0
    for fi in fetched_images:
        record = ingest_one(fi, model, ckpt, raw_dir)
        cur = conn.execute(
            """INSERT OR IGNORE INTO live_events
               (source, source_id, capture_time, lat, lon, storm_id, storm_name,
                image_path, vmax_proxy_kt, embedding_json, ingested_at)
               VALUES (:source, :source_id, :capture_time, :lat, :lon, :storm_id,
                       :storm_name, :image_path, :vmax_proxy_kt, :embedding_json, :ingested_at)""",
            record,
        )
        if cur.rowcount:
            inserted += 1
    conn.commit()
    if own_conn:
        conn.close()
    return inserted


def main():
    from replay_fetcher import ReplayFetcher

    print("No real Fetcher is connected yet -- running the ReplayFetcher instead, "
          "which replays already-verified historical events (real capture time/lat/"
          "lon/storm identity from insat3d_event_identity.csv) to exercise this "
          "pipeline end-to-end honestly. Swap in a real Fetcher subclass when a live "
          "source is available; nothing else here needs to change.")

    model, ckpt = load_backbone()
    conn = init_db()
    fetcher = ReplayFetcher()
    n = run_ingestion_cycle(fetcher, conn, model, ckpt)

    total = conn.execute("SELECT COUNT(*) FROM live_events").fetchone()[0]
    print(f"\nIngested {n} new record(s) this cycle ({total} total in {DB_PATH.relative_to(ROOT)})")
    conn.close()


if __name__ == "__main__":
    main()
