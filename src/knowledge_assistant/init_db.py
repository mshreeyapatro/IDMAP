"""Create the pgvector extension and tables in Neon.  Run: python -m app.init_db"""
from pathlib import Path
from .db import get_conn

if __name__ == "__main__":
    sql = (Path(__file__).resolve().parent / "schema.sql").read_text()
    with get_conn(direct=True) as conn:
        conn.execute(sql)
    print("Neon is ready: pgvector enabled, tables created.")
