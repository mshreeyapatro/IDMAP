CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS rag_chunks (
  id           BIGSERIAL PRIMARY KEY,
  source       TEXT NOT NULL,
  section      TEXT,
  doc_type     TEXT NOT NULL,
  district     TEXT,
  content      TEXT NOT NULL,
  content_hash TEXT UNIQUE NOT NULL,
  embedding    VECTOR(768) NOT NULL,
  created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS rag_chunks_embedding_idx
  ON rag_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS rag_chunks_district_idx ON rag_chunks (district);

CREATE TABLE IF NOT EXISTS rag_chat_log (
  id         BIGSERIAL PRIMARY KEY,
  question   TEXT NOT NULL,
  answer     TEXT,
  mode       TEXT,
  sources    JSONB,
  rating     SMALLINT,
  correction TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rag_curated (
  id            BIGSERIAL PRIMARY KEY,
  question      TEXT NOT NULL,
  answer        TEXT NOT NULL,
  origin        TEXT DEFAULT 'manual',
  question_hash TEXT UNIQUE NOT NULL,
  embedding     VECTOR(768) NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS rag_curated_embedding_idx
  ON rag_curated USING hnsw (embedding vector_cosine_ops);
