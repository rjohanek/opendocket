-- OpenDocket Database Schema
-- Run automatically on first docker-compose up

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ─── Documents ───────────────────────────────────────────────────────────────

CREATE TABLE documents (
    id TEXT PRIMARY KEY,                    -- e.g., "EFTA-2025-001247"
    release_slug TEXT NOT NULL,             -- e.g., "epstein-files"
    documentcloud_id TEXT,                  -- DocumentCloud internal ID
    archivebox_snapshot_id TEXT,            -- ArchiveBox archive reference
    jmail_id TEXT,                          -- Jmail cross-reference (emails only)
    title TEXT NOT NULL,
    category TEXT,
    status TEXT DEFAULT 'available'
        CHECK (status IN ('available', 'removed', 'modified')),
    page_count INTEGER,
    date_released DATE,
    date_removed DATE,
    source_url TEXT,
    ai_summary TEXT,
    entities JSONB DEFAULT '[]'::jsonb,
    jargon_terms JSONB DEFAULT '[]'::jsonb,
    discourse_score REAL DEFAULT 0,
    mention_count INTEGER DEFAULT 0,
    embedding vector(1536),                 -- for semantic search
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_release ON documents(release_slug);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_documents_discourse ON documents(discourse_score DESC);
CREATE INDEX idx_documents_title_trgm ON documents USING gin(title gin_trgm_ops);
CREATE INDEX idx_documents_entities ON documents USING gin(entities);

-- ─── Change History ──────────────────────────────────────────────────────────

CREATE TABLE change_history (
    id SERIAL PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    action TEXT NOT NULL
        CHECK (action IN ('added', 'removed', 'modified', 'restored')),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    note TEXT,
    diff_details JSONB,
    detected_by TEXT DEFAULT 'system',
    archive_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_change_history_doc ON change_history(doc_id);
CREATE INDEX idx_change_history_time ON change_history(timestamp DESC);
CREATE INDEX idx_change_history_action ON change_history(action);

-- ─── Discourse Items ─────────────────────────────────────────────────────────

CREATE TABLE discourse_items (
    id SERIAL PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,                 -- Reddit, YouTube, News, Legal, X, Bluesky
    source_name TEXT,                       -- subreddit, outlet, channel, etc.
    title TEXT NOT NULL,
    url TEXT,
    text_excerpt TEXT,
    author TEXT,
    date TIMESTAMPTZ,
    engagement_score INTEGER DEFAULT 0,     -- upvotes, views, likes (normalized)
    type TEXT CHECK (type IN ('social', 'news', 'legal')),
    raw_data JSONB,                         -- full API response for reference
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_discourse_doc ON discourse_items(doc_id);
CREATE INDEX idx_discourse_platform ON discourse_items(platform);
CREATE INDEX idx_discourse_type ON discourse_items(type);
CREATE INDEX idx_discourse_date ON discourse_items(date DESC);
CREATE INDEX idx_discourse_engagement ON discourse_items(engagement_score DESC);

-- ─── Co-mentions ─────────────────────────────────────────────────────────────

CREATE TABLE co_mentions (
    doc_id_1 TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    doc_id_2 TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    co_mention_count INTEGER DEFAULT 1,
    sources JSONB DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (doc_id_1, doc_id_2),
    CHECK (doc_id_1 < doc_id_2)             -- enforce ordering to prevent dupes
);

-- ─── Discourse Summaries ─────────────────────────────────────────────────────

CREATE TABLE discourse_summaries (
    id SERIAL PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    source_count INTEGER,
    model_used TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_discourse_summaries_doc ON discourse_summaries(doc_id);

-- ─── Glossary ────────────────────────────────────────────────────────────────

CREATE TABLE glossary_terms (
    id SERIAL PRIMARY KEY,
    release_slug TEXT NOT NULL,
    term TEXT NOT NULL,
    decoded_meaning TEXT NOT NULL,
    confidence TEXT DEFAULT 'low'
        CHECK (confidence IN ('confirmed', 'high', 'medium', 'low')),
    occurrences INTEGER DEFAULT 0,
    source_documents JSONB DEFAULT '[]'::jsonb,
    external_sources JSONB DEFAULT '[]'::jsonb,
    proposed_by TEXT DEFAULT 'system',
    approved BOOLEAN DEFAULT FALSE,
    edit_history JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(release_slug, term)
);

CREATE INDEX idx_glossary_release ON glossary_terms(release_slug);
CREATE INDEX idx_glossary_confidence ON glossary_terms(confidence);
CREATE INDEX idx_glossary_occurrences ON glossary_terms(occurrences DESC);

-- ─── Utility ─────────────────────────────────────────────────────────────────

-- Auto-update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER glossary_updated_at
    BEFORE UPDATE ON glossary_terms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
