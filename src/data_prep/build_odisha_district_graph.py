"""
Phase 7 prerequisite: Odisha district adjacency graph (SRS section 7, GNN spatial
propagation).

Reads the Census-2011 India district shapefile (data/raw/boundaries/
india_districts_census2011/), filters to Odisha's 30 districts, and builds a graph
where nodes are districts and edges connect districts whose boundaries touch (or are
within a small tolerance, to absorb digitization gaps). This gives the GNN layer the
graph structure it's been blocked on.

It also computes one real per-district node feature -- distance to the coast -- since
that's derivable purely from the boundary geometry we have (SRS section 7's example
master record and section 11's candidate GNN node features both list it). This is
computed as the shortest distance from each district's polygon to the Odisha coastline,
where the coastline is derived as the part of Odisha's state boundary that is NOT
shared with a neighboring Indian state (data/raw/boundaries/gadm41_india/
gadm41_IND_1.shp) -- i.e. what's left is the sea-facing edge.

Every other node feature (population, risk score, weather, elevation, infrastructure)
is a separate step that still waits on other data sources (see build_master_dataset.py's
exposure/geographic placeholder groups).

Outputs:
  - data/processed/odisha_district_graph.graphml   (networkx-native, for the GNN layer)
  - data/processed/odisha_district_nodes.csv
  - data/processed/odisha_district_edges.csv

Usage: python src/data_prep/build_odisha_district_graph.py
"""

import math
from pathlib import Path

import networkx as nx
import pandas as pd
import shapefile  # pyshp
from shapely.geometry import shape
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parents[2]
DISTRICTS_SHP = ROOT / "data" / "raw" / "boundaries" / "india_districts_census2011" / "2011_Dist.shp"
STATES_SHP = ROOT / "data" / "raw" / "boundaries" / "gadm41_india" / "gadm41_IND_1.shp"
DATA_PROCESSED = ROOT / "data" / "processed"
POPULATION_CSV = DATA_PROCESSED / "odisha_district_population.csv"

GRAPHML_OUT = DATA_PROCESSED / "odisha_district_graph.graphml"
NODES_CSV_OUT = DATA_PROCESSED / "odisha_district_nodes.csv"
EDGES_CSV_OUT = DATA_PROCESSED / "odisha_district_edges.csv"

# Degrees of slack for adjacency, to absorb small digitization gaps between
# districts that share a real-world border but don't touch exactly in the
# shapefile. ~0.01 deg is ~1.1 km at this latitude.
ADJACENCY_TOLERANCE_DEG = 0.01

# Degrees of slack for peeling neighboring-state borders off Odisha's boundary to
# leave only the coastline -- generous enough to swallow the digitization gaps
# between two independently-sourced shapefiles (Census vs. GADM).
COASTLINE_TOLERANCE_DEG = 0.03

# Local equirectangular-ish km/degree scale factors for Odisha's latitude (~20.9N),
# good enough at this regional scale without pulling in a full projection library.
KM_PER_DEG_LAT = 111.0
KM_PER_DEG_LON = 111.32 * math.cos(math.radians(20.9))


def _to_km(geom):
    return transform(lambda x, y: (x * KM_PER_DEG_LON, y * KM_PER_DEG_LAT), geom)


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_odisha_coastline():
    """The segment of Odisha's state boundary not shared with any neighboring
    Indian state -- i.e. its Bay of Bengal coastline."""
    sf = shapefile.Reader(str(STATES_SHP))
    fields = [f[0] for f in sf.fields[1:]]

    # GADM state polygons are full-resolution (dense coastline/border vertices), so
    # naively unioning all 40 states is very slow. We only need the handful of states
    # that actually border Odisha, and we don't need sub-100m vertex density for a
    # km-scale distance feature -- so filter to nearby states and simplify first.
    SIMPLIFY_TOL_DEG = 0.003  # ~300m, negligible at km-scale distances

    records = []
    for sr in sf.iterShapeRecords():
        rec = dict(zip(fields, sr.record))
        records.append((rec, sr.shape.__geo_interface__))

    odisha_raw = next(g for r, g in records if str(r.get("NAME_1", "")).strip() == "Odisha")
    odisha_geom = shape(odisha_raw)
    if not odisha_geom.is_valid:
        odisha_geom = odisha_geom.buffer(0)
    odisha_geom = odisha_geom.simplify(SIMPLIFY_TOL_DEG, preserve_topology=True)

    minx, miny, maxx, maxy = odisha_geom.bounds
    pad = 1.0  # degrees -- comfortably covers any state that could share a border
    nearby_states = []
    for rec, geo in records:
        if str(rec.get("NAME_1", "")).strip() == "Odisha":
            continue
        g = shape(geo)
        gminx, gminy, gmaxx, gmaxy = g.bounds
        if gmaxx < minx - pad or gminx > maxx + pad or gmaxy < miny - pad or gminy > maxy + pad:
            continue  # bounding box nowhere near Odisha -- skip
        if not g.is_valid:
            g = g.buffer(0)
        nearby_states.append(g.simplify(SIMPLIFY_TOL_DEG, preserve_topology=True))

    rest_of_india = unary_union(nearby_states)
    coastline = odisha_geom.boundary.difference(rest_of_india.buffer(COASTLINE_TOLERANCE_DEG))
    return coastline


