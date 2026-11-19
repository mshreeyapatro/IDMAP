import psycopg
from . import config


def get_conn(direct: bool = False):
    """direct=True uses DATABASE_URL_DIRECT (non-pooled) for setup/ingest; the app uses the pooled DATABASE_URL."""
    url = (config.DATABASE_URL_DIRECT if direct else "") or config.DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL is not set (see .env.example)")
    return psycopg.connect(url, autocommit=True, connect_timeout=15)
