import argparse
import json
import time
from .curated import add_curated
from .db import get_conn


def cmd_import(path):
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            row = json.loads(line)
            add_curated(row["question"], row["answer"], "manual")
            n += 1
            print(f"  saved: {row['question'][:70]}")
            time.sleep(1.5)  # stay under free-tier rate limits
    print(f"Imported {n} reviewed answers.")


def cmd_promote():
    with get_conn(direct=True) as conn:
        rows = conn.execute(
            """SELECT id, question, answer, correction, rating FROM rag_chat_log
               WHERE (rating = 1 OR correction IS NOT NULL) AND mode IN ('rag','curated')
               ORDER BY id DESC LIMIT 30""").fetchall()
    if not rows:
        print("Nothing to review yet. Use the helpful / not helpful buttons in the UI first.")
        return
    for _id, q, a, corr, rating in rows:
        final = corr or a
        print("\n" + "=" * 70 + f"\nQUESTION: {q}\n\nANSWER{' (corrected)' if corr else ''}:\n{final}\n")
        if input("Save as a reviewed answer? [y/N] ").strip().lower() == "y":
            add_curated(q, final, "feedback")
            print("  saved.")


def cmd_list():
    with get_conn() as conn:
        for q, o in conn.execute("SELECT question, origin FROM rag_curated ORDER BY id").fetchall():
            print(f"[{o}] {q}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["import", "promote", "list"])
    ap.add_argument("file", nargs="?")
    a = ap.parse_args()
    if a.action == "import":
        cmd_import(a.file or "curated_qa.jsonl")
    elif a.action == "promote":
        cmd_promote()
    else:
        cmd_list()
