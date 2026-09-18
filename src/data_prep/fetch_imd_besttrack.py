"""
Candidate risk-label source: IMD RSMC New Delhi best-track record, filtered to
systems that tracked near or over Odisha, 2013-2021 (the window the insat3d
imagery is believed to span -- see docs/dataset_audit_report.md's "source
traced" note).

This does NOT resolve the blocking gap in the dataset audit (the insat3d numeric
base_id has no confirmed link to a real storm identity or date). What it gives
you is a concrete, dated, named candidate list to manually cross-check base_ids
against -- e.g. by comparing image counts/visual intensity progression for a
base_id against a real storm's known track length and peak grade.

"Near Odisha" = at least one 3-hourly observation fix within 1 degree
(~110 km) of the union of Odisha's 30 district polygons. That deliberately
includes weak, unnamed depressions/deep depressions along with the well-known
named cyclones, since even weak systems could plausibly be what a given
base_id depicts.

Data source: IMD RSMC New Delhi best-track workbook (1982-present), via the
`imdtrack` package's pre-parsed GitHub mirror (kept in sync with IMD's own
publication) -- see https://github.com/syedhamidali/imdtrack.

Outputs:
  - data/raw/historical/imd_besttrack_odisha_2013_2021.csv (one row per storm)

Usage: python src/data_prep/fetch_imd_besttrack.py
"""

from pathlib import Path

import imdtrack as imd
import shapefile  # pyshp
from shapely.geometry import Point, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
DISTRICTS_SHP = ROOT / "data" / "raw" / "boundaries" / "india_districts_census2011" / "2011_Dist.shp"
OUT_CSV = ROOT / "data" / "raw" / "historical" / "imd_besttrack_odisha_2013_2021.csv"

YEAR_START, YEAR_END = 2013, 2021
NEAR_ODISHA_BUFFER_DEG = 1.0  # ~110 km


def load_odisha_union():
    sf = shapefile.Reader(str(DISTRICTS_SHP))
    fields = [f[0] for f in sf.fields[1:]]
    polys = []
    for sr in sf.iterShapeRecords():
        rec = dict(zip(fields, sr.record))
        if str(rec.get("ST_NM", "")).strip() != "Odisha":
            continue
        g = shape(sr.shape.__geo_interface__)
        if not g.is_valid:
            g = g.buffer(0)
        polys.append(g)
    return unary_union(polys)


def main():
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    odisha = load_odisha_union()
    odisha_buffered = odisha.buffer(NEAR_ODISHA_BUFFER_DEG)

    bt = imd.load()
    print(f"Loaded IMD best-track record (content hash {bt.sha256[:16]}...)")

    obs = bt.observations
    obs = obs[
        (obs.year >= YEAR_START) & (obs.year <= YEAR_END) & (obs.basin == "BOB")
    ].dropna(subset=["lat", "lon"])

    near_ids = set()
    min_dist_km = {}
    for row in obs.itertuples():
        p = Point(row.lon, row.lat)
        if odisha_buffered.contains(p):
            near_ids.add(row.storm_id)
            d = odisha.distance(p) * 111.0  # deg -> km, regional approximation
            min_dist_km[row.storm_id] = min(min_dist_km.get(row.storm_id, 1e9), d)

    storms = bt.storms.set_index("storm_id")
    result = storms.loc[sorted(near_ids)][
        ["year", "name", "start_time", "end_time", "n_obs", "max_wind", "min_pressure", "peak_grade"]
    ].copy()
    result["min_dist_to_odisha_km"] = [round(min_dist_km[i], 1) for i in result.index]
    result = result.sort_values("start_time").reset_index()

    result.to_csv(OUT_CSV, index=False)

    n_named = result["name"].notna().sum()
    n_landfall = (result["min_dist_to_odisha_km"] == 0.0).sum()
    print(f"{len(result)} systems tracked near Odisha ({YEAR_START}-{YEAR_END}): "
          f"{n_named} named, {n_landfall} with a track point directly over Odisha")
    print(f"Wrote {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
