"""
Phase 4/7/9 unblock: real Odisha district-level exposure data from the Census
of India 2011 Primary Census Abstract (data/raw/census/2011-IndiaStateDist-0000.xlsx).

This is the first real source for the `exposure` placeholder group in
build_master_dataset.py and the "population exposure" node feature SRS
section 11 calls for on the district graph. It fills `district_population`
for real. It does NOT fill `infrastructure_index` -- the PCA has no physical
infrastructure inventory (roads, shelters, hospitals; that's OSDMA territory),
so that column stays an honest placeholder. What the PCA does give beyond raw
population -- households, literacy, worker participation, urbanization -- are
added as clearly-separate, clearly-real socioeconomic exposure/vulnerability
columns, not disguised as "infrastructure."

Two finer-grained Census files also exist (data/raw/census/) but aren't
processed here: -SbDist (~20k rows, subdistrict/tehsil level -- would align
with gadm41_IND_3 if sub-district granularity is ever needed) and
-SbDistTwnWrd (~110k rows, town/ward level -- far finer than the current
30-district graph). Both are far more detail than the current district-level
graph/master-dataset schema uses; process them only if a future need for that
granularity materializes.

Outputs:
  - data/processed/odisha_district_population.csv (one row per district)

Usage: python src/data_prep/build_odisha_district_population.py
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CENSUS_XLSX = ROOT / "data" / "raw" / "census" / "2011-IndiaStateDist-0000.xlsx"
DATA_PROCESSED = ROOT / "data" / "processed"
OUT_CSV = DATA_PROCESSED / "odisha_district_population.csv"

ODISHA_STATE_CODE = 21


def main():
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(CENSUS_XLSX, sheet_name="Data")

    odisha = df[(df["State"] == ODISHA_STATE_CODE) & (df["Level"] == "DISTRICT")]

    total = odisha[odisha["TRU"] == "Total"].set_index("District")
    urban = odisha[odisha["TRU"] == "Urban"].set_index("District")["TOT_P"].rename("urban_pop")

    # Census's own "Name" field has fixed-width padding (trailing spaces) and
    # at least one spelling that differs from our boundary shapefile ("Baudh"
    # vs "Bauda") -- use the shapefile's names as canonical (censuscode is the
    # reliable join key either way) so every processed file agrees on one
    # spelling per district, rather than three slightly different ones.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_odisha_district_graph import load_odisha_districts
    canonical_name = {d["censuscode"]: d["district"] for d in load_odisha_districts()}

    out = pd.DataFrame({
        "censuscode": total.index,
        "district": [canonical_name.get(c, str(c).strip()) for c in total.index],
        "district_population": total["TOT_P"].values,
        "district_households": total["No_HH"].values,
        "district_literacy_rate": (total["P_LIT"] / total["TOT_P"]).round(4).values,
        "district_worker_participation_rate": (total["TOT_WORK_P"] / total["TOT_P"]).round(4).values,
    })
    out["district_urban_population_pct"] = out["censuscode"].map(
        (urban / total["TOT_P"]).round(4)
    ).fillna(0.0)  # districts with no urban rows in the file are fully rural

    out = out.sort_values("district").reset_index(drop=True)
    out.to_csv(OUT_CSV, index=False)

    print(f"Extracted real Census 2011 exposure data for {len(out)} Odisha districts")
    print(f"  population range: {out.district_population.min():,} - {out.district_population.max():,}")
    print(f"  total Odisha population (2011): {out.district_population.sum():,}")
    print(f"Wrote {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
