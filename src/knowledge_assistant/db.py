import psycopg
from . import config


def get_conn(direct: bool = False):
    """Use assistant-specific DB URLs when set, otherwise the shared IDMAP URLs."""
    url = (config.DATABASE_URL_DIRECT if direct else "") or config.DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL or ASSISTANT_DATABASE_URL is not set (see .env.example)")
    return psycopg.connect(url, autocommit=True, connect_timeout=15)
