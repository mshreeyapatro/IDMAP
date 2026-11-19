"""Bridge assistant questions to IDMAP's existing tools and live data."""
import re
from . import live


def get_live_facts(question: str) -> tuple[str, list[str], bool]:
    parts, used, ok = [], [], False

    text, w_ok = live.weather_for_question(question)
    if text:
        parts.append(text)
        if w_ok:
            used.append("open_meteo_weather")
            ok = True

    q = question.lower()
    try:
        from src.agent import tools

        if any(term in q for term in ("project status", "project roadmap", "which phases", "phase status")):
            status = tools.get_project_status()
            lines = ["IDMAP PROJECT STATUS:"]
            lines.extend(
                f"Phase {number} ({item['name']}): {item['status']} — {item['note']}"
                for number, item in status.items()
            )
            parts.append("\n".join(lines))
            used.append("get_project_status")
            ok = True

        if "anomal" in q:
            match = re.search(r"top\s+(\d+)", q)
            anomalies = tools.list_anomalies(top_n=int(match.group(1)) if match else 5)
            parts.append("IDMAP ANOMALIES:\n" + (str(anomalies) if anomalies else "No flagged anomalies returned."))
            used.append("list_anomalies")
            ok = True

        event_match = re.search(r"\b(?:event|storm|id)\s*#?\s*(\d+)\b", q)
        if event_match:
            event = tools.get_event_summary(int(event_match.group(1)))
            parts.append("IDMAP EVENT DATA:\n" + str(event))
            used.append("get_event_summary")
            ok = True

        if any(term in q for term in ("how many events", "event count", "list events")):
            events = tools.list_events()
            parts.append(f"IDMAP DATASET: {len(events)} event records are available.")
            used.append("list_events")
            ok = True
    except Exception as exc:
        parts.append(f"IDMAP tools could not be reached ({str(exc)[:120]}).")

    return "\n\n".join(parts), used, ok
