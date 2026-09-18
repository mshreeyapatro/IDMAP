"""
Phase 10: AI agent tools (SRS section 15).

Each function here is a "tool": it returns only facts read from files this
project has actually produced (Phases 1-4, 6). Nothing here is invented or
model-generated text -- that's the whole point of a tool-grounded agent per
the SRS ("use tools to retrieve factual outputs rather than inventing values").

If a phase is blocked (XGBoost risk, GNN spatial, resource optimization -- see
chat), there is deliberately no tool for it: the agent must be able to say
"that isn't available yet" rather than a tool silently returning nothing useful.
"""

import sys
from pathlib import Path
from functools import lru_cache

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CV_FEATURES_CSV = ROOT / "data" / "processed" / "insat3d_cv_features.csv"
ANOMALY_CSV = ROOT / "data" / "processed" / "insat3d_anomaly_scores.csv"
MASTER_CSV = ROOT / "data" / "processed" / "master_cyclone_dataset.csv"
AUDIT_REPORT_MD = ROOT / "docs" / "dataset_audit_report.md"
DISTRICT_NODES_CSV = ROOT / "data" / "processed" / "odisha_district_nodes.csv"
DISTRICT_EDGES_CSV = ROOT / "data" / "processed" / "odisha_district_edges.csv"

PLACEHOLDER_GROUP_COLS = {
    "temporal": ["timestamp", "hours_before_landfall"],
    "meteorological": ["wind_speed_kt", "pressure_hpa", "rainfall_mm", "temperature_c"],
    "geographic": ["latitude", "longitude", "district", "coastal_distance_km", "elevation_m"],
    "exposure": ["district_population", "infrastructure_index"],
    "historical": ["historical_basin_frequency", "historical_landfall_rate"],
}

PROJECT_STATUS = {
    1: {"name": "Dataset study", "status": "done", "note": "audit report + inventory produced"},
    2: {"name": "Data preparation", "status": "done", "note": "leakage-safe (image-group) splits, cleaned images"},
    3: {"name": "CV model development", "status": "done", "note": "TCIR-pretrained backbone + insat3d embeddings"},
    4: {"name": "Feature fusion", "status": "done", "note": "Multimodal satellite/temporal/geographic/IMD classification fusion complete"},
    5: {"name": "Current risk (XGBoost)", "status": "done", "note": "CV + RAG ground-truth risk proxy and intensity categorization"},
    6: {"name": "Anomaly detection (Autoencoder)", "status": "done", "note": "unsupervised cross-sectional reconstruction error flagged"},
    7: {"name": "Spatial propagation (GNN)", "status": "done", "note": "30-district adjacency graph built with coastal-distance + Census 2011 population node features"},
    8: {"name": "Explainability (SHAP)", "status": "done", "note": "Autoencoder feature contribution & citation trace explanation"},
    9: {"name": "What-if / resource optimization", "status": "done", "note": "Census 2011 + Multi-Purpose Cyclone Shelter evacuation guidelines"},
    10: {"name": "AI agent", "status": "done", "note": "Multimodal RAG knowledge base + LLM advisory pipeline active"},
    11: {"name": "Production Dashboard & Live Survey Engine", "status": "done", "note": "Unified 5-Model Live Survey, Real-Time SHAP, NASA GIBS Satellite, and Formatted PDF Export"},
}


@lru_cache(maxsize=1)
def _cv_features() -> pd.DataFrame:
    return pd.read_csv(CV_FEATURES_CSV)


@lru_cache(maxsize=1)
def _anomalies() -> pd.DataFrame:
    return pd.read_csv(ANOMALY_CSV)


@lru_cache(maxsize=1)
def _master() -> pd.DataFrame:
    return pd.read_csv(MASTER_CSV)


def image_url(modality: str, split: str, base_id: int, filename: str) -> str:
    """Relative URL for a processed insat3d image, served by backend/main.py's
    /static/insat3d mount. Frontend prefixes this with the API host."""
    return f"/static/insat3d/{modality}/{split}/{base_id}/{filename}"


def get_project_status() -> dict:
    """Tool: report which SRS roadmap phases are done / partial / blocked and why."""
    return PROJECT_STATUS


def _clean(v):
    """NaN/NaT -> None so JSON serialization doesn't emit invalid `NaN` literals."""
    return None if pd.isna(v) else v


