import re
from datetime import datetime, timedelta, timezone
from google.genai import types
from . import config, prompts, websearch
from .curated import similar_curated
from .embeddings import client, embed_query, to_vec
from .retrieve import retrieve
from .tools_bridge import get_live_facts

GREETING = re.compile(r"^\s*(hi+|hello+|hey+|hii+|namaste|good (morning|afternoon|evening)|thanks?|thank you)\W*$", re.I)
RECENT = re.compile(r"\b(latest|recent|recently|most recent|today|todays|today's|tonight|now|current|currently|news|"
                    r"update|updates|this (week|month|year)|yesterday|breaking|ongoing|happening|202[5-9])\b", re.I)
_STOP = {"tell", "what", "which", "who", "when", "where", "why", "how", "about", "please", "give", "show",
         "explain", "the", "odisha", "india", "bay", "bengal", "cyclone", "cyclones", "storm", "district",
         "indian", "ocean", "state", "government", "imd", "osdma", "ndma", "ndrf", "can", "could", "does", "using", "gemini"}
NEEDS_WEB = "[[NEEDS_WEB]]"
SAFETY_WEATHER = re.compile(r"\b(weather|rain|rainfall|temperature|wind|forecast|warning|alert|cyclone|storm)\b", re.I)
IST = timezone(timedelta(hours=5, minutes=30))
WEB_FAIL_NOTE = ("WEB SEARCH FAILED: web search was needed but is UNAVAILABLE right now, so recent events and "
                 "unfamiliar names cannot be verified. Do NOT say that an event, storm or name does not exist or is "
                 "not in official lists. Say you could not verify it, share any related facts from the knowledge "
                 "base, and suggest checking IMD / OSDMA bulletins.")


def missing_terms(question: str, hits: list[dict]) -> list[str]:
    """Names in the question (e.g. a cyclone called Arnab) that appear nowhere in the retrieved knowledge."""
    text = " ".join(h["content"] for h in hits).lower()
    cands = set(re.findall(r"\b[A-Z][a-z]{2,}\b", question))
    for m in re.finditer(r"\b(?:cyclone|storm|typhoon|hurricane|village|town|city|block)\s+([A-Za-z]{3,})", question, re.I):
        cands.add(m.group(1))
    for m in re.finditer(r"\b([A-Za-z]{3,})\s+(?:cyclone|storm|typhoon|hurricane)\b", question, re.I):
        cands.add(m.group(1))
    known = {d.lower() for d in config.DISTRICTS}
    return sorted(w for w in cands if w.lower() not in _STOP and w.lower() not in known and w.lower() not in text)[:3]


def _kb_sources(hits):
    return [{"kind": "kb", "n": i + 1, "source": h["source"], "section": h["section"],
             "score": round(float(h["score"]), 3), "snippet": h["content"][:220]} for i, h in enumerate(hits)]


def _web_sources(res) -> list[dict]:
    try:
        chunks = res.candidates[0].grounding_metadata.grounding_chunks or []
    except Exception:
        return []
    out, seen = [], set()
    for c in chunks:
        w = getattr(c, "web", None)
        if w and w.uri and w.uri not in seen:
            seen.add(w.uri)
            out.append({"kind": "web", "source": w.title or "web source", "section": "Google Search", "url": w.uri})
    return out


def _cfg(use_tool: bool):
    kw = {"system_instruction": prompts.SYSTEM, "temperature": 0.2}
    if use_tool:
        kw["tools"] = [types.Tool(google_search=types.GoogleSearch())]
    return types.GenerateContentConfig(**kw)


def _with_note(contents, note: str):
    last = contents[-1]
    return contents[:-1] + [types.Content(role="user", parts=[types.Part(text=last.parts[0].text + "\n\n" + note)])]


def _generate(contents, use_tool: bool, fail_note: str = ""):
    """Pass 1: every model WITH Gemini's search tool (if requested). Pass 2: every model without it."""
    errors, models = [], [config.GEN_MODEL, *config.GEN_FALLBACKS]
    if use_tool:
        for model in models:
            try:
                res = client().models.generate_content(model=model, contents=contents, config=_cfg(True))
                text = (res.text or "").strip()
                if text:
                    return text, model, _web_sources(res), errors
                errors.append(f"{model} +web: empty reply")
            except Exception as e:
                errors.append(f"{model} +web: {str(e)[:140]}")
    msgs = _with_note(contents, fail_note) if (use_tool and fail_note) else contents
    for model in models:
        try:
            res = client().models.generate_content(model=model, contents=msgs, config=_cfg(False))
            text = (res.text or "").strip()
            if text:
                return text, model, [], errors
            errors.append(f"{model}: empty reply")
        except Exception as e:
            errors.append(f"{model}: {str(e)[:140]}")
    return None, None, [], errors


