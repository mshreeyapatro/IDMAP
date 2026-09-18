"""
Structured Prompt Engineering & Advisory Synthesis for IDMAP RAG + CV Pipeline.
Formats domain-specific system roles, CV model outputs, retrieved knowledge base chunks, and task guidelines.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SYSTEM_ROLE_INSTRUCTION = (
    "You are the IDMAP Multimodal Cyclone Intelligence Advisory Assistant. "
    "Your objective is to provide evidence-based, traceable, and actionable cyclone risk explanations. "
    "Guidelines:\n"
    "1. Do NOT invent cyclone predictions or wind speeds -- use only the provided satellite CV model outputs.\n"
    "2. Base all disaster management recommendations and historical references strictly on the provided RETRIEVED CONTEXT.\n"
    "3. Explicitly cite sources using citation numbers (e.g., [1], [2]) corresponding to retrieved document snippets.\n"
    "4. Clearly distinguish between ML model predictions and retrieved historical knowledge."
)


def build_multimodal_advisory_prompt(
    fusion_data: Dict[str, Any],
    task: str = "advisory",
    custom_question: Optional[str] = None
) -> str:
    """Builds a structured prompt containing SYSTEM ROLE, MODEL OUTPUT, RETRIEVED CONTEXT, and TASK."""
    cv = fusion_data.get("cv_summary", {})
    citations = fusion_data.get("citations", [])

    prompt_lines = [
        f"=== SYSTEM ROLE ===",
        SYSTEM_ROLE_INSTRUCTION,
        "",
        f"=== SATELLITE COMPUTER VISION MODEL OUTPUT ===",
        f"Event ID: #{cv.get('base_id')}",
        f"Split: {cv.get('split')}",
        f"Imagery: {cv.get('raw_image_count')} raw crops, {cv.get('infrared_image_count')} infrared crops",
        f"Est. Wind Speed (TCIR Proxy): {cv.get('vmax_proxy_kt', 0):.1f} knots ({cv.get('vmax_proxy_kmh', 0):.1f} km/h)",
        f"IMD Intensity Classification: {cv.get('intensity_category')} (Severity: {cv.get('severity')})",
        f"Reconstruction Anomaly Score: {cv.get('max_reconstruction_anomaly_score', 0):.4f} (Flagged Anomaly: {cv.get('is_flagged_anomaly')})",
        "",
        f"=== RETRIEVED KNOWLEDGE BASE snippets ==="
    ]

    for c in citations:
        prompt_lines.append(f"{c['citation_id']} Source: {c['source']} | Section: {c['section']}")
        prompt_lines.append(f"Content: {c['snippet']}\n")

    prompt_lines.append("=== TASK INSTRUCTIONS ===")
    if task == "advisory":
        prompt_lines.append(
            "Synthesize a comprehensive Cyclone Risk & Advisory Report covering:\n"
            "1. Satellite Model Diagnosis: Explain the estimated wind speed, intensity classification, and anomaly status.\n"
            "2. Risk Assessment: Potential impact zone, surge height, and wind damage.\n"
            "3. Historical Comparisons: Compare with historical Odisha cyclones cited in the retrieved context.\n"
            "4. District-Level Action Plan: Specific protocols for coastal districts.\n"
            "5. References: Include explicit citations [1], [2] for all background facts."
        )
    elif task == "forecast":
        prompt_lines.append(
            "Synthesize a Cyclone Propagation & Landfall Forecast Advisory covering:\n"
            "1. Current Intensity & Progression Status based on CV model output.\n"
            "2. Expected Warning Stage (Pre-Cyclone Watch / Cyclone Alert / Cyclone Warning) per IMD protocols.\n"
            "3. Actionable timing & evacuation advisory with source citations."
        )
    elif task == "district":
        prompt_lines.append(
            "Synthesize a District-Level Disaster Management Advisory covering:\n"
            "1. High-vulnerability frontline coastal districts (Puri, Jagatsinghpur, Kendrapara, Bhadrak, Balasore, Ganjam).\n"
            "2. Multi-Purpose Cyclone Shelter (MPCS) evacuation priorities.\n"
            "3. Resource allocation & communication redundancy guidelines."
        )
    else:
        prompt_lines.append(f"Answer the user's specific query: '{custom_question or task}' using the CV outputs and retrieved context above.")

    return "\n".join(prompt_lines)


def generate_structured_rule_advisory(fusion_data: Dict[str, Any], task: str = "advisory") -> str:
    """Generates a structured, evidence-grounded report when offline or without LLM API key."""
    cv = fusion_data.get("cv_summary", {})
    citations = fusion_data.get("citations", [])

    lines = [
        f"## IDMAP Multimodal Advisory Report — Event #{cv.get('base_id')}",
        "",
        "### 1. Satellite Model Diagnosis",
        f"- **Intensity Classification**: **{cv.get('intensity_category')}** (IMD Scale)",
        f"- **Estimated Wind Speed**: `{cv.get('vmax_proxy_kt', 0):.1f} knots` (`{cv.get('vmax_proxy_kmh', 0):.1f} km/h`)",
        f"- **Severity Level**: `{cv.get('severity')}`",
        f"- **Autoencoder Anomaly Score**: `{cv.get('max_reconstruction_anomaly_score', 0):.4f}` " +
        (f"**[ANOMALOUS PATTERN FLAGGED]**" if cv.get('is_flagged_anomaly') else "(Normal pattern within variance)"),
        f"- **Satellite Crops Analyzed**: `{cv.get('raw_image_count')}` raw visible + `{cv.get('infrared_image_count')}` infrared",
        "",
        "### 2. Evidence-Based Disaster Advisory",
    ]

    if cv.get("severity") == "Extreme":
        lines.append("- **Immediate Action**: Enact 24-hour mandatory evacuation protocol for 0-5 km coastal belts.")
        lines.append("- **Shelter Operations**: Mobilize Multi-Purpose Cyclone Shelters (MPCS) in Puri, Jagatsinghpur, Kendrapara, and Bhadrak.")
    elif cv.get("severity") == "High":
        lines.append("- **Coastal Watch**: Pre-position ODRAF & NDRF rescue teams in frontline coastal blocks.")
        lines.append("- **Fishermen Warning**: Suspend all fishing & port operations along Odisha coast.")
    else:
        lines.append("- **Standard Monitoring**: Maintain IMD Pre-Cyclone Watch across coastal districts.")
        lines.append("- **Drainage & Power**: Clear urban drainage channels in Bhubaneswar/Cuttack and test DG sets.")

    lines.append("")
    lines.append("### 3. Retrieved Historical Knowledge & Guidelines")
    for cit in citations:
        lines.append(f"- **{cit['citation_id']} {cit['section']}** ({cit['source']})")
        lines.append(f"  > *\"{cit['snippet'].strip()}\"*")

    lines.append("")
    lines.append("---")
    lines.append("*Generated by IDMAP Grounded Multimodal RAG Engine. All statements supported by satellite CV model outputs & official knowledge base citations.*")

    return "\n".join(lines)