def list_events(split: str | None = None) -> list[dict]:
    """Tool: list every cyclone event (image-group) with its split, image counts,
    a thumbnail URL (first available raw image, else first infrared), and --
    where extract_reference_metadata.py found a match -- the real storm identity,
    date, and whether it's an Odisha-relevant storm."""
    df = _master()
    if split:
        df = df[df["split"] == split]
    feats = _cv_features()

    records = []
    for _, row in df.iterrows():
        base_id = int(row["cyclone_id"])
        ev_split = row["split"]
        thumb = None
        for modality in ["raw", "infrared"]:
            m = feats[(feats.base_id == base_id) & (feats.modality == modality)]
            if not m.empty:
                thumb = image_url(modality, ev_split, base_id, m.iloc[0]["filename"])
                break
        records.append({
            "cyclone_id": base_id,
            "split": ev_split,
            "raw_image_count": int(row["raw_image_count"]),
            "infrared_image_count": int(row["infrared_image_count"]),
            "thumbnail_url": thumb,
            "matched_storm_name": _clean(row.get("matched_storm_name")),
            "timestamp": _clean(row.get("timestamp")),
            "wind_speed_kt": _clean(row.get("wind_speed_kt")),
            "is_odisha_relevant": _clean(row.get("is_odisha_relevant")),
        })
    return records


def get_event_summary(base_id: int) -> dict:
    """Tool: full known summary for one event -- CV features, anomaly flags, image
    URLs, and which fusion data groups are still placeholders for it."""
    master_row = _master()[_master()["cyclone_id"] == base_id]
    if master_row.empty:
        return {"error": f"no event with base_id={base_id}"}
    master_row = master_row.iloc[0].to_dict()
    split = master_row["split"]

    anomaly_rows = _anomalies()[_anomalies()["base_id"] == base_id]
    anomalies = anomaly_rows[["modality", "filename", "reconstruction_error", "is_anomaly"]].to_dict(orient="records")
    for a in anomalies:
        a["url"] = image_url(a["modality"], split, base_id, a["filename"])

    images = _cv_features()[_cv_features().base_id == base_id][["modality", "filename"]].to_dict(orient="records")
    for im in images:
        im["url"] = image_url(im["modality"], split, base_id, im["filename"])

    # A group counts as unavailable only if EVERY one of its columns is still NaN
    # for this specific event -- some groups (temporal/meteorological/geographic)
    # are now partially filled per-row by extract_reference_metadata.py's identity
    # match, so this can no longer be a fixed all-placeholder list.
    unavailable_groups = [
        g for g, cols in PLACEHOLDER_GROUP_COLS.items()
        if all(pd.isna(master_row.get(c)) for c in cols)
    ]

    return {
        "base_id": base_id,
        "split": split,
        "raw_image_count": master_row["raw_image_count"],
        "infrared_image_count": master_row["infrared_image_count"],
        "raw_tcir_vmax_proxy_kt": master_row.get("raw_tcir_vmax_proxy_kt_mean"),
        "infrared_tcir_vmax_proxy_kt": master_row.get("infrared_tcir_vmax_proxy_kt_mean"),
        "images": images,
        "per_image_anomaly_scores": anomalies,
        "unavailable_data_groups": unavailable_groups,
        "matched_storm_name": _clean(master_row.get("matched_storm_name")),
        "matched_storm_id": _clean(master_row.get("matched_storm_id")),
        "matched_basin": _clean(master_row.get("matched_basin")),
        "is_odisha_relevant": _clean(master_row.get("is_odisha_relevant")),
        "timestamp": _clean(master_row.get("timestamp")),
        "hours_before_landfall": _clean(master_row.get("hours_before_landfall")),
        "wind_speed_kt": _clean(master_row.get("wind_speed_kt")),
        "pressure_hpa": _clean(master_row.get("pressure_hpa")),
        "latitude": _clean(master_row.get("latitude")),
        "longitude": _clean(master_row.get("longitude")),
        "coastal_distance_km": _clean(master_row.get("coastal_distance_km")),
        "identity_match_time_diff_hours": _clean(master_row.get("identity_match_time_diff_hours")),
        "identity_match_dist_km": _clean(master_row.get("identity_match_dist_km")),
        "nearest_odisha_district": _clean(master_row.get("nearest_odisha_district")),
        "district_population": _clean(master_row.get("district_population")),
        "district_literacy_rate": _clean(master_row.get("district_literacy_rate")),
        "district_urban_population_pct": _clean(master_row.get("district_urban_population_pct")),
    }


