# MASTER SPECIFICATION
# Brazil Pharma Intelligence Platform
# Version: 1.0.0 | Status: ACTIVE

---

## 1. IDENTITY

- **Name**: Brazil Pharma Intelligence Platform (internal codename: "PharmaGraph")
- **Type**: Private internal web application
- **Users**: Single administrator (owner only)
- **Classification**: Proprietary commercial product
- **Purpose**: Automated collection, structuring, search, and analysis of pharmaceutical regulatory intelligence from official government publications

---

## 2. CORE PRINCIPLE

> **The Entity Graph is the product.**
>
> The crawler is a utility. The database is storage.
> The graph — every node, every edge, every provenance trail —
> is the intellectual property.
>
> Everything in the system connects through the Entity Graph.
> Nothing is duplicated. Everything is connected.
> Every edge is provable.

---

## 3. PRIMARY DATA SOURCE

### 3.1 Brazil (Phase 1)
- **Source**: Diário Oficial da União (DOU) via IN.gov.br
- **URL**: https://www.in.gov.br/
- **Focus**: ANVISA publications
- **Publication types**:
  - Drug registrations (new, variations, renewals, cancellations)
  - Manufacturing site authorizations
  - GMP inspections (CBPF — Certificado de Boas Práticas de Fabricação)
  - API manufacturer registrations
  - Product cancellations and recalls
  - Resolution publications

### 3.2 Future Countries (Phase 2+)
- Mexico (COFEPRIS)
- Argentina (ANMAT)
- Colombia (INVIMA)
- **Architecture requirement**: Adding a new country requires only a new collector. Zero schema changes.

---

## 4. INGESTION PIPELINE

The pipeline is **unidirectional** and **date-driven**:

### 4.1 Pipeline Stages

| Stage | Action | Output |
|-------|--------|--------|
| Country | Namespace selector | Country code (BR, MX, AR, CO) |
| Source | Platform identifier | Source record (IN.gov.br) |
| Collector | Source-specific crawler | Collector instance |
| Date | Date range parameter | Start/end dates |
| Search | Query source for publications | Search request logged |
| Results | Parse search results page | List of publication URLs + metadata |
| Publication | Create publication record | Publication row (status: pending_download) |
| HTML | Download and store raw HTML | Immutable HTML + checksum (status: downloaded) |
| Parser | Extract structured data | Extraction results with confidence scores |
| Entities | Resolve and upsert nodes | Node records (companies, products, etc.) |
| Relationships | Create edges with provenance | Edge records linking nodes to publications |

### 4.2 Pipeline Properties
- **Resumable**: Every stage checkpoints. Can restart after failure.
- **Idempotent**: Re-running the same date produces no duplicates.
- **Auditable**: Every action logged with timestamp, status, duration.
- **Survives restart**: State persisted in database, not memory.

---

## 5. ENTITY GRAPH

### 5.1 Node Types

| Node Type | Table | Identity Key | Example |
|-----------|-------|--------------|---------|
| country | countries | ISO 3166-1 alpha-2 | BR |
| authority | authorities | (country_code, code) | ANVISA |
| company | companies | tax_id (CNPJ) | Laboratórios XYZ LTDA |
| manufacturer | manufacturers | tax_id (CNPJ) | Farmacêutica ABC S.A. |
| site | sites | (manufacturer_id, address_hash) | Planta X, São Paulo |
| address | addresses | normalized_hash | Av. Paulista 1000, SP |
| product | products | (brand_name, company_id) | Dipirona XYZ |
| active_ingredient | active_ingredients | inn_name | Dipirona |
| presentation | presentations | (product_id, strength, form, package) | 500mg comp 20ct |
| certificate | certificates | certificate_number | CBPF #123/2024 |
| registration | registrations | registration_number | 1.2345 |
| publication | publications | (source_id, url, checksum) | DOU 2024-01-15 p.42 |
| therapeutic_class | therapeutic_classes | atc_code | N02BB02 |
| dosage_form | dosage_forms | code | tablet |
| package_type | package_types | code | blister_box |

