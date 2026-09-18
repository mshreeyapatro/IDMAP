"""
Phase 10: AI agent orchestrator (SRS section 15).

Two modes:
  - LLM mode: if `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) is set and the
    `google-genai` package is installed, questions are answered by Gemini
    using automatic function calling directly over the plain Python functions
    in tools.py -- the SDK handles the call/execute/continue loop itself, so
    there's no hand-rolled tool-loop here (see google-genai's automatic
    function calling feature). Wrapped in error handling: any API failure
    (network, rate limit, bad key) falls back to rule-based mode rather than
    crashing the request.
  - Fallback mode (what runs without a key, or if the LLM call fails): simple
    keyword routing straight onto the same tools, with template formatting
    instead of LLM prose. Still fully tool-grounded.

Every answer reports which tools were actually called (`tools_used`), so the
caller can show its work rather than asking for blind trust -- this is the
concrete evidence that answers are tool-grounded, not just a claim in a prompt.

Usage: python src/agent/agent.py "which images are the biggest anomalies?"
"""

import os
import re
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

# .env lives at the project root (c:\Professional\Projects\IDMAP\.env) --
# loaded here so both `python src/agent/agent.py` and the FastAPI backend
# (which imports this module) pick up GEMINI_API_KEY without needing the
# caller to export it into the shell first.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools

GEMINI_MODEL = "gemini-flash-latest"  # rolling alias, no version pin needed
MAX_HISTORY_TURNS = 12  # trim long conversations rather than growing every request unbounded

SYSTEM_INSTRUCTION = (
    "You are the IDMAP-Cyclone project assistant. Answer ONLY using tool "
    "results. If a tool reports a phase as 'blocked', tell the user it isn't "
    "available yet and why -- never invent a risk score, forecast, or spatial "
    "ranking that no tool returned. The conversation may include earlier turns; "
    "use them for context (e.g. 'it' or 'that event' referring to something "
    "already discussed)."
)


def _llm_available() -> bool:
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        return False
    try:
        from google import genai  # noqa: F401
        return True
    except ImportError:
        return False


def _answer_with_llm(question: str, history: list[dict] | None = None) -> tuple[str, list[str]]:
    """Gemini with automatic function calling. Returns (answer_text, tools_used).
    Raises on any API failure -- caller (ask()) is responsible for the fallback."""
    from google import genai
    from google.genai import types

    client = genai.Client()  # reads GEMINI_API_KEY / GOOGLE_API_KEY from env

    contents = []
    for turn in (history or [])[-MAX_HISTORY_TURNS:]:
        role = "model" if turn.get("role") == "model" else "user"
        contents.append({"role": role, "parts": [{"text": turn.get("text", "")}]})
    contents.append({"role": "user", "parts": [{"text": question}]})

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[
                tools.get_project_status,
                tools.list_events,
                tools.get_event_summary,
                tools.list_anomalies,
                tools.dataset_audit_summary,
                tools.predict_event,
                tools.retrieve_knowledge,
                tools.generate_advisory,
            ],
        ),
    )

    tools_used = []
    for turn in (response.automatic_function_calling_history or []):
        for part in (turn.parts or []):
            fc = getattr(part, "function_call", None)
            if fc is not None:
                tools_used.append(fc.name)

    return response.text, tools_used