def load_odisha_districts() -> list[dict]:
    sf = shapefile.Reader(str(DISTRICTS_SHP))
    fields = [f[0] for f in sf.fields[1:]]  # skip deletion flag

    districts = []
    for sr in sf.iterShapeRecords():
        rec = dict(zip(fields, sr.record))
        if str(rec.get("ST_NM", "")).strip() != "Odisha":
            continue
        geom = shape(sr.shape.__geo_interface__)
        if not geom.is_valid:
            geom = geom.buffer(0)
        centroid = geom.centroid
        districts.append({
            "district": rec["DISTRICT"],
            "censuscode": rec["censuscode"],
            "geometry": geom,
            "centroid_lon": centroid.x,
            "centroid_lat": centroid.y,
        })
    return districts


def build_graph(districts: list[dict]) -> nx.Graph:
    g = nx.Graph()
    for d in districts:
        g.add_node(
            d["district"],
            censuscode=d["censuscode"],
            centroid_lon=d["centroid_lon"],
            centroid_lat=d["centroid_lat"],
        )

    for i in range(len(districts)):
        for j in range(i + 1, len(districts)):
            a, b = districts[i], districts[j]
            if a["geometry"].distance(b["geometry"]) <= ADJACENCY_TOLERANCE_DEG:
                dist_km = haversine_km(
                    a["centroid_lon"], a["centroid_lat"], b["centroid_lon"], b["centroid_lat"]
                )
                g.add_edge(a["district"], b["district"], centroid_distance_km=round(dist_km, 2))
    return g


def main():
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    districts = load_odisha_districts()
    print(f"Loaded {len(districts)} Odisha districts from {DISTRICTS_SHP.name}")

    coastline = load_odisha_coastline()
    coastline_km = _to_km(coastline)
    for d in districts:
        d["coastal_distance_km"] = round(_to_km(d["geometry"]).distance(coastline_km), 2)
    n_coastal = sum(1 for d in districts if d["coastal_distance_km"] == 0.0)
    print(f"Computed coastal distance for {len(districts)} districts ({n_coastal} touching the coast, 0.0 km)")

    g = build_graph(districts)
    for d in districts:
        g.nodes[d["district"]]["coastal_distance_km"] = d["coastal_distance_km"]

    isolated = list(nx.isolates(g))
    degrees = dict(g.degree())
    print(f"Graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    print(f"Average degree: {sum(degrees.values()) / len(degrees):.2f}")
    if isolated:
        print(f"WARNING: {len(isolated)} isolated district(s) with no detected neighbor: {isolated}")
    else:
        print("No isolated districts.")

    nx.write_graphml(g, GRAPHML_OUT)

    nodes_df = pd.DataFrame([
        {
            "district": n,
            "censuscode": attrs["censuscode"],
            "centroid_lon": attrs["centroid_lon"],
            "centroid_lat": attrs["centroid_lat"],
            "coastal_distance_km": attrs["coastal_distance_km"],
            "degree": degrees[n],
        }
        for n, attrs in g.nodes(data=True)
    ]).sort_values("district")

    # Real population exposure (SRS section 11 candidate node feature), from
    # Census 2011 -- see build_odisha_district_population.py. Soft dependency:
    # merge if that script has already been run, skip gracefully otherwise
    # (this script's own job is geometry, not census data).
    if POPULATION_CSV.exists():
        pop = pd.read_csv(POPULATION_CSV).drop(columns=["district"])
        nodes_df = nodes_df.merge(pop, on="censuscode", how="left")
        print(f"Merged real population/exposure data from {POPULATION_CSV.name}")
    else:
        print(f"{POPULATION_CSV.name} not found -- run build_odisha_district_population.py "
              f"first for real population node features. Skipping for now.")

    nodes_df.to_csv(NODES_CSV_OUT, index=False)

    edges_df = pd.DataFrame([
        {"district_a": u, "district_b": v, "centroid_distance_km": attrs["centroid_distance_km"]}
        for u, v, attrs in g.edges(data=True)
    ]).sort_values(["district_a", "district_b"])
    edges_df.to_csv(EDGES_CSV_OUT, index=False)

    print(f"Wrote {GRAPHML_OUT.relative_to(ROOT)}")
    print(f"Wrote {NODES_CSV_OUT.relative_to(ROOT)}")
    print(f"Wrote {EDGES_CSV_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
