"""
CV + RAG Context Fusion Engine for IDMAP.
Bridges Computer Vision model outputs (satellite features, TCIR intensity proxy, autoencoder anomaly scores)
with document vector search context to generate unified multimodal context for LLM explanations & advisories.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent import tools as agent_tools
from src.rag.vector_store import get_vector_store


def classify_intensity_category(vmax_kt: float) -> Dict[str, str]:
    """Classifies wind speed in knots to IMD storm categories."""
    if vmax_kt < 17:
        return {"category": "Low Pressure Area", "short": "LPA", "severity": "Low"}
    elif vmax_kt < 28:
        return {"category": "Depression", "short": "D", "severity": "Low"}
    elif vmax_kt < 34:
        return {"category": "Deep Depression", "short": "DD", "severity": "Moderate"}
    elif vmax_kt < 48:
        return {"category": "Cyclonic Storm", "short": "CS", "severity": "Moderate"}
    elif vmax_kt < 64:
        return {"category": "Severe Cyclonic Storm", "short": "SCS", "severity": "High"}
    elif vmax_kt < 90:
        return {"category": "Very Severe Cyclonic Storm", "short": "VSCS", "severity": "High"}
    elif vmax_kt < 120:
        return {"category": "Extremely Severe Cyclonic Storm", "short": "ESCS", "severity": "Extreme"}
    else:
        return {"category": "Super Cyclonic Storm", "short": "SuCS", "severity": "Extreme"}


def get_cv_rag_fusion_context(base_id: int, user_query: Optional[str] = None) -> Dict[str, Any]:
    """Fuses satellite CV outputs for a given event ID with RAG semantic search."""
    event_summary = agent_tools.get_event_summary(base_id)
    if "error" in event_summary:
        return {"error": f"Event {base_id} not found."}

    # Extract CV features
    raw_vmax = event_summary.get("raw_tcir_vmax_proxy_kt", 0.0) or 0.0
    cat_info = classify_intensity_category(raw_vmax)
    anomaly_scores = event_summary.get("per_image_anomaly_scores", [])
    max_anomaly = max([a["reconstruction_error"] for a in anomaly_scores], default=0.0)
    flagged_anomalies = [a for a in anomaly_scores if a.get("is_anomaly")]

    # Build semantic search query combining CV output + user query
    query_parts = [
        cat_info["category"],
        f"wind speed {raw_vmax:.1f} knots",
        "Odisha evacuation disaster management guidelines district advisory"
    ]
    if user_query:
        query_parts.append(user_query)

    search_query = " ".join(query_parts)

    # Perform RAG retrieval
    vector_store = get_vector_store()
    retrieved_chunks = vector_store.search(search_query, top_k=4)

    # Format citations
    citations = []
    for idx, c in enumerate(retrieved_chunks, 1):
        citations.append({
            "citation_id": f"[{idx}]",
            "source": c["metadata"].get("source", "Knowledge Base"),
            "section": c["metadata"].get("section", "General"),
            "score": c["score"],
            "snippet": c["text"][:200] + "..."
        })

    # Construct unified context representation
    cv_summary = {
        "base_id": base_id,
        "split": event_summary.get("split"),
        "raw_image_count": event_summary.get("raw_image_count", 0),
        "infrared_image_count": event_summary.get("infrared_image_count", 0),
        "vmax_proxy_kt": raw_vmax,
        "vmax_proxy_kmh": raw_vmax * 1.852,
        "intensity_category": cat_info["category"],
        "severity": cat_info["severity"],
        "max_reconstruction_anomaly_score": max_anomaly,
        "is_flagged_anomaly": len(flagged_anomalies) > 0,
    }

    # Format structured context text for LLM prompt
    context_lines = [
        f"=== SATELLITE CV MODEL OUTPUT (Event #{base_id}) ===",
        f"- Dataset Split: {cv_summary['split']}",
        f"- Imagery Count: {cv_summary['raw_image_count']} raw crops, {cv_summary['infrared_image_count']} infrared crops",
        f"- Est. Max Wind Speed (TCIR Proxy): {cv_summary['vmax_proxy_kt']:.1f} knots ({cv_summary['vmax_proxy_kmh']:.1f} km/h)",
        f"- IMD Intensity Classification: {cv_summary['intensity_category']} (Severity: {cv_summary['severity']})",
        f"- Autoencoder Reconstruction Anomaly Score: {max_anomaly:.4f} (Flagged Anomaly: {cv_summary['is_flagged_anomaly']})",
        "",
        "=== RETRIEVED KNOWLEDGE BASE CONTEXT & CITATIONS ==="
    ]
    for cit in citations:
        context_lines.append(f"{cit['citation_id']} Source: {cit['source']} | Section: {cit['section']}")
        context_lines.append(f"    Excerpt: {cit['snippet']}")

    return {
        "cv_summary": cv_summary,
        "retrieved_chunks": retrieved_chunks,
        "citations": citations,
        "structured_context_str": "\n".join(context_lines),
    }


if __name__ == "__main__":
    fusion = get_cv_rag_fusion_context(46, user_query="What districts are most vulnerable?")
    if "error" in fusion:
        print("Error:", fusion["error"])
    else:
        print(fusion["structured_context_str"])