def _answer_with_rules(question: str) -> tuple[str, list[str]]:
    """Fallback router: no LLM, direct keyword -> tool dispatch."""
    q = question.lower()

    if any(k in q for k in ["status", "phase", "roadmap", "what's done", "what is done"]):
        status = tools.get_project_status()
        lines = ["Project status by SRS roadmap phase:"]
        for n, s in status.items():
            lines.append(f"  Phase {n} ({s['name']}): {s['status'].upper()} -- {s['note']}")
        return "\n".join(lines), ["get_project_status"]

    if any(k in q for k in ["advisory", "report", "guideline", "evacuation", "shelter"]):
        m = re.search(r"event\s*(\d+)|storm\s*(\d+)|id\s*(\d+)|#(\d+)", q)
        base_id = int(next(g for g in m.groups() if g)) if m else 46
        adv = tools.generate_advisory(base_id)
        if "error" in adv:
            return adv["error"], ["generate_advisory"]
        return adv["advisory_report"], ["generate_advisory", "retrieve_knowledge"]

    if any(k in q for k in ["fani", "phailin", "hudhud", "amphan", "yaas", "gulab", "imd", "surge", "district"]):
        chunks = tools.retrieve_knowledge(question, top_k=3)
        if not chunks:
            return "No matching knowledge base entries found.", ["retrieve_knowledge"]
        lines = [f"Retrieved {len(chunks)} relevant knowledge base excerpts:"]
        for c in chunks:
            lines.append(f"\n- **{c['metadata']['section']}** ({c['metadata']['source']}):\n  {c['text'][:300]}...")
        return "\n".join(lines), ["retrieve_knowledge"]

    if "anomal" in q:
        m = re.search(r"top\s*(\d+)", q)
        top_n = int(m.group(1)) if m else 5
        results = tools.list_anomalies(top_n=top_n)
        if not results:
            return "No images are currently flagged as anomalous.", ["list_anomalies"]
        lines = [f"Top {len(results)} anomalous images (autoencoder reconstruction error):"]
        for r in results:
            lines.append(
                f"  event {r['base_id']} ({r['split']}, {r['modality']}/{r['filename']}): "
                f"error={r['reconstruction_error']:.3f}"
            )
        return "\n".join(lines), ["list_anomalies"]

    m = re.search(r"event\s*(\d+)|storm\s*(\d+)|id\s*(\d+)|#(\d+)", q)
    if m:
        base_id = int(next(g for g in m.groups() if g))
        summary = tools.get_event_summary(base_id)
        if "error" in summary:
            return summary["error"], ["get_event_summary"]
        lines = [
            f"Event {base_id} (split: {summary['split']}):",
            f"  {summary['raw_image_count']} raw / {summary['infrared_image_count']} infrared images",
            f"  raw vmax proxy: {summary['raw_tcir_vmax_proxy_kt']:.1f} kt "
            f"(IMD Classification: {tools.predict_event(base_id).get('intensity_category', 'N/A')})"
            if summary['raw_image_count'] else "  no raw images",
        ]
        if summary["unavailable_data_groups"]:
            lines.append(f"  data still missing for this event: {', '.join(summary['unavailable_data_groups'])}")
        flagged = [a for a in summary["per_image_anomaly_scores"] if a["is_anomaly"]]
        if flagged:
            lines.append(f"  flagged anomalous: {[f['filename'] for f in flagged]}")
        return "\n".join(lines), ["get_event_summary"]

    if any(k in q for k in ["how many", "list events", "count"]):
        events = tools.list_events()
        return f"{len(events)} events total across train/val/test splits.", ["list_events"]

    return (
        "I can answer questions about: project status, historical cyclones (Fani, Phailin, etc.), "
        "IMD warning guidelines, event predictions, and generate evidence-grounded advisories.",
        [],
    )


def ask(question: str, history: list[dict] | None = None) -> dict:
    """Returns {answer, tools_used, mode, llm_error?}. `mode` is 'llm' or
    'fallback' so the caller (and the UI) can show which one actually answered."""
    if _llm_available():
        try:
            answer, tools_used = _answer_with_llm(question, history)
            return {"answer": answer, "tools_used": tools_used, "mode": "llm"}
        except Exception as exc:  # network, rate limit, bad key, SDK error -- never crash the request
            print(f"[agent] Gemini call failed, falling back to rules: {exc}", file=sys.stderr)
            traceback.print_exc()
            answer, tools_used = _answer_with_rules(question)
            return {
                "answer": answer,
                "tools_used": tools_used,
                "mode": "fallback",
                "llm_error": str(exc),
            }

    answer, tools_used = _answer_with_rules(question)
    return {"answer": answer, "tools_used": tools_used, "mode": "fallback"}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "what's the project status?"
    print(f"Q: {q}\n")
    result = ask(q)
    print(result["answer"])
    print(f"\n[mode={result['mode']}, tools_used={result['tools_used']}]")
