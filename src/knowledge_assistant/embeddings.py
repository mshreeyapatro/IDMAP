import time
from google import genai
from google.genai import types
from . import config

_client = None


def client():
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY or ASSISTANT_GEMINI_API_KEY is not set (see .env.example)")
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def _embed(texts: list[str], task_type: str) -> list[list[float]]:
    """One API call for the given list (callers keep lists small). Waits and retries on rate limits."""
    for attempt in range(6):
        try:
            res = client().models.embed_content(
                model=config.EMBED_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type=task_type, output_dimensionality=config.EMBED_DIM),
            )
            return [e.values for e in res.embeddings]
        except Exception as e:
            limited = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            if attempt == 5:
                if limited:
                    raise RuntimeError(
                        "Gemini quota exhausted (429). Run `python -m app.check_gemini`, check "
                        "https://ai.dev/rate-limit , wait a few minutes, or enable billing / use a key from "
                        "a different Google AI Studio project.") from e
                raise
            wait = 25 * (attempt + 1) if limited else 2 ** attempt * 2
            print(f"  Gemini busy ({'rate limit' if limited else 'error'}); waiting {wait}s then retrying...", flush=True)
            time.sleep(wait)


def embed_documents(texts: list[str]) -> list[list[float]]:
    return _embed(texts, "RETRIEVAL_DOCUMENT")


def embed_query(text: str) -> list[float]:
    return _embed([text], "RETRIEVAL_QUERY")[0]


def to_vec(values: list[float]) -> str:
    """pgvector text literal, used with %s::vector"""
    return "[" + ",".join(f"{v:.6f}" for v in values) + "]"
