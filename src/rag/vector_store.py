"""
Vector Retrieval & Semantic Index Store for IDMAP RAG Pipeline.
Supports sentence-transformers or TF-IDF cosine similarity fallback for offline/lightweight execution.
"""

import os
import pickle
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from src.rag import ingestion

ROOT = Path(__file__).resolve().parents[2]
CACHE_PATH = ROOT / "data" / "processed" / "vector_store.pkl"


class VectorStore:
    def __init__(self, use_sentence_transformers: bool = True):
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.model = None
        self.vectorizer = None
        self.use_st = use_sentence_transformers

        if self.use_st:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                print("[VectorStore] Using SentenceTransformer ('all-MiniLM-L6-v2')")
            except Exception as e:
                print(f"[VectorStore] SentenceTransformer not available ({e}), falling back to TF-IDF.")
                self.use_st = False

        if not self.use_st:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(stop_words="english")
            print("[VectorStore] Using TF-IDF vectorizer fallback.")

    def build_index(self, force_rebuild: bool = False):
        """Loads chunks from ingestion and generates embeddings."""
        if not force_rebuild and CACHE_PATH.exists():
            try:
                with open(CACHE_PATH, "rb") as f:
                    data = pickle.load(f)
                    self.chunks = data["chunks"]
                    self.embeddings = data["embeddings"]
                    self.vectorizer = data.get("vectorizer")
                    print(f"[VectorStore] Loaded cached vector index with {len(self.chunks)} chunks.")
                    return
            except Exception as e:
                print(f"[VectorStore] Cache load failed ({e}), rebuilding index...")

        self.chunks = ingestion.get_all_knowledge_chunks()
        texts = [c["text"] for c in self.chunks]

        if not texts:
            print("[VectorStore] Warning: No knowledge chunks found!")
            self.embeddings = np.array([])
            return

        if self.use_st and self.model:
            self.embeddings = self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            if self.vectorizer is None:
                self.vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_mat = self.vectorizer.fit_transform(texts)
            # Normalize TF-IDF vectors
            from sklearn.preprocessing import normalize
            self.embeddings = normalize(tfidf_mat, norm="l2").toarray()

        # Cache to disk
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_PATH, "wb") as f:
            pickle.dump({
                "chunks": self.chunks,
                "embeddings": self.embeddings,
                "vectorizer": self.vectorizer
            }, f)
        print(f"[VectorStore] Built and cached index for {len(self.chunks)} chunks.")

    def search(self, query: str, top_k: int = 4, filter_meta: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Performs cosine similarity search against query."""
        if self.embeddings is None or len(self.chunks) == 0:
            self.build_index()

        if self.embeddings is None or len(self.embeddings) == 0:
            return []

        # Encode query
        if self.use_st and self.model:
            q_emb = self.model.encode([query], normalize_embeddings=True)[0]
        else:
            q_vec = self.vectorizer.transform([query])
            from sklearn.preprocessing import normalize
            q_emb = normalize(q_vec, norm="l2").toarray()[0]

        # Calculate cosine similarity (dot product of normalized vectors)
        scores = np.dot(self.embeddings, q_emb)

        # Apply metadata filtering if specified
        valid_indices = []
        for idx, chunk in enumerate(self.chunks):
            if filter_meta:
                match = True
                for k, v in filter_meta.items():
                    if chunk["metadata"].get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            valid_indices.append(idx)

        if not valid_indices:
            return []

        valid_scores = scores[valid_indices]
        top_indices = np.argsort(valid_scores)[::-1][:top_k]

        results = []
        for i in top_indices:
            actual_idx = valid_indices[i]
            chunk = self.chunks[actual_idx]
            results.append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "score": float(valid_scores[i]),
            })

        return results


_store_instance = None

def get_vector_store() -> VectorStore:
    """Singleton getter for vector store."""
    global _store_instance
    if _store_instance is None:
        _store_instance = VectorStore()
        _store_instance.build_index()
    return _store_instance


if __name__ == "__main__":
    store = get_vector_store()
    res = store.search("Puri cyclone Fani evacuation guidelines", top_k=3)
    print("\nSearch Query: 'Puri cyclone Fani evacuation guidelines'")
    for r in res:
        print(f"-> [Score: {r['score']:.3f}] Source: {r['metadata']['source']} Section: {r['metadata']['section']}")
        print(f"   Snippet: {r['text'][:120]}...\n")
