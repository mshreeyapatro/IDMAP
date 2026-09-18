"""
Phase 4: feature fusion / master dataset (SRS section 7).

Aggregates the per-image CV features (data/processed/insat3d_cv_features.csv) up
to one row per base_id (event/image-group) and joins in every other data group
the SRS's example master record calls for. Every group is written as an explicit
placeholder column (NaN + a paired `<group>_data_source_needed` flag) so the
schema is ready to receive real data without a pipeline rewrite, and so
downstream code can immediately see, per-column (and per-row -- some groups now
have real values for SOME events and not others), what is real vs. missing.

UPDATE: the original blocking gap here -- no confirmed link between insat3d's
numeric base_id and any real storm identity/date/location -- is resolved for
most events. src/data_prep/extract_reference_metadata.py discovered that the
`reference/` images have real capture date + TC-center lat/lon burned into the
image as text, OCR'd it, and matched every base_id against the IMD best-track
record (data/processed/insat3d_event_identity.csv). That fills in real
`temporal`, part of `meteorological` (wind/pressure, not rainfall/temperature),
and part of `geographic` (lat/lon/coastal_distance/district, not elevation --
still no DEM) for the base_ids it could match. `historical` is real only for
events before 1891-2016's coverage ends -- most matched storms are 2017+, so
it's mostly still placeholder too.

UPDATE 2: `exposure` is now partially real too, from Census 2011
(data/raw/census/, see build_odisha_district_population.py). `district_population`
is filled for Odisha-relevant events via NEAREST-district assignment, not
strict polygon containment -- most events are pre-landfall snapshots over open
water, so `district` (exact containment) is usually null even for a real
Odisha storm; `nearest_odisha_district` never is, for any Odisha-relevant
event, and is honestly named to not overclaim "the storm was over this
district" precision it doesn't have. `infrastructure_index` stays a genuine
placeholder -- Census has no physical infrastructure inventory (that's OSDMA
territory) -- but real Census-derived socioeconomic exposure columns
(households, literacy rate, worker participation, urbanization) are added
alongside it, clearly separate from "infrastructure."

Only 16 of the ~66 events are storms whose track actually came near Odisha
(`is_odisha_relevant` in the identity table) -- the rest are real cyclones from
elsewhere (mostly Arabian Sea). Every row keeps `is_odisha_relevant` so
downstream Odisha-specific modeling (phases 5/7/9) can filter to just those,
while the full set stays available for general CV pretraining, same treatment
as the TCIR dataset.

Usage: python src/layer2/feature_fusion/build_master_dataset.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[3]
CV_FEATURES_CSV = ROOT / "data" / "processed" / "insat3d_cv_features.csv"
IDENTITY_CSV = ROOT / "data" / "processed" / "insat3d_event_identity.csv"
HISTORICAL_FREQ_CSV = ROOT / "data" / "raw" / "historical" / "imd_cyclone_frequency_1891_2016.csv"
POPULATION_CSV = ROOT / "data" / "processed" / "odisha_district_population.csv"
OUT_CSV = ROOT / "data" / "processed" / "master_cyclone_dataset.csv"

# IMD best-track basin codes -> the historical frequency file's column suffix
BASIN_TO_HISTORICAL_COL = {"BOB": "BOB", "ARB": "AS"}


def _embed_cols(df: pd.DataFrame) -> list:
    """Detected from the CSV header rather than hardcoded, so a backbone with a
    different embed_dim (retraining, architecture change) doesn't silently
    truncate or error here."""
    return sorted(c for c in df.columns if c.startswith("embed_"))

PLACEHOLDER_GROUPS = {
    "temporal": {
        "cols": ["timestamp", "hours_before_landfall"],
        "needed": "per-image capture timestamp from the original (pre-rename) data source",
    },
    "meteorological": {
        "cols": ["wind_speed_kt", "pressure_hpa", "rainfall_mm", "temperature_c"],
        "needed": "IMD best-track records for the matching storm/date",
    },
    "geographic": {
        "cols": ["latitude", "longitude", "district", "coastal_distance_km", "elevation_m"],
        "needed": "cyclone-center lat/lon (from best-track) + Odisha district boundaries/DEM",
    },
    "exposure": {
        "cols": ["district_population", "infrastructure_index"],
        "needed": "Census/WorldPop population + district infrastructure inventory (e.g. OSDMA)",
    },
    "historical": {
        "cols": ["historical_basin_frequency", "historical_landfall_rate"],
        "needed": "the storm's year, to join against imd_cyclone_frequency_1891_2016.csv",
    },
}


def aggregate_cv_features() -> pd.DataFrame:
    df = pd.read_csv(CV_FEATURES_CSV)
    embed_cols = _embed_cols(df)

    records = []
    for base_id, g in df.groupby("base_id"):
        split = g["split"].iloc[0]
        record = {"cyclone_id": base_id, "split": split}

        for modality in ["raw", "infrared"]:
            m = g[g.modality == modality]
            record[f"{modality}_image_count"] = len(m)
            if len(m):
                record[f"{modality}_tcir_vmax_proxy_kt_mean"] = m["tcir_vmax_proxy_kt"].mean()
                for c in embed_cols:
                    record[f"{modality}_{c}"] = m[c].mean()
            else:
                record[f"{modality}_tcir_vmax_proxy_kt_mean"] = np.nan
                for c in embed_cols:
                    record[f"{modality}_{c}"] = np.nan

        records.append(record)

    return pd.DataFrame(records).sort_values("cyclone_id").reset_index(drop=True), embed_cols


def add_placeholder_columns(df: pd.DataFrame) -> pd.DataFrame:
    for group, spec in PLACEHOLDER_GROUPS.items():
        for col in spec["cols"]:
            df[col] = np.nan
        df[f"{group}_data_source_needed"] = spec["needed"]
    return df


def historical_basin_frequency(timestamps: pd.Series, basins: pd.Series, hist_by_year: dict) -> pd.Series:
    """Whole-year cyclone count for each event's basin, only available for
    years the 1891-2016 IMD frequency file actually covers (most matched
    storms are 2017+, so this is NaN for most rows -- that's real, not a bug)."""
    def lookup(ts, basin):
        if pd.isna(ts) or pd.isna(basin):
            return np.nan
        col = BASIN_TO_HISTORICAL_COL.get(basin)
        year_row = hist_by_year.get(ts.year)
        if col is None or year_row is None:
            return np.nan
        return year_row.get(col, np.nan)
    return pd.Series([lookup(t, b) for t, b in zip(timestamps, basins)], index=timestamps.index)


def fill_from_event_identity(df: pd.DataFrame) -> pd.DataFrame:
    """Overlays real values (from OCR + IMD best-track matching, see
    extract_reference_metadata.py) onto the placeholder columns, wherever a
    base_id has a confident identity match. Rows/cells with no match keep NaN --
    this is a partial fill, not a full unblock, and is honest about that per-row."""
    if not IDENTITY_CSV.exists():
        print(f"No {IDENTITY_CSV.name} found -- run src/data_prep/extract_reference_metadata.py first "
              f"to populate real temporal/meteorological/geographic values. Leaving placeholders as-is.")
        return df

    ident = pd.read_csv(IDENTITY_CSV, parse_dates=["ocr_date", "matched_time", "odisha_closest_approach_time"])
    ident = ident.set_index("base_id")

    df = df.set_index("cyclone_id")
    timestamp = ident["ocr_date"].fillna(ident["matched_time"])
    hours_before_landfall = (
        (ident["odisha_closest_approach_time"] - timestamp).dt.total_seconds() / 3600
    ).where(ident["is_odisha_relevant"])

    hist = pd.read_csv(HISTORICAL_FREQ_CSV)
    hist_whole_year_cols = {v: f"January - December (Whole Year): {v}" for v in BASIN_TO_HISTORICAL_COL.values()}
    hist_by_year = (
        hist.set_index("Year")[list(hist_whole_year_cols.values())]
        .rename(columns={v: k for k, v in hist_whole_year_cols.items()})
        .to_dict(orient="index")
    )

    updates = pd.DataFrame({
        "timestamp": timestamp,
        "hours_before_landfall": hours_before_landfall,
        "wind_speed_kt": ident["wind_speed_kt"],
        "pressure_hpa": ident["pressure_hpa"],
        "latitude": ident["ocr_lat"],
        "longitude": ident["ocr_lon"],
        "district": ident["district"],
        "coastal_distance_km": ident["coastal_distance_km"],
        "matched_storm_name": ident["name"],
        "matched_storm_id": ident["storm_id"],
        "matched_basin": ident["basin"],
        "is_odisha_relevant": ident["is_odisha_relevant"],
        "identity_match_time_diff_hours": ident["match_time_diff_hours"],
        "identity_match_dist_km": ident["match_dist_km"],
    })
    updates["historical_basin_frequency"] = historical_basin_frequency(timestamp, ident["basin"], hist_by_year)

    for col in ["timestamp", "hours_before_landfall", "wind_speed_kt", "pressure_hpa",
                "latitude", "longitude", "district", "coastal_distance_km",
                "historical_basin_frequency"]:
        df[col] = updates[col].reindex(df.index).combine_first(df[col])
    for col in ["matched_storm_name", "matched_storm_id", "matched_basin",
                "is_odisha_relevant", "identity_match_time_diff_hours", "identity_match_dist_km"]:
        df[col] = updates[col].reindex(df.index)

    return df.reset_index()


def fill_exposure_from_census(df: pd.DataFrame) -> pd.DataFrame:
    """Real Census 2011 exposure data (build_odisha_district_population.py),
    joined via NEAREST-district assignment for Odisha-relevant events with a
    real lat/lon fix -- most insat3d captures are pre-landfall over open
    water, so exact polygon containment (`district`) is usually null even for
    a genuine Odisha storm. `nearest_odisha_district` is named explicitly so
    it doesn't overclaim -- it's the closest district, not a claim the storm
    was administratively over it at capture time."""
    if not POPULATION_CSV.exists():
        print(f"No {POPULATION_CSV.name} found -- run "
              f"src/data_prep/build_odisha_district_population.py first for real exposure "
              f"values. Leaving exposure placeholders as-is.")
        return df

    sys.path.insert(0, str(ROOT / "src" / "data_prep"))
    from build_odisha_district_graph import load_odisha_districts

    districts = load_odisha_districts()
    pop = pd.read_csv(POPULATION_CSV).set_index("district")

    def nearest_district(lat, lon):
        p = Point(lon, lat)
        return min(districts, key=lambda d: d["geometry"].distance(p))["district"]

    def assign(row):
        if not row.get("is_odisha_relevant") or pd.isna(row.get("latitude")) or pd.isna(row.get("longitude")):
            return None
        return nearest_district(row["latitude"], row["longitude"])

    df["nearest_odisha_district"] = df.apply(assign, axis=1)
    df["district_population"] = df["district_population"].combine_first(
        df["nearest_odisha_district"].map(pop["district_population"])
    )
    for col in ["district_households", "district_literacy_rate",
                "district_worker_participation_rate", "district_urban_population_pct"]:
        df[col] = df["nearest_odisha_district"].map(pop[col])

    return df


def main():
    df, embed_cols = aggregate_cv_features()
    df = add_placeholder_columns(df)
    df = fill_from_event_identity(df)
    df = fill_exposure_from_census(df)
    df.to_csv(OUT_CSV, index=False)

    n_real_cols = 2 + 2 * (2 + 1 + len(embed_cols))  # id+split + per-modality count+proxy+embeds
    n_placeholder_cols = sum(len(s["cols"]) for s in PLACEHOLDER_GROUPS.values())

    print(f"Master dataset: {len(df)} rows (one per event/base_id)")
    print(f"  {n_real_cols} real (satellite/CV) columns")
    print(f"  {n_placeholder_cols} placeholder columns across {len(PLACEHOLDER_GROUPS)} data groups "
          f"(now partially filled per-row where an event identity was matched)")
    if "is_odisha_relevant" in df.columns:
        n_odisha = df["is_odisha_relevant"].sum()
        print(f"  {int(n_odisha)}/{len(df)} events are Odisha-relevant (storm track came within "
              f"150km) -- filter on is_odisha_relevant for Odisha-specific modeling")
    print(f"Saved: {OUT_CSV}")


if __name__ == "__main__":
    main()
