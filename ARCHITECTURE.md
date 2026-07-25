# ARCHITECTURE
# Brazil Pharma Intelligence Platform
# Version: 1.0.0

---

## 1. SYSTEM OVERVIEW
┌─────────────────────────────────────────────────────────────────┐
│ USER INTERFACE │
│ (Next.js + TailwindCSS) │
│ │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│ │Dashboard │ │ Search │ │ Entity │ │ Reports │ │
│ │ │ │ │ │ Browser │ │ (HTML + PDF) │ │
│ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────┬──────────┘ │
│ │ │ │ │ │
│ ┌────┴────────────┴────────────┴────────────────┴──────────┐ │
│ │ API Client (fetch + auth) │ │
│ └──────────────────────────┬───────────────────────────────┘ │
└─────────────────────────────┼───────────────────────────────────┘
│ HTTPS
▼
┌─────────────────────────────────────────────────────────────────┐
│ API LAYER (FastAPI) │
│ │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│ │ Auth │ │ Graph │ │ Search │ │ Reports │ │
│ │ Guard │ │ Query │ │ Engine │ │ Generator │ │
│ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────┬──────────┘ │
│ │ │ │ │ │
│ ┌────┴────────────┴────────────┴────────────────┴──────────┐ │
│ │ Service Layer │ │
│ │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │ │
│ │ │ Pipeline │ │ Entity │ │ Parser │ │ Backup │ │ │
│ │ │ Manager │ │Resolver │ │ Engine │ │ Service │ │ │
│ │ └──────────┘ └──────────┘ └──────────┘ └────────────┘ │ │
│ └──────────────────────────┬───────────────────────────────┘ │
└─────────────────────────────┼───────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ DATA LAYER (Supabase) │
│ │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ ENTITY GRAPH │ │
│ │ │ │
│ │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────┐ │ │
│ │ │ Nodes │──│ Edges │──│Aliases │──│ Merges │ │ │
│ │ │ (typed) │ │(proven.)│ │ │ │ │ │ │
│ │ └─────────┘ └─────────┘ └─────────┘ └───────────┘ │ │
│ └──────────────────────────────────────────────────────────┘ │
│ │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│ │Publicat. │ │ Jobs │ │ Logs │ │ AI Extractions │ │
│ │(immutable)│ │ │ │ │ │ (versioned) │ │
│ └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ INGESTION PIPELINE │
│ │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐ │
│ │Scheduler│──▶│Collector│──▶│Download │──▶│ Parser │ │
│ │(daily) │ │(per src)│ │(HTML) │ │(regex/xpath) │ │
│ └─────────┘ └─────────┘ └─────────┘ └──────┬───────┘ │
│ │ │
│ ▼ │
│ ┌──────────────┐ │
│ │Entity Resolver│ │
│ │→ Nodes+Edges │ │
│ └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
## 2. DIRECTORY STRUCTURE
pharma-graph/
├── MASTER_SPEC.md
├── ARCHITECTURE.md
├── DATABASE.md
├── ROADMAP.md
├── DEVELOPMENT_RULES.md
│
├── backend/
│ ├── app/
│ │ ├── init.py
│ │ ├── main.py # FastAPI application entry
│ │ ├── config.py # Environment configuration
│ │ ├── database.py # Database connection pool
│ │ │
│ │ ├── models/ # SQLAlchemy models
│ │ │ ├── init.py
│ │ │ ├── nodes.py # All node type models
│ │ │ ├── edges.py # Edge model
│ │ │ ├── publications.py # Publication model
│ │ │ ├── jobs.py # Job tracking model
│ │ │ ├── logs.py # Log model
│ │ │ └── ai_extractions.py # AI extraction log model
│ │ │
│ │ ├── schemas/ # Pydantic schemas
│ │ │ ├── init.py
│ │ │ ├── nodes.py
│ │ │ ├── edges.py
│ │ │ ├── publications.py
│ │ │ ├── search.py
│ │ │ └── reports.py
│ │ │
│ │ ├── api/ # API route handlers
│ │ │ ├── init.py
│ │ │ ├── router.py # Main router aggregation
│ │ │ ├── auth.py
│ │ │ ├── dashboard.py
│ │ │ ├── entities.py
│ │ │ ├── publications.py
│ │ │ ├── search.py
│ │ │ ├── graph.py
│ │ │ ├── reports.py
│ │ │ ├── ingestion.py
│ │ │ └── admin.py
│ │ │
│ │ ├── services/ # Business logic
│ │ │ ├── init.py
│ │ │ ├── entity_resolver.py # Entity resolution engine
│ │ │ ├── graph_service.py # Graph query service
│ │ │ ├── search_service.py # Full-text search
│ │ │ ├── report_service.py # Report generation
│ │ │ ├── backup_service.py # Database backup
│ │ │ └── auth_service.py # Authentication
│ │ │
│ │ ├── pipeline/ # Ingestion pipeline
│ │ │ ├── init.py
│ │ │ ├── scheduler.py # Task scheduler
│ │ │ ├── base_collector.py # Abstract collector
│ │ │ ├── collectors/
│ │ │ │ ├── init.py
│ │ │ │ └── brazil_dou.py # IN.gov.br collector
│ │ │ ├── downloaders/
│ │ │ │ ├── init.py
│ │ │ │ └── html_downloader.py
│ │ │ ├── parsers/
│ │ │ │ ├── init.py
│ │ │ │ ├── base_parser.py # Abstract parser
│ │ │ │ └── anvisa_parser.py # ANVISA-specific parser
│ │ │ └── pipeline_manager.py # Orchestrates full pipeline
│ │ │
│ │ └── utils/ # Shared utilities
│ │ ├── init.py
│ │ ├── text_normalizer.py
│ │ ├── checksum.py
│ │ ├── cnpj.py # CNPJ validation/normalization
│ │ └── date_utils.py
│ │
│ ├── migrations/ # Alembic migrations
│ │ ├── env.py
│ │ ├── script.py.mako
│ │ └── versions/
│ │
│ ├── tests/ # Test suite
│ │ ├── init.py
│ │ ├── conftest.py
│ │ ├── test_api/
│ │ ├── test_services/
│ │ └── test_pipeline/
│ │
│ ├── requirements.txt
│ ├── alembic.ini
│ ├── Dockerfile
│ └── .env.example
│
├── frontend/
│ ├── src/
│ │ ├── app/ # Next.js App Router
│ │ │ ├── layout.tsx
│ │ │ ├── page.tsx # Dashboard
│ │ │ ├── login/
│ │ │ │ └── page.tsx
│ │ │ ├── entities/
│ │ │ │ ├── page.tsx # Entity browser
│ │ │ │ └── [id]/
│ │ │ │ └── page.tsx # Entity detail + timeline
│ │ │ ├── publications/
│ │ │ │ ├── page.tsx
│ │ │ │ └── [id]/
│ │ │ │ └── page.tsx
│ │ │ ├── search/
│ │ │ │ └── page.tsx
│ │ │ ├── graph/
│ │ │ │ └── page.tsx # Interactive graph view
│ │ │ ├── reports/
│ │ │ │ ├── page.tsx
│ │ │ │ └── generate/
│ │ │ │ └── page.tsx
│ │ │ └── admin/
│ │ │ ├── page.tsx # Ingestion control
│ │ │ ├── jobs/
│ │ │ │ └── page.tsx
│ │ │ └── logs/
│ │ │ └── page.tsx
│ │ │
│ │ ├── components/
│ │ │ ├── ui/ # Base UI components
│ │ │ ├── dashboard/
│ │ │ ├── entities/
│ │ │ ├── graph/
│ │ │ └── reports/
│ │ │
│ │ ├── lib/
│ │ │ ├── api.ts # API client
│ │ │ ├── auth.ts # Auth utilities
│ │ │ └── utils.ts
│ │ │
│ │ └── styles/
│ │ └── globals.css
│ │
│ ├── public/
│ ├── package.json
│ ├── next.config.js
│ ├── tailwind.config.ts
│ ├── tsconfig.json
│ ├── Dockerfile
│ └── .env.example
│
├── supabase/
│ └── migrations/
│ ├── 001_initial_schema.sql
│ ├── 002_seed_countries.sql
│ └── 003_enable_rls.sql
│
├── docker-compose.yml
├── .github/
│ └── workflows/
│ ├── ci.yml
│ └── deploy.yml
├── .gitignore
├── .env.example
└── README.md
## 3. DATA FLOW