### 5.2 Edge Types

Every edge has **mandatory provenance**:
- `source_publication_id` — which publication asserted this relationship
- `text_span` — exact text from the publication
- `extraction_method` — regex, xpath, html_parser, or ai
- `confidence` — 0.0 to 1.0

| Edge Type | Source → Target |
|-----------|-----------------|
| published_in | Publication → Country |
| issued_by | Registration → Authority |
| held_by | Registration → Company |
| for_product | Registration → Product |
| contains_ingredient | Product → Active Ingredient |
| has_presentation | Product → Presentation |
| manufactured_by | Presentation → Manufacturer |
| produced_at_site | Manufacturer → Site |
| located_at | Site → Address |
| holds_certificate | Site/Manufacturer → Certificate |
| supersedes | Registration → Registration |
| varies | Registration → Registration |
| renews | Registration → Registration |
| cancels | Registration → Registration |
| belongs_to_class | Product → Therapeutic Class |
| mentioned_in | (any node) → Publication |

### 5.3 Entity Resolution

Before creating a node, the system resolves it:
1. Match by identifier (CNPJ, INN code, registration number)
2. Match by normalized name (exact)
3. Fuzzy match (trigram similarity > 0.85)
4. No match → create new node
5. Low-confidence match → queue for human review

Alias tracking and reversible merges are maintained.

---

## 6. TECH STACK

| Layer | Technology | Hosting (Free) |
|-------|-----------|----------------|
| Backend | Python 3.12 + FastAPI | Render Free Tier |
| Frontend | Next.js 14 + TypeScript + TailwindCSS | Vercel Free Tier |
| Database | PostgreSQL 16 | Supabase Free Tier |
| Task Queue | Background tasks (APScheduler) | Render Free Tier |
| CI/CD | GitHub Actions | GitHub Free Tier |
| Version Control | Git | GitHub Free Tier |
| PDF Generation | WeasyPrint (Python) | Render Free Tier |

**All open source. Zero paid libraries. Zero commercial APIs.**

---

## 7. USER INTERFACE

### 7.1 Design Language
- Bloomberg Terminal-inspired
- Dense information display
- Desktop-first
- Minimal colors (dark theme primary)
- Monospace for data, sans-serif for UI
- Fast — no unnecessary animations

### 7.2 Core Views
- **Dashboard**: Today's publications, new registrations, inspections, errors, confidence metrics
- **Entity Browser**: Companies, manufacturers, sites, products, ingredients
- **Entity Detail**: Full timeline + graph neighborhood + linked publications
- **Search**: Global search across all nodes and edges
- **Publication Browser**: All publications with filters
- **Graph View**: Interactive visualization of entity neighborhoods
- **Reports**: Company, manufacturer, site, drug, ingredient, timeline reports (HTML + PDF)
- **Admin**: Ingestion control, job monitoring, logs, entity merge queue

---

## 8. HISTORICAL IMPORT

- **Start date**: January 1, 2018
- **End date**: Current date
- **Strategy**: Day-by-day iteration
- **Checkpoint**: After each day completes, checkpoint saved to database
- **Resume**: If interrupted, resumes from last checkpoint
- **Deduplication**: By URL + checksum before download

---

## 9. SECURITY

- Single user authentication (password-protected)
- No public access
- All API endpoints require authentication
- Session-based auth with secure cookies
- No API keys exposed to client

---

## 10. BACKUPS

- Nightly database export (pg_dump)
- Stored locally on server
- Retention: 30 days rolling

---

## 11. WHAT IS NOT BUILT

- Newsletter
- Email alerts
- Marketing features
- CRM
- Billing / Subscriptions / Payments
- Customer portal
- Multi-user support
- SaaS features

---

## 12. SUCCESS CRITERIA

> A searchable, historically complete regulatory intelligence database
> covering Brazil from January 2018 to present, with every fact
> connected through a provable Entity Graph, expandable to
> Argentina, Mexico, and Colombia without architectural changes.
