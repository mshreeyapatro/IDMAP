"""
RAG Knowledge Base Ingestion & Chunking Module for IDMAP.
Parses documents in data/knowledge_base/ and extracts structured chunks with rich metadata.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE_DIR = ROOT / "data" / "knowledge_base"


def load_raw_documents() -> List[Dict[str, Any]]:
    """Loads all Markdown, Text, and CSV files in data/knowledge_base/."""
    docs = []
    if not KNOWLEDGE_BASE_DIR.exists():
        return docs

    for filepath in KNOWLEDGE_BASE_DIR.glob("*.*"):
        if filepath.suffix.lower() in [".md", ".txt", ".csv"]:
            try:
                content = filepath.read_text(encoding="utf-8")
                docs.append({
                    "filename": filepath.name,
                    "path": str(filepath),
                    "content": content,
                })
            except Exception as e:
                print(f"[RAG Ingestion] Error reading {filepath}: {e}")
    return docs


def extract_metadata_from_section(section_title: str, doc_name: str) -> Dict[str, Any]:
    """Extracts metadata tags from section headers and content."""
    meta = {
        "source": doc_name,
        "section": section_title,
        "year": None,
        "cyclone": None,
        "district": None,
        "topic": "general",
    }
    
    # Check for years (e.g. 1999, 2013, 2014, 2019, 2020, 2021)
    year_match = re.search(r"\b(199\d|20[0-2]\d)\b", section_title)
    if year_match:
        meta["year"] = int(year_match.group(1))

    # Check for cyclone names
    cyclones = ["Fani", "Phailin", "Super Cyclone", "Hudhud", "Amphan", "Yaas", "Gulab"]
    for c in cyclones:
        if c.lower() in section_title.lower():
            meta["cyclone"] = c
            break

    # Check for district names
    districts = [
        "Puri", "Jagatsinghpur", "Kendrapara", "Bhadrak", "Balasore",
        "Ganjam", "Khordha", "Cuttack", "Mayurbhanj", "Gajapati", "Rayagada", "Koraput"
    ]
    for d in districts:
        if d.lower() in section_title.lower():
            meta["district"] = d
            break

    # Topic classification
    st_lower = section_title.lower()
    if "imd" in st_lower or "categorization" in st_lower or "warning" in st_lower:
        meta["topic"] = "imd_guidelines"
    elif "district" in st_lower or "profile" in st_lower:
        meta["topic"] = "district_profile"
    elif "cyclone" in st_lower or "history" in st_lower:
        meta["topic"] = "cyclone_history"
    elif "surge" in st_lower or "hazard" in st_lower or "protocol" in st_lower:
        meta["topic"] = "disaster_protocol"

    return meta


def chunk_document(doc: Dict[str, Any], max_chars: int = 600, overlap: int = 100) -> List[Dict[str, Any]]:
    """Splits a document into structured chunks by markdown headings and character limits."""
    content = doc["content"]
    filename = doc["filename"]

    chunks = []
    # Split by markdown h2 or h3 headers
    sections = re.split(r"\n(?=##?\s+)", content)

    chunk_id = 0
    for section in sections:
        section = section.strip()
        if not section:
            continue

        lines = section.split("\n")
        header = lines[0].replace("#", "").strip() if lines[0].startswith("#") else "General Information"
        section_meta = extract_metadata_from_section(header, filename)

        # If section is small enough, keep as single chunk
        if len(section) <= max_chars:
            chunks.append({
                "chunk_id": f"{filename}_{chunk_id}",
                "text": section,
                "metadata": {**section_meta, "chunk_index": chunk_id}
            })
            chunk_id += 1
        else:
            # Sub-chunk longer sections
            start = 0
            while start < len(section):
                end = min(start + max_chars, len(section))
                chunk_text = section[start:end]
                chunks.append({
                    "chunk_id": f"{filename}_{chunk_id}",
                    "text": chunk_text,
                    "metadata": {**section_meta, "chunk_index": chunk_id}
                })
                chunk_id += 1
                start += max_chars - overlap

    return chunks


def get_all_knowledge_chunks() -> List[Dict[str, Any]]:
    """Main ingestion helper: returns all processed chunks from knowledge base."""
    docs = load_raw_documents()
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    return all_chunks


if __name__ == "__main__":
    chunks = get_all_knowledge_chunks()
    print(f"Loaded {len(chunks)} knowledge chunks from {KNOWLEDGE_BASE_DIR}.")
    if chunks:
        print("Sample Chunk 0:", chunks[0])