### 3.1 Ingestion Flow
┌─────────────┐
│ Scheduler │ (daily cron or manual trigger)
└──────┬──────┘
│ creates job
▼
┌─────────────┐
│ Job Record │ (status: pending, date_range, country, source)
└──────┬──────┘
│
▼
┌─────────────┐ ┌──────────────────┐
│ Collector │────▶│ Log: search │
│ (Brazil) │ │ requested │
└──────┬──────┘ └──────────────────┘
│ returns list of URLs
▼
┌─────────────┐ ┌──────────────────┐
│ Deduplicate │────▶│ Log: skipped │
│ (by URL + │ │ (N duplicates) │
│ checksum) │ └──────────────────┘
└──────┬──────┘
│ new publications
▼
┌─────────────┐ ┌──────────────────┐
│ Create │────▶│ Publication │
│ Publication│ │ (status: │
│ Records │ │ pending_download)
└──────┬──────┘ └──────────────────┘
│
▼
┌─────────────┐ ┌──────────────────┐
│ Download │────▶│ Log: downloaded │
│ HTML │ │ HTML + checksum │
└──────┬──────┘ └──────────────────┘
│ stores raw HTML (immutable)
▼
┌─────────────┐
│ Parser │ (regex, XPath, HTML parsing)
│ (ANVISA) │
└──────┬──────┘
│ extracted fields + confidence
▼
┌─────────────┐
│ Entity │ (normalize → match → resolve)
│ Resolver │
└──────┬──────┘
│ upserts nodes, creates edges
▼
┌─────────────────────────────────────────┐
│ ENTITY GRAPH │
│ │
│ Nodes: companies, products, sites... │
│ Edges: held_by, manufactured_by... │
│ All with provenance → publication │
└─────────────────────────────────────────┘
### 3.2 Query Flow
User Request (search, entity detail, report)
│
▼
┌─────────────┐
│ API Route │ (auth check)
└──────┬──────┘
│
▼
┌─────────────┐
│ Service │ (business logic)
└──────┬──────┘
│
▼
┌─────────────┐
│ Graph │ (SQL queries, recursive traversals)
│ Query │
└──────┬──────┘
│
▼
┌─────────────┐
│ Response │ (JSON or PDF)
└─────────────┘
## 4. KEY DESIGN DECISIONS

| Decision | Rationale |
|----------|-----------|
| Unified `edges` table | Single source of truth for all relationships; provenance on every edge |
| Typed node tables | Each entity type has specific attributes; proper indexing per type |
| Immutable publications | Source data never modified; re-parseable if parser improves |
| Append-only graph | Nodes/edges never deleted; marked inactive with timestamp |
| Entity resolution before insert | Prevents duplicate nodes; maintains graph integrity |
| Date-driven pipeline | Deterministic; resumable; no missed dates |
| Python backend | Best ecosystem for parsing, NLP, PDF generation |
| Next.js frontend | SSR for fast initial load; App Router for modern patterns |
| Supabase PostgreSQL | Free tier sufficient; built-in auth; row-level security |

---

## 5. SCALABILITY CONSIDERATIONS

- **Adding a country**: Create new collector class + new source record. Zero schema changes.
- **Adding a node type**: Create new typed table + new edge types. Existing graph unaffected.
- **10M+ edges**: PostgreSQL handles with proper indexing; materialized views for dashboard.
- **Concurrent ingestion**: Job-based; each collector runs independently.
- **Parser improvements**: Re-parse existing publications; new edges created alongside old (versioned).
