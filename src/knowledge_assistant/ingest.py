"""Read your data, chunk it, embed it with Gemini, store it in Neon.

Run:  python -m app.ingest --dry-run             (count chunks + estimate Neon size, no cost)
      python -m app.ingest                       (add new / changed content only)
      python -m app.ingest --also raw/historical (also scan another folder under DATA_DIR; repeatable)
      python -m app.ingest --reset               (wipe rag_chunks first)
"""
import argparse
import csv
import hashlib
import re
import time

from . import config
from .db import get_conn
from .embeddings import embed_documents, to_vec

MAX_CHARS = 1100
SKIP_COL = re.compile(r"embed|latent|feat(ure)?_?\d+|unnamed", re.I)  # model-vector columns are noise for search
MAX_FILE_BYTES = 5_000_000  # never read files bigger than this as text

# Structured CSVs -> one text "fact card" per row (path under DATA_DIR, label, row cap).
# (cv_features / anomaly_scores are numeric model outputs, so they stay in tools, not RAG.)
CSV_SOURCES = [
    ("processed/odisha_district_population.csv", "district_profile", 60),
    ("processed/odisha_district_nodes.csv", "district_profile", 60),
    ("processed/master_cyclone_dataset.csv", "cyclone_event", 400),
]


def md_sections(text: str):
    sections, title, buf = [], "Introduction", []
    for line in text.splitlines():
        m = re.match(r"^#{1,3}\s+(.*)", line)
        if m:
            if "".join(buf).strip():
                sections.append((title, "\n".join(buf).strip()))
            title, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    if "".join(buf).strip():
        sections.append((title, "\n".join(buf).strip()))
    return sections


def pack(text: str, limit: int = MAX_CHARS):
    """Split long sections on blank lines into pieces <= limit chars."""
    pieces, cur = [], ""
    for para in re.split(r"\n\s*\n", text):
        if cur and len(cur) + len(para) + 2 > limit:
            pieces.append(cur.strip())
            cur = ""
        cur += para + "\n\n"
    if cur.strip():
        pieces.append(cur.strip())
    return pieces


def district_of(text: str):
    found = config.find_districts(text)
    return found[0] if len(found) == 1 else None


def _fmt(v):
    try:
        f = float(v)
        return str(int(f)) if f == int(f) else f"{f:.3f}"
    except (ValueError, OverflowError):
        return v


def csv_cards(path, doc_type: str, cap: int, label: str):
    rows = []
    with open(path, newline="", encoding="utf-8-sig", errors="ignore") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if i >= cap:
                break
            body = "; ".join(f"{k}={_fmt(v)}" for k, v in row.items()
                             if v not in ("", None) and not SKIP_COL.search(k or ""))
            rows.append((label, f"row {i + 1}", doc_type, district_of(body), f"{doc_type} from {label}: {body}"))
    return rows


def text_chunks(path, label: str):
    rows = []
    for title, body in md_sections(path.read_text(encoding="utf-8", errors="ignore")):
        for piece in pack(body):
            rows.append((label, title, "knowledge_doc", district_of(piece), piece))
    return rows


def load_extra(folder: str):
    """Generic scan of one more folder: .md/.txt, .pdf (needs pypdf), small .csv."""
    rows, base = [], config.DATA_DIR / folder
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
            continue
        ext, label = path.suffix.lower(), str(path.relative_to(config.DATA_DIR))
        if ext in (".md", ".txt"):
            rows += text_chunks(path, label)
        elif ext == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError:
                print(f"skip {label}: run  pip install pypdf  to read PDFs")
                continue
            for n, page in enumerate(PdfReader(str(path)).pages, 1):
                for piece in pack((page.extract_text() or "").strip()):
                    rows.append((label, f"page {n}", "knowledge_doc", district_of(piece), piece))
        elif ext == ".csv":
            rows += csv_cards(path, "table_record", 200, label)
    return rows


def collect(extra_folders=()):
    rows = []  # (source, section, doc_type, district, content)
    kb = config.DATA_DIR / "knowledge_base"
    for path in sorted(kb.glob("*.md")):
        rows += text_chunks(path, path.name)
    for rel, doc_type, cap in CSV_SOURCES:
        path = config.DATA_DIR / rel
        if not path.exists():
            print(f"skip (not found): {path}")
            continue
        rows += csv_cards(path, doc_type, cap, path.name)
    for folder in extra_folders:
        rows += load_extra(folder)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--also", action="append", default=[], help="extra folder under DATA_DIR")
    args = ap.parse_args()

    rows = collect(args.also)
    chars = sum(len(r[4]) for r in rows)
    per_chunk = config.EMBED_DIM * 4 * 2 + 600  # vector + index + text/overhead (rough)
    print(f"Prepared {len(rows)} chunks ({chars / 1024:.0f} KB of text); "
          f"estimated Neon storage ~{len(rows) * per_chunk / 1e6:.1f} MB (free plan limit is 500 MB)")
    if args.dry_run:
        return

    with get_conn(direct=True) as conn:
        if args.reset:
            conn.execute("TRUNCATE rag_chunks RESTART IDENTITY")
        have = {r[0] for r in conn.execute("SELECT content_hash FROM rag_chunks").fetchall()}
        todo = []
        for r in rows:
            h = hashlib.sha256((r[0] + "|" + r[4]).encode()).hexdigest()
            if h not in have:
                todo.append((h, r))
        print(f"{len(todo)} new / changed chunks to embed")
        if not todo:
            return
        bs = config.EMBED_BATCH
        done = 0
        for i in range(0, len(todo), bs):
            batch = todo[i:i + bs]
            texts = [f"{r[0]} > {r[1]}\n{r[4]}" for _, r in batch]
            vecs = embed_documents(texts)
            with conn.cursor() as cur:
                for (h, r), v in zip(batch, vecs):
                    cur.execute(
                        """INSERT INTO rag_chunks (source, section, doc_type, district, content, content_hash, embedding)
                           VALUES (%s,%s,%s,%s,%s,%s,%s::vector) ON CONFLICT (content_hash) DO NOTHING""",
                        (r[0], r[1], r[2], r[3], r[4], h, to_vec(v)),
                    )
            done += len(batch)
            print(f"  stored {done}/{len(todo)}", flush=True)
            if i + bs < len(todo):
                time.sleep(config.EMBED_PAUSE)
        total = conn.execute("SELECT count(*) FROM rag_chunks").fetchone()[0]
        size = conn.execute("SELECT pg_size_pretty(pg_total_relation_size('rag_chunks'))").fetchone()[0]
        print(f"Done. rag_chunks holds {total} rows, using {size} in Neon.")


if __name__ == "__main__":
    main()
