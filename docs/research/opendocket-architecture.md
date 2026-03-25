# OpenDocket: Detailed Architecture Proposal

**Version:** 1.0
**Date:** March 25, 2026
**Prepared for:** Rae Johanek, Manifold AI

---

## Design Philosophy

This architecture is built on a "compose, don't rebuild" principle. Where a robust open-source tool already exists for a given function, OpenDocket integrates with it rather than reimplementing it. Where no tool exists — particularly for document-level change tracking and document-linked discourse aggregation — OpenDocket builds that capability as new, original code. The system is parameterized by a "Release Configuration" so that deploying for a new government document release requires a config file, not new code.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        OpenDocket Web Frontend                         │
│              (Next.js — Document Index, Viewer, Discourse)             │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────────────┐
│                      OpenDocket API (FastAPI)                           │
│                                                                         │
│  /documents    /changes    /discourse    /glossary    /config           │
└────┬──────────────┬────────────┬─────────────┬─────────────┬───────────┘
     │              │            │             │             │
     ▼              ▼            ▼             ▼             ▼
┌─────────┐  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐
│ Document │  │  Change   │ │Discourse │ │ Glossary │ │  Release  │
│  Layer   │  │  Tracker  │ │Aggregator│ │  Engine  │ │  Config   │
│(REUSE)   │  │(REUSE+NEW)│ │(NEW+REUSE│ │  (NEW)   │ │  (NEW)    │
└─────────┘  └───────────┘ └──────────┘ └──────────┘ └───────────┘
```

Each layer below details exactly which existing tool handles what, what's new code, and how they connect.

---

## Layer 1: Document Hosting, Viewing & Search

### What it does
Stores documents, makes them viewable in-browser (no download required), provides full-text search, OCR, and entity extraction.

### Reused technology: DocumentCloud (via MuckRock)

**Why DocumentCloud is the right backbone:**

- **Free for journalists, researchers, and civic use** — OpenDocket's use case qualifies
- **Python client library** (`pip install python-documentcloud`) with full CRUD: upload, search, annotate, organize into projects
- **In-browser viewer** — responsive oEmbed/iframe embeds for documents, individual pages, and annotations. No download required. This directly solves your core accessibility problem.
- **Built-in OCR** (Tesseract-based) — processes scanned PDFs automatically on upload
- **Full-text search** across all uploaded documents
- **Entity extraction** — auto-identifies people, organizations, locations
- **Annotation system** — add notes to specific pages/regions (useful for community context)
- **Proven at scale** — 4.1M+ documents hosted, used by ProPublica, NYT, Washington Post
- **Open source** — the platform itself is open source ([github.com/MuckRock](https://github.com/MuckRock))

**Integration approach:**

```python
# Upload a document to DocumentCloud
from documentcloud import DocumentCloud
client = DocumentCloud(username, password)

# Upload and auto-OCR
doc = client.documents.upload("path/to/document.pdf",
    title="EFTA-2025-001247",
    source="DOJ Epstein Library",
    access="public"
)

# Organize into a project (one project per release)
project = client.projects.get_or_create_by_title("Epstein Files - Batch 1")
project.document_list = [doc.id]
project.put()

# Search across all documents
results = client.documents.search("young assistants")

# Embed in frontend (returns responsive iframe code)
# https://www.documentcloud.org/documents/{id}
# oEmbed endpoint auto-generates embed code
```

**What DocumentCloud does NOT do** (and where OpenDocket fills gaps):

- Does not monitor government source pages for new/removed files
- Does not maintain a change history per document
- Does not aggregate or summarize public discourse
- Does not decode jargon or maintain a glossary

### Supplementary reuse: Jmail Data API (Epstein-specific, for email documents)

For the Epstein files specifically, Jmail has already done extraordinary work parsing, structuring, and indexing email documents. Their Data API is fully open — no API keys, no rate limits, static Parquet files at `data.jmail.world`.

**Integration approach:**

```python
import duckdb

# Query Jmail's email data directly over HTTP with SQL
conn = duckdb.connect()
emails = conn.execute("""
    SELECT * FROM read_parquet('https://data.jmail.world/v1/emails.parquet')
    WHERE body LIKE '%young assistants%'
""").fetchdf()

# Cross-reference Jmail email IDs with DocumentCloud document IDs
# via OpenDocket's metadata store
```

**When to use Jmail vs. DocumentCloud:** Jmail is the source of truth for *email* content (it's better structured for emails than raw PDFs). DocumentCloud is the source of truth for *non-email documents* (FBI records, flight logs, depositions, financial records). OpenDocket unifies both behind a single search and viewing interface.

---

## Layer 2: Document Change Tracking & Preservation

### What it does
Monitors official government release pages, detects when documents are added, removed, or modified, archives a copy of everything, and maintains a per-document change history.

### Reused technology: ChangeDetection.io + ArchiveBox

**ChangeDetection.io** handles the *detection* side:

- Self-hosted, open-source, Docker-deployable
- Full REST API (`/api/v1/`) for programmatic management of watches
- **PDF change monitoring** — can detect when PDF content changes
- **Webhook system** — fires notifications via apprise (supports webhooks, email, Slack, Discord, and 70+ services) when changes detected
- **Jinja2 templating** for notification content (can include diff details)
- **JSON API monitoring** — can monitor government API endpoints directly

**Integration approach:**

```yaml
# ChangeDetection.io watch configuration for DOJ Epstein Library
# (This would be auto-generated from the Release Config)

watches:
  - url: "https://www.justice.gov/epstein/doj-disclosures"
    title: "DOJ Epstein Disclosures Index"
    check_interval: 3600  # hourly
    notification_urls:
      - "json://opendocket-api:8000/webhooks/change-detected"
    css_filter: ".document-listing"  # target the document list specifically

  - url: "https://www.justice.gov/epstein"
    title: "DOJ Epstein Library Main Page"
    check_interval: 3600
    notification_urls:
      - "json://opendocket-api:8000/webhooks/change-detected"
```

**ArchiveBox** handles the *preservation* side:

- Self-hosted, open-source web archiving
- Saves HTML, PDFs, screenshots, full page content
- CLI, REST API (beta), and webhooks for integration
- Headless Chrome for capturing dynamic content
- **This is how we replicate what COURIER does** — when ChangeDetection.io fires a webhook saying "document X was removed," ArchiveBox already has the archived copy

**Integration approach:**

```python
# When a new document is detected on the DOJ page:
# 1. ChangeDetection.io webhook fires
# 2. OpenDocket's webhook handler:

import subprocess

def on_change_detected(payload):
    new_docs = parse_new_documents(payload)
    removed_docs = parse_removed_documents(payload)

    for doc_url in new_docs:
        # Archive immediately
        subprocess.run(["archivebox", "add", doc_url])
        # Upload to DocumentCloud
        pdf_path = download_pdf(doc_url)
        dc_doc = dc_client.documents.upload(pdf_path, ...)
        # Record in change history
        db.change_history.insert({
            "doc_id": extract_doc_id(doc_url),
            "action": "added",
            "timestamp": now(),
            "source_url": doc_url,
            "archive_url": archivebox_url,
            "documentcloud_id": dc_doc.id
        })

    for doc_url in removed_docs:
        # Archive is already preserved — just record the removal
        db.change_history.insert({
            "doc_id": extract_doc_id(doc_url),
            "action": "removed",
            "timestamp": now(),
            "note": "Removed from official DOJ page"
        })
```

### New code: Change Reconciliation Engine

This is the **core new component** that ties ChangeDetection.io and ArchiveBox together with DocumentCloud:

```
┌────────────────────┐     webhook      ┌─────────────────────────┐
│ ChangeDetection.io │ ──────────────▶  │  Change Reconciliation  │
│ (monitors source)  │                  │       Engine (NEW)       │
└────────────────────┘                  │                          │
                                        │  • Parses diffs          │
                                        │  • Identifies add/remove │
                                        │  • Extracts doc IDs      │
┌────────────────────┐   archive cmd    │  • Triggers archiving    │
│    ArchiveBox       │ ◀──────────────  │  • Triggers DC upload    │
│ (preserves copies) │                  │  • Updates change log    │
└────────────────────┘                  │  • Alerts subscribers    │
                                        └────────────┬────────────┘
┌────────────────────┐   upload API                  │
│   DocumentCloud    │ ◀─────────────────────────────┘
│  (hosts & serves)  │
└────────────────────┘
```

**What the Change Reconciliation Engine does (new code):**

1. Receives webhooks from ChangeDetection.io
2. Parses the diff to identify which specific documents were added, removed, or modified
3. For new docs: downloads the PDF, uploads to DocumentCloud, triggers ArchiveBox archive
4. For removed docs: flags in the database, verifies ArchiveBox has the archived copy
5. For modified docs: uploads new version to DocumentCloud, preserves both versions
6. Records every event in a structured change history database
7. Publishes change events (via WebSocket or SSE) to the frontend for real-time updates

---

## Layer 3: Discourse Aggregation & Summary

### What it does
For each document (by reference number), collects and summarizes what's being said about it across news, social media, legal databases, and forums.

### Why this is mostly new code

This is the **biggest gap** in the existing landscape. Communalytic is the closest tool, but it's designed for academic research on social dynamics — not for mapping discourse *back to specific documents.* It also doesn't have a public API suitable for real-time integration.

The discourse aggregation layer is where OpenDocket creates the most original value.

### Architecture: Multi-Source Collector + LLM Summarizer

```
┌────────────────────────────────────────────────────────┐
│              Discourse Aggregation Pipeline             │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ News Collector│  │Social Collect│  │Legal Collector│ │
│  │              │  │              │  │              │ │
│  │ • NewsAPI    │  │ • Reddit API │  │ • PACER/RECAP│ │
│  │ • GDELT      │  │   (PRAW)     │  │ • CourtList- │ │
│  │ • Google News│  │ • YouTube    │  │   ener       │ │
│  │   RSS feeds  │  │   Data API   │  │ • Google     │ │
│  │              │  │ • Bluesky    │  │   Scholar    │ │
│  │              │  │   (AT Proto) │  │              │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                  │         │
│         └────────┬────────┴────────┬─────────┘         │
│                  ▼                 ▼                    │
│         ┌──────────────┐  ┌──────────────┐             │
│         │  Document    │  │  LLM-based   │             │
│         │  Matcher     │  │  Summarizer  │             │
│         │              │  │              │             │
│         │ Maps mentions│  │ Generates    │             │
│         │ to doc IDs   │  │ per-document │             │
│         │ via ref #,   │  │ discourse    │             │
│         │ Bates stamp, │  │ summaries    │             │
│         │ title, entity│  │ with source  │             │
│         │ matching     │  │ citations    │             │
│         └──────┬───────┘  └──────┬───────┘             │
│                │                 │                      │
│                └────────┬────────┘                      │
│                         ▼                               │
│                ┌──────────────┐                         │
│                │  Discourse   │                         │
│                │  Database    │                         │
│                │              │                         │
│                │ Per-doc feed │                         │
│                │ Co-mentions  │                         │
│                │ Heat scores  │                         │
│                │ Trend data   │                         │
│                └──────────────┘                         │
└────────────────────────────────────────────────────────┘
```

### Source-by-source integration details

**News: GDELT + NewsAPI + RSS**

[GDELT](https://www.gdeltproject.org/) is a free, open platform that monitors news media worldwide in real-time. It's the most practical choice for news aggregation because it's free, has no rate limits for reasonable use, and covers 100+ languages. GDELT's DOC API allows full-text search of news articles and returns URLs, titles, publication dates, and tone analysis.

```python
# GDELT DOC API — free, no auth required
import requests

def search_news_for_document(doc_id, doc_title, entities):
    """Search GDELT for news mentioning a specific document."""
    queries = [doc_id] + entities[:3]  # Search by ID and top entities
    results = []
    for query in queries:
        resp = requests.get("https://api.gdeltproject.org/api/v2/doc/doc", params={
            "query": query,
            "mode": "artlist",
            "maxrecords": 50,
            "format": "json",
            "timespan": "90d"
        })
        results.extend(resp.json().get("articles", []))
    return deduplicate(results)
```

Supplemented with RSS feeds from specific high-value outlets (NPR, CBS News, Miami Herald, The Guardian) for more targeted coverage.

**Social Media: Reddit (PRAW) + YouTube Data API + Bluesky (AT Protocol)**

Reddit is the most important social source for this use case — r/EpsteinFiles, r/TrueCrime, r/conspiracy, and r/politics are where the deepest document-level analysis happens.

```python
import praw

reddit = praw.Reddit(client_id="...", client_secret="...", user_agent="OpenDocket")

def search_reddit_for_document(doc_id, keywords):
    """Search Reddit for discussions of a specific document."""
    results = []
    for subreddit_name in ["EpsteinFiles", "TrueCrime", "politics", "news"]:
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.search(doc_id, sort="relevance", time_filter="year"):
            results.append({
                "platform": "Reddit",
                "subreddit": subreddit_name,
                "title": post.title,
                "url": f"https://reddit.com{post.permalink}",
                "score": post.score,
                "num_comments": post.num_comments,
                "date": post.created_utc,
                "text": post.selftext[:500]
            })
    return results
```

YouTube Data API (free tier: 10,000 quota units/day) for video commentary. Bluesky via the AT Protocol (fully open, no API keys needed for public data).

**Legal: RECAP/CourtListener**

[CourtListener](https://www.courtlistener.com/) by Free Law Project is an open legal data platform with a free REST API. RECAP is their browser extension and database that crowd-sources PACER documents (which are normally paywalled). This is how we connect Epstein documents to related court filings.

```python
# CourtListener API — free, API key required (free registration)
def search_legal_for_document(doc_id, entities):
    resp = requests.get("https://www.courtlistener.com/api/rest/v4/search/", params={
        "q": f'"{doc_id}" OR "{entities[0]}"',
        "type": "r",  # RECAP documents
    }, headers={"Authorization": f"Token {COURTLISTENER_API_KEY}"})
    return resp.json()["results"]
```

### Document Matcher (new code, critical component)

The Document Matcher is the intelligence that maps unstructured mentions back to specific documents. This is necessary because people don't always reference documents by their official ID — they might say "the flight logs," "that FBI interview," or "document 7823."

```python
class DocumentMatcher:
    """Maps unstructured text mentions to specific document IDs."""

    def __init__(self, document_index):
        self.index = document_index  # All doc metadata from DocumentCloud

    def match(self, text):
        """Returns list of (doc_id, confidence, match_reason) tuples."""
        matches = []

        # Strategy 1: Exact reference number match (highest confidence)
        for doc in self.index:
            if doc.id in text:
                matches.append((doc.id, 1.0, "exact_id_match"))

        # Strategy 2: Bates number / page reference match
        bates_pattern = r'EFTA[-\s]?\d{4}[-\s]?\d{3,6}'
        for match in re.finditer(bates_pattern, text):
            normalized = normalize_bates(match.group())
            if normalized in self.bates_to_doc:
                matches.append((self.bates_to_doc[normalized], 0.95, "bates_match"))

        # Strategy 3: Entity + category co-occurrence (medium confidence)
        # e.g., "Maxwell deposition" → EFTA-2026-012001
        entities_in_text = extract_entities(text)
        for doc in self.index:
            overlap = set(entities_in_text) & set(doc.entities)
            if len(overlap) >= 2 and doc.category.lower() in text.lower():
                matches.append((doc.id, 0.7, f"entity_category_match: {overlap}"))

        # Strategy 4: LLM-assisted matching for ambiguous references
        # Used sparingly for high-value content only
        if not matches:
            matches = self.llm_match(text)

        return deduplicate_matches(matches)
```

### LLM Summarizer (new code)

Generates per-document discourse summaries with source citations. Runs on a schedule (daily) or on-demand.

```python
def generate_discourse_summary(doc_id, discourse_items):
    """Generate a sourced summary of public discourse about a document."""
    context = "\n".join([
        f"[{item['platform']}] {item['title']} ({item['date']}): {item['text'][:300]}"
        for item in discourse_items
    ])

    prompt = f"""Summarize the public discourse about government document {doc_id}.
    Focus on:
    1. What are the key claims or findings people are discussing?
    2. Are there any disputes or controversies?
    3. What context do commentators provide that isn't in the document itself?
    4. Has the document been connected to other documents or events?

    Every claim in your summary MUST cite its source by platform and title.

    Source material:
    {context}"""

    response = llm_client.generate(prompt, model="claude-sonnet-4-6")
    return response
```

### Communalytic: Advisory role, not direct integration

After researching Communalytic's capabilities, I recommend **not** directly integrating it into the pipeline for two reasons: (1) it doesn't have a public API suitable for automated integration, and (2) its strengths (network analysis, toxicity analysis, coordination detection) are complementary but not core to OpenDocket's document-centric mission. Instead, I recommend:

- **Export OpenDocket's discourse data to Communalytic** for deeper academic analysis when needed
- Use Communalytic's analytical *methods* as inspiration for OpenDocket's own co-mention network analysis
- If Communalytic adds API access in the future, integrate it as an optional enrichment source

---

## Layer 4: Jargon & Code Word Glossary

### What it does
Maintains a living, community-editable glossary of terms, codes, pseudonyms, and jargon found across documents, with confidence levels and sourcing.

### This is new code (no existing tool does this)

```
┌─────────────────────────────────────────────┐
│            Glossary Engine                    │
│                                               │
│  ┌─────────────┐    ┌──────────────────────┐ │
│  │ Auto-detect  │    │ Community Edits       │ │
│  │ (LLM-based)  │    │ (wiki-style with     │ │
│  │              │    │  moderation queue)    │ │
│  │ Scans new    │    │                      │ │
│  │ documents for│    │  Users can:          │ │
│  │ unusual terms│    │  • Propose new terms │ │
│  │ recurring    │    │  • Edit decodings    │ │
│  │ phrases,     │    │  • Add sources       │ │
│  │ potential    │    │  • Flag inaccuracies │ │
│  │ euphemisms   │    │  • Vote on confidence│ │
│  └──────┬───────┘    └──────────┬───────────┘ │
│         │                       │              │
│         └───────────┬───────────┘              │
│                     ▼                          │
│           ┌──────────────────┐                 │
│           │  Glossary DB     │                 │
│           │                  │                 │
│           │  term            │                 │
│           │  decoded_meaning │                 │
│           │  confidence      │                 │
│           │  source_docs[]   │                 │
│           │  external_srcs[] │                 │
│           │  occurrences     │                 │
│           │  edit_history[]  │                 │
│           └──────────────────┘                 │
└─────────────────────────────────────────────┘
```

---

## Layer 5: Release Configuration (Generalizability Engine)

### What it does
Makes OpenDocket deployable for *any* government document release by parameterizing everything that's case-specific.

```yaml
# release-configs/epstein-files.yaml
release:
  name: "Epstein Files"
  slug: "epstein-files"
  description: "Documents released under the Epstein Files Transparency Act (2025)"

source:
  type: "government_webpage"
  urls:
    - url: "https://www.justice.gov/epstein/doj-disclosures"
      label: "DOJ Disclosures"
    - url: "https://www.justice.gov/epstein"
      label: "Main Library"
  document_id_pattern: "EFTA-\\d{4}-\\d{6}"
  scraping:
    css_selector: ".document-listing a[href$='.pdf']"
    check_interval_seconds: 3600

supplementary_sources:
  - type: "jmail_api"
    base_url: "https://data.jmail.world/v1/"
    datasets: ["emails", "hoc-emails"]

documentcloud:
  project_prefix: "epstein-files"
  access: "public"

discourse:
  search_queries:
    - "Epstein files"
    - "Epstein documents"
    - "EFTA-"
    - "DOJ Epstein"
  subreddits: ["EpsteinFiles", "TrueCrime", "politics", "news", "conspiracy"]
  youtube_channels: ["LegalEagle", "LawAndCrime", "BreakingPoints"]
  news_outlets_rss:
    - "https://www.npr.org/rss/rss.php?id=1001"
    - "https://feeds.cbsnews.com/feeds/topstories.xml"
  courtlistener_queries:
    - "Epstein"
    - "Maxwell"
    - "Giuffre"

glossary:
  seed_terms:
    - term: "the house"
      meaning: "Epstein's Palm Beach residence at 358 El Brillo Way"
      confidence: "confirmed"
  auto_detect_enabled: true
```

```yaml
# release-configs/jfk-files.yaml (example of generalizability)
release:
  name: "JFK Assassination Records"
  slug: "jfk-files"
  description: "Documents released under the JFK Records Act"

source:
  type: "government_webpage"
  urls:
    - url: "https://www.archives.gov/research/jfk"
      label: "NARA JFK Collection"
  document_id_pattern: "\\d{3}-\\d{5}-\\d{5}"
  scraping:
    css_selector: ".document-link"
    check_interval_seconds: 86400  # daily

# ... same structure, different values
```

---

## Data Model

```sql
-- Core document metadata (synced from DocumentCloud + OpenDocket enrichment)
CREATE TABLE documents (
    id TEXT PRIMARY KEY,                -- e.g., "EFTA-2025-001247"
    release_slug TEXT NOT NULL,         -- e.g., "epstein-files"
    documentcloud_id TEXT,              -- DocumentCloud's internal ID
    archivebox_snapshot_id TEXT,        -- ArchiveBox archive reference
    jmail_id TEXT,                      -- Jmail cross-reference (if email)
    title TEXT NOT NULL,
    category TEXT,
    status TEXT DEFAULT 'available',    -- available | removed | modified
    page_count INTEGER,
    date_released DATE,
    date_removed DATE,
    source_url TEXT,
    ai_summary TEXT,
    entities JSONB,                     -- extracted entities
    jargon_terms JSONB,                 -- flagged terms
    discourse_score REAL DEFAULT 0,
    mention_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Full change history per document
CREATE TABLE change_history (
    id SERIAL PRIMARY KEY,
    doc_id TEXT REFERENCES documents(id),
    action TEXT NOT NULL,               -- added | removed | modified | restored
    timestamp TIMESTAMPTZ NOT NULL,
    note TEXT,
    diff_details JSONB,                 -- what specifically changed
    detected_by TEXT,                   -- "changedetection.io" | "manual"
    archive_url TEXT                    -- ArchiveBox URL for this version
);

-- Discourse items (from all sources)
CREATE TABLE discourse_items (
    id SERIAL PRIMARY KEY,
    doc_id TEXT REFERENCES documents(id),
    platform TEXT NOT NULL,             -- Reddit | YouTube | News | Legal | X | Bluesky
    source_name TEXT,                   -- subreddit, outlet, channel, etc.
    title TEXT NOT NULL,
    url TEXT,
    text_excerpt TEXT,
    date TIMESTAMPTZ,
    engagement_score INTEGER,           -- upvotes, views, likes (normalized)
    type TEXT,                          -- social | news | legal
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

-- Co-mention tracking (documents discussed together)
CREATE TABLE co_mentions (
    doc_id_1 TEXT REFERENCES documents(id),
    doc_id_2 TEXT REFERENCES documents(id),
    co_mention_count INTEGER DEFAULT 1,
    sources JSONB,                      -- which discourse items mention both
    PRIMARY KEY (doc_id_1, doc_id_2)
);

-- AI-generated discourse summaries (regenerated periodically)
CREATE TABLE discourse_summaries (
    doc_id TEXT REFERENCES documents(id),
    summary TEXT NOT NULL,
    source_count INTEGER,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    model_used TEXT
);

-- Glossary
CREATE TABLE glossary_terms (
    id SERIAL PRIMARY KEY,
    release_slug TEXT NOT NULL,
    term TEXT NOT NULL,
    decoded_meaning TEXT NOT NULL,
    confidence TEXT DEFAULT 'low',      -- confirmed | high | medium | low
    occurrences INTEGER DEFAULT 0,
    source_documents JSONB,             -- doc IDs where term appears
    external_sources JSONB,             -- citations for the decoding
    proposed_by TEXT,                   -- user or "auto-detect"
    approved BOOLEAN DEFAULT FALSE,
    edit_history JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Infrastructure & Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  Next.js      │  │  FastAPI     │  │  PostgreSQL            │ │
│  │  Frontend     │  │  API Server  │  │  (+ pgvector for       │ │
│  │  :3000        │  │  :8000       │  │   semantic search)     │ │
│  └──────────────┘  └──────────────┘  │  :5432                 │ │
│                                       └────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Change       │  │  ArchiveBox  │  │  Redis                 │ │
│  │ Detection.io │  │  :8001       │  │  (job queue + cache)   │ │
│  │  :5000       │  │              │  │  :6379                 │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Celery Workers (background tasks)                        │   │
│  │  • Discourse collection (scheduled: every 6 hours)        │   │
│  │  • Summary generation (scheduled: daily)                  │   │
│  │  • Document matcher (on new discourse items)              │   │
│  │  • Glossary auto-detect (on new documents)                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Hosted services (not self-hosted):**

- **DocumentCloud** — SaaS, free tier for civic/journalism use
- **LLM API** — Claude API (for summarization and glossary auto-detect)
- **GDELT** — free API, no hosting required

**Self-hosted (in the Docker stack):**

- ChangeDetection.io, ArchiveBox, PostgreSQL, Redis, the FastAPI API, the Next.js frontend, Celery workers

---

## Build vs. Reuse Summary

| Component | Approach | Tool | Effort |
|-----------|----------|------|--------|
| Document hosting & viewing | **REUSE** | DocumentCloud | Low — API integration |
| In-browser PDF viewer | **REUSE** | DocumentCloud oEmbed | Low — iframe embed |
| Full-text search + OCR | **REUSE** | DocumentCloud built-in | Low — comes free |
| Entity extraction | **REUSE** | DocumentCloud built-in | Low — comes free |
| Email data (Epstein) | **REUSE** | Jmail Data API | Low — Parquet/SQL |
| Change detection | **REUSE** | ChangeDetection.io | Low — config + webhook |
| Document preservation | **REUSE** | ArchiveBox | Low — CLI/API calls |
| Change reconciliation | **BUILD** | New (Python) | Medium — webhook handler + diff parsing |
| News aggregation | **REUSE** | GDELT API + RSS | Low — API calls |
| Reddit aggregation | **REUSE** | PRAW (Reddit API) | Low — API calls |
| YouTube aggregation | **REUSE** | YouTube Data API | Low — API calls |
| Legal aggregation | **REUSE** | CourtListener API | Low — API calls |
| Bluesky aggregation | **REUSE** | AT Protocol | Low — open protocol |
| Document Matcher | **BUILD** | New (Python + LLM) | High — core novel component |
| Discourse Summarizer | **BUILD** | New (LLM pipeline) | Medium — prompt engineering |
| Co-mention Network | **BUILD** | New (Python) | Medium — graph analysis |
| Jargon Glossary Engine | **BUILD** | New (Python + LLM) | Medium — auto-detect + community edit |
| Release Config System | **BUILD** | New (YAML + Python) | Medium — parameterization framework |
| Frontend | **BUILD** | New (Next.js + React) | High — custom UI |
| API Layer | **BUILD** | New (FastAPI) | Medium — CRUD + aggregation |

**Estimated split: ~40% reuse, ~60% new code** — but the new code is focused on the novel value (discourse aggregation, change reconciliation, glossary) rather than solved problems (document hosting, search, archiving).

---

## Development Phases

**Phase 1 (MVP — 4-6 weeks):**
Core document index with DocumentCloud integration, ChangeDetection.io monitoring, basic change history, manual glossary. Deploy for Epstein files.

**Phase 2 (Discourse — 4-6 weeks):**
Discourse aggregation pipeline (Reddit + news), Document Matcher, LLM summarizer, co-mention network. Per-document discourse feeds in the UI.

**Phase 3 (Polish — 3-4 weeks):**
Glossary auto-detect, community editing, Bluesky/YouTube/legal source integration, Release Config system, deploy a second release (e.g., JFK files) to prove generalizability.

**Phase 4 (Scale — ongoing):**
Real-time WebSocket updates, notification subscriptions ("alert me when document X changes"), Communalytic export for academic use, mobile-responsive design.

---

## API Design (Key Endpoints)

```
GET    /api/documents                     # List/search documents
GET    /api/documents/{id}                # Document detail + metadata
GET    /api/documents/{id}/changes        # Change history for a document
GET    /api/documents/{id}/discourse      # Discourse feed for a document
GET    /api/documents/{id}/glossary       # Jargon terms in a document
GET    /api/discourse/trending            # Most-discussed documents
GET    /api/discourse/co-mentions         # Document co-mention network
GET    /api/glossary                      # Full glossary
POST   /api/glossary                      # Propose a new term
PATCH  /api/glossary/{id}                 # Edit a term
GET    /api/changes/feed                  # Real-time change feed (SSE)
POST   /api/webhooks/change-detected      # ChangeDetection.io webhook
GET    /api/config/releases               # Available release configurations
```
