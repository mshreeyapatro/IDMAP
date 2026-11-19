import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .assistant import answer
from .db import get_conn

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


class Turn(BaseModel):
    role: str
    text: str


class AskRequest(BaseModel):
    question: str
    history: list[Turn] = []


class FeedbackRequest(BaseModel):
    log_id: int
    rating: int  # 1 = helpful, -1 = not helpful
    correction: str | None = None


@router.get("/health")
def health():
    try:
        with get_conn() as conn:
            n = conn.execute("SELECT count(*) FROM rag_chunks").fetchone()[0]
        return {"ok": True, "chunks": n}
    except Exception as exc:
        return {"ok": False, "chunks": 0, "detail": str(exc)[:200]}


@router.post("/ask")
def ask(req: AskRequest):
    q = req.question.strip()
    if not q:
        raise HTTPException(400, "Empty question")
    out = answer(q, [t.model_dump() for t in req.history])
    try:
        with get_conn() as conn:
            row = conn.execute(
                "INSERT INTO rag_chat_log (question, answer, mode, sources) VALUES (%s,%s,%s,%s) RETURNING id",
                (q, out["answer"], out["mode"], json.dumps(out["sources"]))).fetchone()
            out["log_id"] = row[0]
    except Exception:
        pass  # logging must never break an answer
    return out


@router.post("/feedback")
def feedback(req: FeedbackRequest):
    with get_conn() as conn:
        conn.execute("UPDATE rag_chat_log SET rating=%s, correction=%s WHERE id=%s",
                     (req.rating, req.correction, req.log_id))
    return {"ok": True}
