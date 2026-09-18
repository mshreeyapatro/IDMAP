# Live Satellite Ingestion Pipeline (Scaffold)

Forward-looking piece, built ahead of having an actual live data source
connected (per chat: no source is picked yet). This is the pipeline shape a
live feed should land in, designed specifically so the problem this project
spent an entire session solving for insat3d — no timestamp, no storm
identity, no lat/lon, having to OCR it back out of old images after the fact
(`src/data_prep/extract_reference_metadata.py`) — never happens again once
new imagery starts flowing in.

## The one rule a real data source must follow

Whatever `Fetcher` eventually talks to a real satellite feed must return
**capture time, and lat/lon/storm identity whenever the source provides
it**, at the moment each image is ingested. That's it. Most live feeds give
you this for free (a satellite pass has a known timestamp; if the source
publishes an active-storm feed, it usually tags images with a storm ID
already) — it's archival data, stripped of its original metadata, that
forces the reverse-engineering this project just went through.

## Why not another `.h5` file

Discussed in chat: HDF5 suits one static, already-collected batch (like
TCIR). A live feed is the opposite — images arrive continuously, one at a
time, and you don't want a live system writing into one shared, growing
binary file. This pipeline instead: saves each image as its own file
(organized by storm ID) and logs metadata + extracted features as a new row
in a SQLite database — append-only, safe under repeated/concurrent runs,
queryable directly with SQL.

## Architecture

```
Fetcher.fetch_new() -> list[FetchedImage]     <- swap this per real data source
        │
        v
ingest_one()
  - save raw image bytes -> data/live/raw/<storm_id>/<source>_<id>_<time>.jpg
  - preprocess (grayscale, resize to 128x128 -- same as extract_insat3d_features.py)
  - run through the TCIR-pretrained backbone (same checkpoint, same embedding
    space as the historical insat3d features -- so live and historical data
    are directly comparable, no separate re-training needed)
        │
        v
SQLite insert, deduplicated on (source, source_id)
  -> data/live/live_events.db, table `live_events`
```

## What exists right now vs. what's still a placeholder

| Piece | Status |
|---|---|
| `src/ingestion/pipeline.py` — `Fetcher` interface, ingestion logic, SQLite schema | Built, tested |
| `src/ingestion/replay_fetcher.py` — `ReplayFetcher` | Built, tested — **not a live source**. Replays the 66 already-verified historical events from `insat3d_event_identity.csv` (real dates/lat-lon/storm names, honestly re-used, not fabricated) so the pipeline could be built and proven correct against real data before any live connection exists |
| A real `Fetcher` (e.g. for MOSDAC/INSAT-3D, or another provider) | **Not built** — needs a real account/API, which hasn't been picked yet (see chat) |
| Wiring live records into the dashboard/agent tools | Not built — natural next step once a real Fetcher exists |

## Verified test run

```
python src/ingestion/pipeline.py
```
- 1st run: 66/66 historical events ingested (61 with a storm name, 5 genuine
  unnamed depressions — matches `insat3d_event_identity.csv` exactly)
- 2nd run (same command, no new data): 0 new rows — dedup confirmed working
- Each row carries a real `capture_time`, `lat`/`lon`, `storm_id`,
  `storm_name`, its saved image path, a `vmax_proxy_kt` estimate, and a
  32-dim embedding from the trained backbone — spot-checked against known
  values (e.g. Amphan/Bulbul/Chapala rows match their real dates and
  coordinates)

## Adding a real source later

Write a new `Fetcher` subclass (see `replay_fetcher.py` for the shape) whose
`fetch_new()` downloads new imagery from the real API and returns
`FetchedImage` objects with that source's own timestamp/lat-lon/storm-ID
metadata. Nothing in `pipeline.py` needs to change. Swap it into `main()` (or
call `run_ingestion_cycle()` directly) and run on a schedule (cron / Task
Scheduler) once picked.