def _compose(now, tool_on, live_text, hits, kb_relevant, missing, curated, web_text, web_failed, question, history):
    msg = f"TODAY: {now}\n\nWEB SEARCH: {'available' if (tool_on or web_text) else 'NOT available'}\n\n"
    if live_text:
        msg += f"LIVE DATA:\n{live_text}\n\n"
    if kb_relevant:
        ctx = "\n\n".join(f"[{i + 1}] (source: {h['source']} > {h['section']})\n{h['content']}" for i, h in enumerate(hits))
        msg += f"KNOWLEDGE-BASE EXCERPTS:\n{ctx}\n\n"
    else:
        msg += "KNOWLEDGE-BASE EXCERPTS: none relevant to this question.\n\n"
    if missing:
        msg += (f"NOTE: the knowledge base has NO mention of: {', '.join(missing)}. "
                "Use web results for these; do not answer from the excerpts alone.\n\n")
    if web_text:
        msg += web_text + "\n\n"
    if web_failed:
        msg += WEB_FAIL_NOTE + "\n\n"
    if curated:
        ex = "\n\n".join(f"Q: {c['question']}\nA: {c['answer']}" for c in curated)
        msg += f"APPROVED EXAMPLES (reviewed by the IDMAP team):\n{ex}\n\n"
    msg += f"QUESTION: {question}"
    contents = [types.Content(role="model" if t.get("role") == "model" else "user",
                              parts=[types.Part(text=t.get("text", ""))]) for t in history[-6:]]
    contents.append(types.Content(role="user", parts=[types.Part(text=msg)]))
    return contents


def answer(question: str, history: list[dict]) -> dict:
    if GREETING.match(question):
        return {"answer": prompts.GREETING_REPLY, "mode": "chat", "sources": [], "tools_used": []}

    qv = to_vec(embed_query(question))          # one embedding call, reused below
    curated = similar_curated(qv)
    if curated and curated[0]["score"] >= config.CURATED_DIRECT:
        c = curated[0]
        return {"answer": c["answer"], "mode": "curated", "tools_used": [],
                "sources": [{"kind": "kb", "n": 1, "source": "Reviewed answer", "section": c["question"],
                             "score": round(c["score"], 3), "snippet": c["answer"][:220]}]}

    hits = retrieve(question, qv=qv)
    live_text, tools_used, live_ok = get_live_facts(question)
    best = hits[0]["score"] if hits else 0.0
    kb_relevant = best >= config.WEAK_SCORE
    recency = bool(RECENT.search(question))
    missing = missing_terms(question, hits)
    expect_web = recency or not kb_relevant or bool(missing)
    # Live model weather is useful for conditions, but it is not an official IMD warning
    # or cyclone bulletin. Look for current corroboration even when live weather is present.
    safety_weather = bool(SAFETY_WEATHER.search(question))
    use_web = config.WEB_MODE != "off" and (safety_weather or not live_ok) and (
        config.WEB_MODE == "always" or expect_web or safety_weather
    )

    if not (kb_relevant or live_text or use_web or config.ALLOW_GENERAL):
        return {"answer": prompts.NO_CONTEXT, "mode": "no_context", "sources": [], "tools_used": []}

    now = datetime.now(IST).strftime("%A, %d %B %Y, %H:%M IST")
    free = config.WEB_BACKEND == "free"

    def attempt(use_web_now: bool):
        web_text, web_src = ("", [])
        if use_web_now and free:
            search_q = question
            if safety_weather:
                search_q += " official IMD weather warning cyclone bulletin Odisha India"
            web_text, web_src = websearch.search(search_q, recent=recency or safety_weather)
        tool_on = use_web_now and not free
        failed = use_web_now and free and not web_text
        contents = _compose(now, tool_on, live_text, hits, kb_relevant, missing, curated, web_text, failed, question, history)
        text, model, web, errors = _generate(contents, tool_on, WEB_FAIL_NOTE if (expect_web or failed) else "")
        if free:
            web = web_src if (text and web_text) else []
        return text, model, web, errors

    text, model, web, errors = attempt(use_web)

    if text and NEEDS_WEB in text:  # RAG first; the model says the knowledge base was not enough
        text = text.replace(NEEDS_WEB, "").strip()
        if config.WEB_MODE != "off" and not use_web and not live_ok:
            use_web = True
            t2, m2, w2, e2 = attempt(True)
            if t2:
                text, model, web, errors = t2.replace(NEEDS_WEB, "").strip(), m2, w2, errors + e2
    elif text:
        text = text.strip()

    kb = _kb_sources(hits) if kb_relevant else []
    live_src = [{"kind": "live", "source": "Open-Meteo live data", "section": "current conditions + 3-day forecast"}] if live_ok else []

    if text:
        mode = "rag_web" if (web and kb_relevant) else "web" if web else "live" if live_ok else "rag" if kb_relevant else "general"
        out = {"answer": text, "mode": mode, "model": model, "sources": kb + live_src + web, "tools_used": tools_used}
        if use_web and (expect_web or True) and not web:
            why = websearch.LAST_ERROR if free else next((e for e in errors if "+web" in e), "Gemini did not run a web search")
            out["warning"] = (f"Web search returned nothing ({(why or 'no results')[:160]}). "
                              "This answer is NOT verified against current sources and may be incomplete or out of date.")
        return out

    parts = []
    if live_text:
        parts.append(live_text)
    parts += [f"[{i + 1}] {h['content'][:400]}" for i, h in enumerate(hits if kb_relevant else [])]
    fallback = "Gemini is unavailable. Here is the raw information I found:\n\n" + ("\n\n".join(parts) or "(nothing relevant)")
    return {"answer": fallback, "mode": "fallback", "sources": kb + live_src, "tools_used": tools_used,
            "llm_error": " | ".join(errors)[:600]}
