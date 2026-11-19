"""Reviewed Q&A pairs stored in Neon. They teach the assistant YOUR style and facts without fine-tuning.

    python -m app.curate import curated_qa.jsonl     # load pairs from a file
    python -m app.curate promote                     # review thumbs-up / corrected answers from real chats
    python -m app.curate list
"""
import hashlib
from . import config
from .db import get_conn
from .embeddings import embed_query, to_vec


def similar_curated(qv: str, k: int = 2) -> list[dict]:
    try:
        with get_conn() as conn:
            rows = conn.execute(
                """SELECT question, answer, 1 - (embedding <=> %s::vector) AS score
                   FROM rag_curated ORDER BY embedding <=> %s::vector LIMIT %s""", (qv, qv, k)).fetchall()
    except Exception:
        return []  # table missing (run python -m app.init_db) must never break answering
    return [{"question": q, "answer": a, "score": float(s)} for q, a, s in rows if s >= config.CURATED_MIN]


def add_curated(question: str, answer: str, origin: str = "manual") -> bool:
    qh = hashlib.sha256(question.strip().lower().encode()).hexdigest()
    vec = to_vec(embed_query(question.strip()))
    with get_conn(direct=True) as conn:
        cur = conn.execute(
            """INSERT INTO rag_curated (question, answer, origin, question_hash, embedding)
               VALUES (%s,%s,%s,%s,%s::vector)
               ON CONFLICT (question_hash) DO UPDATE SET answer = EXCLUDED.answer, origin = EXCLUDED.origin""",
            (question.strip(), answer.strip(), origin, qh, vec))
        return cur.rowcount > 0
