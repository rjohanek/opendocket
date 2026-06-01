# OpenDocket

**Government Document Accessibility Platform — View, Track, Understand**

OpenDocket makes government document releases accessible to the public by solving three problems that make large-scale disclosures difficult to use:

1. **Documents require individual downloads** → OpenDocket hosts them in a web-based viewer (via DocumentCloud) so anyone can read them in their browser.
2. **Files are added and removed without notice** → OpenDocket monitors official sources and maintains a complete change history, preserving archived copies of removed documents.
3. **Raw documents lack context** → OpenDocket aggregates what the public is saying about each document (from news, Reddit, YouTube, legal filings, and more), generates AI summaries, and maintains a community-editable jargon glossary.

The platform is **generalizable** — deploying for a new government document release (JFK files, FOIA dumps, etc.) requires only a YAML config file, not new code.

Note: This project was made quickly as a proof of concept using Claude. 

Future directions include adding NLP to provide more robust document analysis.

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- (Optional) API keys for enhanced features (see Configuration below)

### 1. Clone and configure

```bash
git clone https://github.com/your-org/opendocket.git
cd opendocket

# Copy the example env file and edit with your values
cp .env.example .env
```

### 2. Start all services

```bash
docker compose up -d
```

This starts:


| Service             | URL                                                      | Description                  |
| ------------------- | -------------------------------------------------------- | ---------------------------- |
| **Frontend**        | [http://localhost:3000](http://localhost:3000)           | Web UI (Next.js)             |
| **API**             | [http://localhost:8000](http://localhost:8000)           | REST API (FastAPI)           |
| **API Docs**        | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger docs     |
| **ChangeDetection** | [http://localhost:5000](http://localhost:5000)           | Website monitoring dashboard |
| **ArchiveBox**      | [http://localhost:8001](http://localhost:8001)           | Document archive browser     |
| **PostgreSQL**      | localhost:5432                                           | Database                     |
| **Redis**           | localhost:6379                                           | Cache & job queue            |


### 3. Seed the database with sample data

```bash
docker compose exec api python scripts/seed_data.py
```

### 4. Open the app

Visit **[http://localhost:3000](http://localhost:3000)** to see the document index.

---

## Configuration

### Environment Variables (.env)

All configuration is done via the `.env` file. The app runs with **no API keys configured** — features degrade gracefully:


| Variable                              | Required? | What it enables                                              |
| ------------------------------------- | --------- | ------------------------------------------------------------ |
| `DOCUMENTCLOUD_USERNAME` / `PASSWORD` | No        | In-browser document viewing via DocumentCloud embed          |
| `REDDIT_CLIENT_ID` / `SECRET`         | No        | Reddit discourse collection                                  |
| `YOUTUBE_API_KEY`                     | No        | YouTube discourse collection                                 |
| `COURTLISTENER_API_KEY`               | No        | Legal document cross-referencing                             |
| `ANTHROPIC_API_KEY`                   | No        | AI-generated discourse summaries and glossary auto-detection |
| `ACTIVE_RELEASE`                      | Yes       | Which release config to use (default: `epstein-files`)       |


**Getting API keys:**

- **DocumentCloud**: Free for journalists/researchers. Sign up at [accounts.muckrock.com](https://accounts.muckrock.com/accounts/signup/)
- **Reddit**: Create an app at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) (select "script" type)
- **YouTube**: Get a Data API key at [Google Cloud Console](https://console.cloud.google.com/apis/credentials) (free tier: 10,000 units/day)
- **CourtListener**: Free registration at [courtlistener.com](https://www.courtlistener.com/sign-in/)
- **Anthropic**: Get a Claude API key at [console.anthropic.com](https://console.anthropic.com/)

### Release Configurations

Release configs live in `configs/releases/` as YAML files. Each config specifies:

- **Source URLs** to monitor for new/removed documents
- **Document ID pattern** (regex) for identifying documents
- **Scraping strategy** (CSS selectors, check intervals)
- **Discourse sources** (subreddits, RSS feeds, search queries)
- **Glossary seed terms** (known jargon with decoded meanings)

See `configs/releases/epstein-files.yaml` for a full example, and `configs/releases/jfk-files.yaml` for a generalizability demo.

**To add a new release:**

```bash
# 1. Create a config file
cp configs/releases/epstein-files.yaml configs/releases/my-release.yaml
# 2. Edit the config with your source URLs, search queries, etc.
# 3. Set ACTIVE_RELEASE=my-release in .env
# 4. Restart: docker compose restart api worker scheduler
```

---

## Architecture

```
Frontend (Next.js :3000)
    │
    ▼
API (FastAPI :8000)
    │
    ├── DocumentCloud ← document hosting, viewing, OCR, search
    ├── ChangeDetection.io ← monitors govt pages for changes
    ├── ArchiveBox ← preserves documents (including removed ones)
    ├── GDELT + RSS ← news article collection
    ├── Reddit API (PRAW) ← social media discourse
    ├── YouTube Data API ← video commentary
    ├── CourtListener ← legal cross-references
    ├── Bluesky (AT Protocol) ← social discourse
    └── Claude API ← AI summaries and glossary auto-detection
    │
    ▼
PostgreSQL + pgvector (data store)
Redis (cache + Celery job queue)
```

### Key Components


| Component                        | Location                                       | What it does                                                                                                           |
| -------------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Change Reconciliation Engine** | `backend/app/services/change_reconciler.py`    | Processes ChangeDetection.io webhooks, identifies document-level changes, triggers archiving and DocumentCloud uploads |
| **Discourse Collectors**         | `backend/app/services/discourse/collectors.py` | Platform-specific collectors (GDELT, Reddit, YouTube, CourtListener, Bluesky) that gather mentions                     |
| **Document Matcher**             | `backend/app/services/discourse/matcher.py`    | Maps unstructured text mentions back to specific document IDs using multi-strategy matching                            |
| **Discourse Summarizer**         | `backend/app/services/discourse/summarizer.py` | LLM-based summarization of per-document public discourse with source citations                                         |
| **Glossary Engine**              | `backend/app/services/glossary_engine.py`      | Auto-detects jargon in new documents, supports community editing                                                       |
| **Release Config Loader**        | `backend/app/core/release_config.py`           | Loads YAML configs that parameterize the system for different document releases                                        |
| **Celery Workers**               | `backend/app/workers/celery_app.py`            | Scheduled background tasks (discourse collection every 6h, glossary updates daily)                                     |


---

## API Endpoints


| Method | Endpoint                        | Description                                      |
| ------ | ------------------------------- | ------------------------------------------------ |
| GET    | `/api/documents`                | List/search documents (with filters and sorting) |
| GET    | `/api/documents/stats`          | Aggregate statistics                             |
| GET    | `/api/documents/categories`     | List categories with counts                      |
| GET    | `/api/documents/{id}`           | Document detail with change history              |
| GET    | `/api/changes/feed`             | Recent changes across all documents              |
| GET    | `/api/changes/stats`            | Change statistics                                |
| GET    | `/api/changes/stream`           | Server-Sent Events for real-time updates         |
| GET    | `/api/discourse/trending`       | Most-discussed documents                         |
| GET    | `/api/discourse/co-mentions`    | Document co-mention network                      |
| GET    | `/api/discourse/{doc_id}`       | Discourse feed for a specific document           |
| GET    | `/api/glossary`                 | Full glossary with search and filtering          |
| POST   | `/api/glossary`                 | Propose a new glossary term                      |
| PATCH  | `/api/glossary/{id}`            | Edit a glossary term                             |
| GET    | `/api/config/releases`          | List available release configurations            |
| POST   | `/api/webhooks/change-detected` | ChangeDetection.io webhook                       |
| GET    | `/api/health`                   | Health check                                     |


Full interactive docs at **[http://localhost:8000/docs](http://localhost:8000/docs)** (Swagger UI).

---

## Setting Up ChangeDetection.io

After `docker compose up`, visit **[http://localhost:5000](http://localhost:5000)** to configure watches:

1. Click **"+ Add"** to create a new watch
2. Enter the DOJ page URL: `https://www.justice.gov/epstein/doj-disclosures`
3. Set the check interval (e.g., 1 hour)
4. Under **Notifications**, add: `json://api:8000/api/webhooks/change-detected`
5. Optionally set a CSS filter to target only the document listing

When the watched page changes, ChangeDetection.io will fire a webhook to OpenDocket, which will automatically reconcile the changes.

---

## Development

### Running locally without Docker

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Workers:**

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info
```

### Running tests

```bash
cd backend
pytest tests/ -v
```

### Adding a new discourse collector

1. Add a new `collect_*` function in `backend/app/services/discourse/collectors.py`
2. Add it to the `collect_all()` function
3. Add any needed API keys to `config.py` and `.env.example`

---

## Project Structure

```
opendocket/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   │   ├── documents.py  # Document CRUD + search
│   │   │   ├── changes.py    # Change history + SSE stream
│   │   │   ├── discourse.py  # Discourse feed + trending
│   │   │   ├── glossary.py   # Glossary CRUD + community edits
│   │   │   ├── webhooks.py   # ChangeDetection.io webhook
│   │   │   └── releases.py   # Release config endpoints
│   │   ├── core/             # Config, database, release loader
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── services/         # Business logic
│   │   │   ├── change_reconciler.py    # Change detection → archive → DB
│   │   │   ├── glossary_engine.py      # Auto-detect + community edit
│   │   │   └── discourse/
│   │   │       ├── collectors.py       # Multi-platform data collection
│   │   │       ├── matcher.py          # Map mentions → document IDs
│   │   │       ├── summarizer.py       # LLM-based discourse summaries
│   │   │       └── pipeline.py         # Orchestrates the full flow
│   │   └── workers/          # Celery scheduled tasks
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── hooks/            # SWR data fetching hooks
│   │   ├── lib/              # API client
│   │   └── pages/            # Next.js pages
│   ├── Dockerfile
│   └── package.json
├── configs/
│   └── releases/             # YAML release configurations
│       ├── epstein-files.yaml
│       └── jfk-files.yaml
├── scripts/
│   ├── init_db.sql           # Database schema
│   └── seed_data.py          # Sample data for development
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## License

MIT — This is an open-source civic technology project.

---

## Contributing

Contributions welcome! Key areas where help is needed:

- **New discourse collectors** (X/Twitter, Mastodon, Telegram)
- **Document OCR and text extraction** improvements
- **Co-mention network visualization** (graph/force-directed layout)
- **New release configurations** for other government document releases
- **Community moderation tools** for the glossary
- **Accessibility improvements** (screen readers, keyboard navigation)
- **Internationalization** (many government releases are multilingual)

