from . import config
from .db import get_conn
from .embeddings import embed_query, to_vec

_SQL = """SELECT id, source, section, doc_type, district, content,
                 1 - (embedding <=> %s::vector) AS score
          FROM rag_chunks {where}
          ORDER BY embedding <=> %s::vector LIMIT %s"""


def retrieve(question: str, top_k: int | None = None, qv: str | None = None) -> list[dict]:
    top_k = top_k or config.TOP_K
    qv = qv or to_vec(embed_query(question))
    hits: dict[int, dict] = {}
    cols = ["id", "source", "section", "doc_type", "district", "content", "score"]
    with get_conn() as conn:
        for row in conn.execute(_SQL.format(where=""), (qv, qv, top_k)).fetchall():
            hits[row[0]] = dict(zip(cols, row))
        # If a district is named, also pull its own chunks so they are not outranked.
        for d in config.find_districts(question)[:2]:
            for row in conn.execute(_SQL.format(where="WHERE district = %s"), (qv, d, qv, 3)).fetchall():
                hits.setdefault(row[0], dict(zip(cols, row)))
    ranked = sorted(hits.values(), key=lambda h: h["score"], reverse=True)
    return [h for h in ranked if h["score"] >= config.MIN_SCORE][: top_k + 2]
