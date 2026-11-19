"""Free web search (no API key, no billing): Google News RSS for headlines + Wikipedia for background.

Gemini then writes the answer from these results, so you do not need Gemini's paid Google Search grounding.
Results are headlines and short summaries, not full articles.
"""
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

UA = "IDMAP-Assistant/1.0 (student project, PMEC Berhampur)"
FILLER = re.compile(r"\b(tell me|about|please|using gemini|with gemini|can you|could you|what is|what are|what was|"
                    r"who is|give me|explain|the|me|updates?)\b", re.I)
LAST_ERROR = ""


def _get(url: str, timeout: int = 8) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def clean_query(q: str) -> str:
    c = re.sub(r"\s+", " ", FILLER.sub(" ", q)).strip(" ?.!,")
    return (c or q.strip())[:120]


def news(query: str, n: int = 6) -> list[dict]:
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
    root = ET.fromstring(_get(url))
    out, seen = [], set()
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        key = title.lower()
        if not title or key in seen:
            continue
        seen.add(key)
        try:
            date = parsedate_to_datetime(it.findtext("pubDate") or "").strftime("%d %b %Y")
        except Exception:
            date = ""
        src = it.find("source")
        out.append({"title": title, "source": (src.text if src is not None else "") or "",
                    "date": date, "url": (it.findtext("link") or "").strip()})
        if len(out) >= n:
            break
    return out


def wiki(query: str, n: int = 2) -> list[dict]:
    params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": query, "gsrlimit": n,
              "prop": "extracts", "exintro": 1, "explaintext": 1, "exsentences": 5, "redirects": 1}
    data = json.loads(_get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)))
    pages = sorted(((data.get("query") or {}).get("pages") or {}).values(), key=lambda p: p.get("index", 99))
    words = [w for w in re.findall(r"[a-z0-9]{4,}", query.lower())]
    topics = [t for t in ("cyclone", "storm", "typhoon", "hurricane", "flood", "earthquake", "tsunami") if t in query.lower()]
    out = []
    for p in pages:
        title, ext = p.get("title", ""), (p.get("extract") or "").strip()
        if not ext or not any(w in title.lower() for w in words):  # drop unrelated pages
            continue
        if topics and not any(t in (title + " " + ext).lower() for t in topics):  # e.g. a journalist named Arnab
            continue
        if True:
            out.append({"title": title, "extract": ext[:700],
                        "url": "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")})
    return out


def search(question: str, recent: bool = False) -> tuple[str, list[dict]]:
    """Returns (text for the prompt, sources for the UI). ('', []) if nothing could be fetched."""
    global LAST_ERROR
    LAST_ERROR = ""
    q = clean_query(question)
    items, pages = [], []
    try:
        items = news(q + " when:30d", 6) if recent else []
        if not items:
            items = news(q, 6)
    except Exception as e:
        LAST_ERROR = f"news: {str(e)[:70]}"
    try:
        pages = wiki(q)
    except Exception as e:
        LAST_ERROR = (LAST_ERROR + " | " if LAST_ERROR else "") + f"wikipedia: {str(e)[:70]}"
    if not items and not pages:
        return "", []

    lines = ["WEB RESULTS (Google News headlines and Wikipedia summaries; headlines are not full articles and "
             "can contain errors; trust only what they actually say):"]
    srcs = []
    for it in items:
        lines.append(f"- NEWS {it['date']} | {it['source']} | {it['title']}")
        srcs.append({"kind": "web", "source": f"{it['title'][:90]}", "section": f"{it['source']} {it['date']}".strip(),
                     "url": it["url"]})
    for pg in pages:
        lines.append(f"- WIKIPEDIA {pg['title']}: {pg['extract']}")
        srcs.append({"kind": "web", "source": f"Wikipedia: {pg['title']}", "section": "summary", "url": pg["url"]})
    return "\n".join(lines), srcs