def list_anomalies(top_n: int = 5, only_flagged: bool = True) -> list[dict]:
    """Tool: most anomalous images by autoencoder reconstruction error, with image URLs."""
    df = _anomalies().sort_values("reconstruction_error", ascending=False)
    if only_flagged:
        df = df[df["is_anomaly"]]
    records = df.head(top_n)[["base_id", "split", "modality", "filename", "reconstruction_error"]].to_dict(orient="records")
    for r in records:
        r["url"] = image_url(r["modality"], r["split"], r["base_id"], r["filename"])
    return records


def dataset_audit_summary() -> str:
    """Tool: raw text of the Phase 1 dataset audit report, for questions about
    data quality, dataset scope, or known open issues."""
    if not AUDIT_REPORT_MD.exists():
        return "Audit report not found."
    return AUDIT_REPORT_MD.read_text(encoding="utf-8")


def get_district_graph(district: str | None = None) -> dict:
    """Tool: the Odisha district adjacency graph (Phase 7 prerequisite). With no
    argument, returns every node and edge. With `district`, returns that district's
    direct neighbors and their centroid distances."""
    if not DISTRICT_NODES_CSV.exists() or not DISTRICT_EDGES_CSV.exists():
        return {"error": "district graph not found -- run src/data_prep/build_odisha_district_graph.py"}

    nodes = pd.read_csv(DISTRICT_NODES_CSV)
    edges = pd.read_csv(DISTRICT_EDGES_CSV)

    if district is None:
        return {
            "nodes": nodes.to_dict(orient="records"),
            "edges": edges.to_dict(orient="records"),
        }

    if district not in nodes["district"].values:
        return {"error": f"no district named {district!r} in the graph"}

    neighbor_edges = edges[(edges.district_a == district) | (edges.district_b == district)]
    neighbors = [
        {
            "district": row.district_b if row.district_a == district else row.district_a,
            "centroid_distance_km": row.centroid_distance_km,
        }
        for row in neighbor_edges.itertuples()
    ]
    return {"district": district, "neighbors": neighbors}


def predict_event(base_id: int) -> dict:
    """Tool: runs CV model prediction & anomaly analysis for a given event ID."""
    from src.rag import fusion_context
    fusion = fusion_context.get_cv_rag_fusion_context(base_id)
    if "error" in fusion:
        return {"error": fusion["error"]}
    return fusion["cv_summary"]


def retrieve_knowledge(query: str, top_k: int = 4) -> list:
    """Tool: semantic vector search over the Odisha cyclone knowledge base."""
    from src.rag.vector_store import get_vector_store
    store = get_vector_store()
    return store.search(query, top_k=top_k)


def generate_advisory(base_id: int, task: str = "advisory") -> dict:
    """Tool: fuses satellite CV model predictions with retrieved knowledge base context to produce evidence-grounded advisory."""
    from src.rag import fusion_context, prompts
    fusion = fusion_context.get_cv_rag_fusion_context(base_id)
    if "error" in fusion:
        return {"error": fusion["error"]}
    
    report_text = prompts.generate_structured_rule_advisory(fusion, task=task)
    return {
        "event_id": base_id,
        "cv_summary": fusion["cv_summary"],
        "citations": fusion["citations"],
        "advisory_report": report_text,
    }


def explain_risk_prediction(base_id: int) -> dict:
    """Tool: SHAP feature contribution analysis explaining why a cyclone event received its risk rating."""
    from src.layer2.risk_xgboost import explainability
    return explainability.explain_event(base_id)


def explain_live_risk_prediction(
    wind_speed_kt: float = 65.0,
    coastal_distance_km: float = 85.0,
    district_population: float = 1250000.0,
    pressure_hpa: float = 998.0,
    anomaly_error: float = 0.08
) -> dict:
    """Tool: SHAP feature contribution analysis explaining real-time live telemetry or simulated forecast predictions."""
    from src.layer2.risk_xgboost import explainability
    return explainability.explain_custom_features(
        wind_speed_kt=wind_speed_kt,
        coastal_distance_km=coastal_distance_km,
        district_population=district_population,
        pressure_hpa=pressure_hpa,
        anomaly_error=anomaly_error
    )



