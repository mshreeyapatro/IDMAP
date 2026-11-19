import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# The integrated assistant can use its own credentials. If those are omitted,
# it falls back to the existing IDMAP credentials for a one-database setup.
ASSISTANT_DATABASE_URL = os.getenv("ASSISTANT_DATABASE_URL", "")
DATABASE_URL = ASSISTANT_DATABASE_URL or os.getenv("DATABASE_URL", "")
DATABASE_URL_DIRECT = (
    os.getenv("ASSISTANT_DIRECT_URL", "")
    or os.getenv("DATABASE_URL_DIRECT", "")
    or (os.getenv("DIRECT_URL", "") if not ASSISTANT_DATABASE_URL else "")
)
GEMINI_API_KEY = os.getenv("ASSISTANT_GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
GEN_MODEL = os.getenv("GEN_MODEL", "gemini-3.1-flash-lite")
GEN_FALLBACKS = [m.strip() for m in os.getenv("GEN_FALLBACKS", "gemini-3-flash-preview,gemini-2.5-flash").split(",") if m.strip()]
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "IDMAP Assistant")
WEB_MODE = os.getenv("WEB_MODE", "auto").lower()   # auto: RAG first, web only when needed (recommended) | always: Gemini may search on every question | off
if os.getenv("ALLOW_WEB", "true").lower() == "false":
    WEB_MODE = "off"
WEB_FALLBACK = os.getenv("WEB_FALLBACK", "true").lower() == "true"  # free news + Wikipedia search when Gemini's search tool is unavailable
ALLOW_GENERAL = os.getenv("ALLOW_GENERAL", "true").lower() == "true"  # answer from general knowledge (labelled) when nothing else fits
WEAK_SCORE = float(os.getenv("WEAK_SCORE", "0.60"))  # best knowledge-base score below this = "not about this question"
WEB_BACKEND = os.getenv("WEB_BACKEND", "free").lower()  # free = Google News RSS + Wikipedia (no billing) | gemini = Gemini's Google Search grounding (needs quota/billing)
CURATED_MIN = float(os.getenv("CURATED_MIN", "0.80"))      # reviewed Q&A used as style/fact examples
CURATED_DIRECT = float(os.getenv("CURATED_DIRECT", "0.93"))  # near-identical question -> reviewed answer as-is
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = int(os.getenv("EMBED_DIM", "768"))
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data"))).expanduser()
EMBED_BATCH = int(os.getenv("EMBED_BATCH", "20"))
EMBED_PAUSE = float(os.getenv("EMBED_PAUSE", "8"))
TOP_K = int(os.getenv("TOP_K", "5"))
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.45"))
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")]

DISTRICTS = [
    "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh", "Cuttack", "Deogarh",
    "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi",
    "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj",
    "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh",
]
ALIASES = {"Baleshwar": "Balasore", "Keonjhar": "Kendujhar", "Sonepur": "Subarnapur", "Khurda": "Khordha"}


def find_districts(text: str) -> list[str]:
    low = text.lower()
    found = {d for d in DISTRICTS if d.lower() in low}
    found |= {canon for alias, canon in ALIASES.items() if alias.lower() in low}
    return sorted(found)