def simulate_whatif_scenario(base_id: int, delta_wind_speed_kt: float = 0.0, new_coastal_distance_km: float | None = None) -> dict:
    """Tool: simulates dynamic parameter shifts (wind speed, coastal distance) and computes risk impact."""
    from src.agent import whatif_engine
    return whatif_engine.simulate_whatif(base_id, delta_wind_speed_kt=delta_wind_speed_kt, new_coastal_distance_km=new_coastal_distance_km)


def get_resource_plan(district_name: str | None = None, severity_level: str = "High") -> dict:
    """Tool: emergency evacuation allocations and shelter requirements for Odisha districts."""
    from src.agent import resource_planner
    return resource_planner.get_resource_plan(district_name=district_name, severity_level=severity_level)


def get_live_weather_feed() -> dict:
    """Tool: real-time meteorological feed across 6 Odisha coastal stations via Open-Meteo API."""
    from src.ingestion import live_weather
    return live_weather.get_live_weather_feed()


def get_live_satellite_feed() -> dict:
    """Tool: live satellite imagery layer metadata & tile URLs via NASA GIBS / MOSDAC."""
    from src.ingestion import live_satellite
    return live_satellite.get_live_satellite_feed()


def generate_live_advisory() -> dict:
    """Tool: generates real-time evidence-grounded AI advisory fusing live Open-Meteo metrics with RAG knowledge base retrieval."""
    from src.ingestion import live_weather
    from src.rag.vector_store import get_vector_store

    weather = live_weather.get_live_weather_feed()
    max_wind = weather.get("max_coastal_wind_speed_kt", 15.0)
    severity = weather.get("overall_state_severity", "Normal")

    # Semantic RAG retrieval based on active live weather severity
    store = get_vector_store()
    query = f"Odisha cyclone disaster management evacuation guidelines for {severity} wind speed {max_wind} kt"
    citations = store.search(query, top_k=3)

    report_lines = [
        f"# LIVE ODISHA CYCLONE ADVISORY REPORT",
        f"**Source**: Open-Meteo Live API & IMD RAG Knowledge Base",
        f"**Overall State Severity**: {severity}",
        f"**Peak Coastal Wind Speed**: {max_wind} kt",
        f"**Minimum Coastal Surface Pressure**: {weather.get('min_coastal_pressure_hpa')} hPa",
        f"",
        f"### Station Summary",
    ]

    for st in weather.get("stations", []):
        name = st.get("station")
        w_kt = st.get("wind_speed_kt")
        p_hpa = st.get("surface_pressure_hpa")
        st_sev = st.get("severity_status")
        report_lines.append(f"- **{name}** ({st.get('type')}): {w_kt} kt wind, {p_hpa} hPa pressure — *{st_sev}*")

    report_lines.extend([
        "",
        "### Evidence-Grounded RAG Knowledge Base Citations",
    ])

    for c in citations:
        source = c.get("metadata", {}).get("source", "IMD Document")
        text = c.get("text", "")[:200]
        report_lines.append(f"> **[{source}]**: {text}...")

    report_lines.extend([
        "",
        "### Actionable Recommendations",
        f"- Maintain active monitoring across coastal stations (Puri, Paradip, Gopalpur, Balasore, Chandbali).",
        f"- Evacuation shelters are on standby if coastal wind speeds exceed 34 kt.",
    ])

    return {
        "fetched_at": weather.get("fetched_at"),
        "live_weather": weather,
        "citations": citations,
        "advisory_report": "\n".join(report_lines)
    }


TOOL_REGISTRY = {
    "get_project_status": get_project_status,
    "list_events": list_events,
    "get_event_summary": get_event_summary,
    "list_anomalies": list_anomalies,
    "dataset_audit_summary": dataset_audit_summary,
    "get_district_graph": get_district_graph,
    "predict_event": predict_event,
    "retrieve_knowledge": retrieve_knowledge,
    "generate_advisory": generate_advisory,
    "explain_risk_prediction": explain_risk_prediction,
    "simulate_whatif_scenario": simulate_whatif_scenario,
    "get_resource_plan": get_resource_plan,
    "get_live_weather_feed": get_live_weather_feed,
    "get_live_satellite_feed": get_live_satellite_feed,
    "generate_live_advisory": generate_live_advisory,
}
