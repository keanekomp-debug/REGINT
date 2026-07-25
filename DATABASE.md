# DATABASE DESIGN
# Brazil Pharma Intelligence Platform
# Version: 1.0.0

---

## 1. DESIGN PRINCIPLES

1. **Append-only**: Records are never deleted. Soft deletes via `deleted_at`.
2. **Immutable sources**: Publications, once downloaded, are never modified.
3. **Provenance on every edge**: Every relationship cites its source publication.
4. **Country-agnostic**: Adding a country requires zero schema changes.
5. **Indexed**: Every foreign key, search column, and filter column has an index.
6. **Auditable**: Every mutation logged with timestamp and job reference.
7. **Reversible migrations**: Every migration has UP and DOWN scripts.
8. **Versioned AI**: Every AI extraction stored with prompt, model, confidence, timestamp.

---

## 2. TABLE INVENTORY

### 2.1 Reference / Configuration
| Table | Purpose |
|-------|---------|
| countries | Country registry (BR, MX, AR, CO) |
| authorities | Regulatory bodies (ANVISA, COFEPRIS, etc.) |
| sources | Data source endpoints (IN.gov.br) |
| users | Single admin user |

### 2.2 Pipeline / Ingestion
| Table | Purpose |
|-------|---------|
| publications | Immutable source publications |
| jobs | Ingestion job tracking |
| logs | System and crawler logs |
| ai_extractions | AI extraction audit trail |

### 2.3 Entity Graph — Nodes
| Table | Purpose |
|-------|---------|
| companies | Pharmaceutical companies (holders) |
| manufacturers | Manufacturing companies |
| sites | Manufacturing sites |
| addresses | Physical addresses |
| products | Drug products (brand names) |
| active_ingredients | Active pharmaceutical ingredients |
| presentations | Product presentations (strength/form/package) |
| registrations | Drug registrations |
| certificates | GMP/CBPF certificates |
| therapeutic_classes | ATC therapeutic classes |
| dosage_forms | Dosage form types |
| package_types | Package type types |

### 2.4 Entity Graph — Edges
| Table | Purpose |
|-------|---------|
| edges | Unified relationship table with provenance |
| entity_aliases | Name variants for entity resolution |
| entity_merges | Reversible merge log |

### 2.5 Search
| Table | Purpose |
|-------|---------|
| search_index | Denormalized search vector for fast global search |

---

## 3. COMPLETE SCHEMA

### 3.1 Reference Tables

```sql
-- ============================================================
-- COUNTRIES
-- ============================================================
CREATE TABLE countries (
    code            CHAR(2) PRIMARY KEY,          -- ISO 3166-1 alpha-2
    name            TEXT NOT NULL,
    name_native     TEXT,
    region          TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- ============================================================
-- AUTHORITIES
-- ============================================================
CREATE TABLE authorities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code    CHAR(2) NOT NULL REFERENCES countries(code),
    code            TEXT NOT NULL,                 -- e.g., 'ANVISA'
    name            TEXT NOT NULL,
    name_short      TEXT NOT NULL,
    url             TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(country_code, code)
);

CREATE INDEX idx_authorities_country ON authorities(country_code);
CREATE INDEX idx_authorities_active ON authorities(is_active) WHERE is_active = TRUE;

CREATE INDEX idx_countries_region ON countries(region);
CREATE INDEX idx_countries_active ON countries(is_active) WHERE is_active = TRUE;
-- ============================================================
-- SOURCES
-- ============================================================
CREATE TABLE sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code    CHAR(2) NOT NULL REFERENCES countries(code),
    authority_id    UUID REFERENCES authorities(id),
    code            TEXT NOT NULL,                 -- e.g., 'DOU_ANVISA'
    name            TEXT NOT NULL,
    base_url        TEXT NOT NULL,
    collector_class TEXT NOT NULL,                 -- Python class path
    schedule_cron   TEXT,                          -- e.g., '0 6 * * *'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    config          JSONB NOT NULL DEFAULT '{}',
    last_collected_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(country_code, code)
);

CREATE INDEX idx_sources_country ON sources(country_code);
CREATE INDEX idx_sources_active ON sources(is_active) WHERE is_active = TRUE;
-- ============================================================
-- USERS (single admin)
-- ============================================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'admin' CHECK (role IN ('admin')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- ============================================================
-- PUBLICATIONS (IMMUTABLE)
-- ============================================================
CREATE TABLE publications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       UUID NOT NULL REFERENCES sources(id),
    country_code    CHAR(2) NOT NULL REFERENCES countries(code),
    
    -- Publication metadata
    publication_date DATE NOT NULL,
    title           TEXT NOT NULL,
    section         TEXT,                          -- DOU section (Seção 1, etc.)
    page            TEXT,                          -- Page reference
    url             TEXT NOT NULL,
    external_id     TEXT,                          -- ID from source system
    
    -- Content (immutable once downloaded)
    html_content    TEXT,                          -- Raw HTML (immutable)
    plain_text      TEXT,                          -- Extracted plain text
    checksum_sha256 TEXT,                          -- SHA-256 of HTML content
    
    -- Status tracking
    status          TEXT NOT NULL DEFAULT 'pending_search'
                    CHECK (status IN (
                        'pending_search',
                        'found',
                        'pending_download',
                        'downloaded',
                        'parsing',
                        'parsed',
                        'failed_download',
                        'failed_parse'
                    )),
    
    -- Metadata
    download_attempts INTEGER NOT NULL DEFAULT 0,
    parse_attempts  INTEGER NOT NULL DEFAULT 0,
    metadata        JSONB NOT NULL DEFAULT '{}',
    
    -- Audit
    found_at        TIMESTAMPTZ,
    downloaded_at   TIMESTAMPTZ,
    parsed_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Deduplication
    UNIQUE(source_id, url)
);

CREATE INDEX idx_publications_source ON publications(source_id);
CREATE INDEX idx_publications_country ON publications(country_code);
CREATE INDEX idx_publications_date ON publications(publication_date DESC);
CREATE INDEX idx_publications_status ON publications(status);
CREATE INDEX idx_publications_checksum ON publications(checksum_sha256) WHERE checksum_sha256 IS NOT NULL;
CREATE INDEX idx_publications_url ON publications(url);
CREATE INDEX idx_publications_date_status ON publications(publication_date, status);
CREATE INDEX idx_publications_search ON publications USING gin(
    setweight(to_tsvector('portuguese', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('portuguese', COALESCE(plain_text, '')), 'B')
);
-- ============================================================
-- JOBS (ingestion job tracking)
-- ============================================================
CREATE TABLE jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type        TEXT NOT NULL CHECK (job_type IN (
                        'ingestion', 'historical_import', 'reparse', 'backup'
                    )),
    source_id       UUID REFERENCES sources(id),
    country_code    CHAR(2) REFERENCES countries(code),
    
    -- Parameters
    date_from       DATE,
    date_to         DATE,
    config          JSONB NOT NULL DEFAULT '{}',
    
    -- Status
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN (
                        'pending', 'running', 'completed', 'failed', 'cancelled'
                    )),
    
    -- Progress
    total_items     INTEGER NOT NULL DEFAULT 0,
    processed_items INTEGER NOT NULL DEFAULT 0,
    failed_items    INTEGER NOT NULL DEFAULT 0,
    skipped_items   INTEGER NOT NULL DEFAULT 0,
    checkpoint      JSONB,                         -- resumable state
    
    -- Timing
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    
    -- Results
    result_summary  JSONB NOT NULL DEFAULT '{}',
    error_message   TEXT,
    
    -- Audit
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON jobs(status) WHERE status IN ('pending', 'running');
CREATE INDEX idx_jobs_type ON jobs(job_type);
CREATE INDEX idx_jobs_source ON jobs(source_id);
CREATE INDEX idx_jobs_created ON jobs(created_at DESC);
CREATE INDEX idx_jobs_country_date ON jobs(country_code, date_from);
-- ============================================================
-- LOGS (system and crawler logs)
-- ============================================================
CREATE TABLE logs (
    id              BIGSERIAL PRIMARY KEY,
    job_id          UUID REFERENCES jobs(id),
    level           TEXT NOT NULL CHECK (level IN ('debug', 'info', 'warning', 'error', 'critical')),
    category        TEXT NOT NULL,                 -- 'crawler', 'parser', 'resolver', 'system'
    message         TEXT NOT NULL,
    details         JSONB NOT NULL DEFAULT '{}',
    
    -- Context
    url             TEXT,                          -- URL being processed (if applicable)
    publication_id  UUID REFERENCES publications(id),
    
    -- Timing
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_logs_job ON logs(job_id);
CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_category ON logs(category);
CREATE INDEX idx_logs_created ON logs(created_at DESC);
CREATE INDEX idx_logs_publication ON logs(publication_id) WHERE publication_id IS NOT NULL;
-- ============================================================
-- AI EXTRACTIONS (versioned audit trail)
-- ============================================================
CREATE TABLE ai_extractions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    publication_id  UUID NOT NULL REFERENCES publications(id),
    job_id          UUID REFERENCES jobs(id),
    
    -- AI details
    model           TEXT NOT NULL,                 -- e.g., 'gpt-4', 'llama-3'
    prompt          TEXT NOT NULL,                 -- Full prompt sent to model
    response        TEXT NOT NULL,                 -- Full response from model
    temperature     REAL,
    max_tokens      INTEGER,
    
    -- Results
    extracted_fields JSONB NOT NULL DEFAULT '{}',  -- Structured extraction result
    confidence      REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    text_spans      JSONB NOT NULL DEFAULT '[]',   -- [{text, offset, field_name}]
    
    -- Versioning
    version         INTEGER NOT NULL DEFAULT 1,
    is_current      BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Timing
    duration_ms     INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
3.3 Entity Graph — Node Tables
-- ============================================================
-- COMPANIES (drug registration holders)
-- ============================================================
CREATE TABLE companies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    tax_id          TEXT,                          -- CNPJ (Brazil)
    tax_id_country  CHAR(2),                       -- Country of tax ID
    country_code    CHAR(2) REFERENCES countries(code),
    
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_job_id UUID REFERENCES jobs(id)
);
-- ============================================================
-- MANUFACTURERS
-- ============================================================
CREATE TABLE manufacturers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    tax_id          TEXT,
    tax_id_country  CHAR(2),
    country_code    CHAR(2) REFERENCES countries(code),
    
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_job_id UUID REFERENCES jobs(id)
);

CREATE INDEX idx_manufacturers_name_trgm ON manufacturers USING gin(name_normalized gin_trgm_ops);
CREATE INDEX idx_manufacturers_tax_id ON manufacturers(tax_id) WHERE tax_id IS NOT NULL;
CREATE INDEX idx_manufacturers_country ON manufacturers(country_code);
CREATE INDEX idx_manufacturers_active ON manufacturers(is_active, deleted_at) WHERE is_active = TRUE AND deleted_at IS NULL;
-- ============================================================
-- SITES (manufacturing facilities)
-- ============================================================
CREATE TABLE sites (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manufacturer_id UUID NOT NULL REFERENCES manufacturers(id),
    name            TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    address_id      UUID REFERENCES addresses(id),
    country_code    CHAR(2) REFERENCES countries(code),
    
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_job_id UUID REFERENCES jobs(id)
);

CREATE INDEX idx_sites_manufacturer ON sites(manufacturer_id);
CREATE INDEX idx_sites_address ON sites(address_id) WHERE address_id IS NOT NULL;
CREATE INDEX idx_sites_name_trgm ON sites USING gin(name_normalized gin_trgm_ops);
CREATE INDEX idx_sites_country ON sites(country_code);
CREATE INDEX idx_sites_active ON sites(is_active, deleted_at) WHERE is_active = TRUE AND deleted_at IS NULL;
-- ============================================================
-- ADDRESSES
-- ============================================================
CREATE TABLE addresses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_address     TEXT NOT NULL,
    normalized_hash TEXT NOT NULL UNIQUE,          -- Hash of normalized address
    street          TEXT,
    city            TEXT,
    state           TEXT,
    postal_code     TEXT,
    country_code    CHAR(2) REFERENCES countries(code),
    
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_job_id UUID REFERENCES jobs(id)
);

CREATE INDEX idx_addresses_hash ON addresses(normalized_hash);
CREATE INDEX idx_addresses_city ON addresses(city);
CREATE INDEX idx_addresses_country ON addresses(country_code);
CREATE INDEX idx_addresses_search ON addresses USING gin(
    to_tsvector('portuguese', COALESCE(raw_address, ''))
);
-- ============================================================
-- PRODUCTS (drug brand names)
-- ============================================================
CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_name      TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    company_id      UUID REFERENCES companies(id),
    country_code    CHAR(2) REFERENCES countries(code),
    
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_job_id UUID REFERENCES jobs(id)
);

CREATE INDEX idx_products_name_trgm ON products USING gin(name_normalized gin_trgm_ops);
CREATE INDEX idx_products_company ON products(company_id) WHERE company_id IS NOT NULL;
CREATE INDEX idx_products_country ON products(country_code);
CREATE INDEX idx_products_active ON products(is_active, deleted_at) WHERE is_active = TRUE AND deleted_at IS NULL;
-- ============================================================
-- ACTIVE INGREDIENTS
-- ============================================================
CREATE TABLE active_ingredients (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inn_name        TEXT NOT NULL,                 -- International Nonproprietary Name
    name_normalized TEXT NOT NULL,
    inn_code        TEXT,                          -- WHO INN code if available
    country_code    CHAR(2) REFERENCES countries(code),
    
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_job_id UUID REFERENCES jobs(id)
);

CREATE INDEX idx_active_ingredients_name_trgm ON active_ingredients USING gin(name_normalized gin_trgm_ops);
CREATE INDEX idx_active_ingredients_inn ON active_ingredients(inn_code) WHERE inn_code IS NOT NULL;
CREATE INDEX idx_active_ingredients_active ON active_ingredients(is_active, deleted_at) WHERE is_active = TRUE AND deleted_at IS NULL;
-- ============================================================
-- PRESENTATIONS (strength + form + package)
-- ============================================================
CREATE TABLE presentations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id      UUID NOT NULL REFERENCES products(id),
    strength        TEXT NOT NULL,                 -- e.g., '500mg'
    dosage_form_id  UUID REFERENCES dosage_forms(id),
    package_description TEXT NOT NULL,             -- e.g., '20 comprimidos'
    package_type_id UUID REFERENCES package_types(id),
    
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_job_id UUID REFERENCES jobs(id),
    
    UNIQUE(product_id, strength, dosage_form_id, package_description)
);
CREATE INDEX idx_presentations_product ON presentations(product_id);
CREATE INDEX idx_presentations_form ON presentations(dosage_form_id) WHERE dosage_form_id IS NOT NULL;
CREATE INDEX idx_presentations_active ON presentations(is_active, deleted_at) WHERE is_active = TRUE AND deleted_at IS NULL;
-- ============================================================
-- REGISTRATIONS
-- ============================================================
CREATE TABLE registrations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registration_number TEXT NOT NULL,
    process_number  TEXT,
    company_id      UUID REFERENCES companies(id),
    product_id      UUID REFERENCES products(id),
    country_code    CHAR(2) NOT NULL REFERENCES countries(code),
    authority_id    UUID REFERENCES authorities(id),
    
    registration_type TEXT,                        -- 'new', 'variation', 'renewal', 'cancellation'
    status          TEXT,                          -- 'active', 'cancelled', 'expired', 'suspended'
    resolution      TEXT,                          -- Resolution number
    granted_date    DATE,
    expiry_date     DATE,
    
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_job_id UUID REFERENCES jobs(id)
);

CREATE INDEX idx_registrations_number ON registrations(registration_number);
CREATE INDEX idx_registrations_process ON registrations(process_number) WHERE process_number IS NOT NULL;
CREATE INDEX idx_registrations_company ON registrations(company_id) WHERE company_id IS NOT NULL;
CREATE INDEX idx_registrations_product ON registrations(product_id) WHERE product_id IS NOT NULL;
CREATE INDEX idx_registrations_country ON registrations(country_code);
CREATE INDEX idx_registrations_status ON registrations(status);
CREATE INDEX idx_registrations_active ON registrations(is_active, deleted_at) WHERE is_active = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_registrations_number_trgm ON registrations USING gin(registration_number gin_trgm_ops);
-- ============================================================
-- CERTIFICATES (GMP / CBPF)
-- ============================================================
CREATE TABLE certificates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_number TEXT NOT NULL,
    certificate_type TEXT NOT NULL,                -- 'gmp', 'cbpf', 'bpf'
    country_code    CHAR(2) NOT NULL REFERENCES countries(code),
    authority_id    UUID REFERENCES authorities(id),
    
    issued_date     DATE,
    expiry_date     DATE,
    status          TEXT DEFAULT 'active' CHECK (status IN ('active', 'expired', 'suspended', 'cancelled')),
    
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_job_id UUID REFERENCES jobs(id)
);

CREATE INDEX idx_certificates_number ON certificates(certificate_number);
CREATE INDEX idx_certificates_type ON certificates(certificate_type);
CREATE INDEX idx_certificates_country ON certificates(country_code);
CREATE INDEX idx_certificates_status ON certificates(status);
CREATE INDEX idx_certificates_active ON certificates(is_active, deleted_at) WHERE is_active = TRUE AND deleted_at IS NULL;
-- ============================================================
-- THERAPEUTIC CLASSES
-- ============================================================
CREATE TABLE therapeutic_classes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    atc_code        TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    level           INTEGER NOT NULL,             -- ATC level (1-5)
    parent_id       UUID REFERENCES therapeutic_classes(id),
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_therapeutic_classes_atc ON therapeutic_classes(atc_code);
CREATE INDEX idx_therapeutic_classes_parent ON therapeutic_classes(parent_id) WHERE parent_id IS NOT NULL;
-- ============================================================
-- DOSAGE FORMS
-- ============================================================
CREATE TABLE dosage_forms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- ============================================================
-- PACKAGE TYPES
-- ============================================================
CREATE TABLE package_types (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
3.4 Entity Graph — Edges & Resolution
-- ============================================================
-- EDGES (unified relationship table with provenance)
-- ============================================================
CREATE TABLE edges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source node
    source_node_type TEXT NOT NULL,
    source_node_id  UUID NOT NULL,
    
    -- Edge type
    edge_type       TEXT NOT NULL,
    
    -- Target node
    target_node_type TEXT NOT NULL,
    target_node_id  UUID NOT NULL,
    
    -- PROVENANCE (mandatory)
    source_publication_id UUID NOT NULL REFERENCES publications(id),
    text_span       TEXT,                          -- Exact text from publication
    text_span_offset INTEGER,                      -- Character offset in plain_text
    extraction_method TEXT NOT NULL CHECK (extraction_method IN ('regex', 'xpath', 'html_parser', 'ai', 'manual')),
    confidence      REAL NOT NULL DEFAULT 1.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    ai_extraction_id UUID REFERENCES ai_extractions(id),
    
    -- Temporal
    asserted_date   DATE,                          -- When relationship became effective
    expiry_date     DATE,                          -- When relationship ends (if known)
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at  TIMESTAMPTZ,
    
    -- Properties (edge-specific data)
    properties      JSONB NOT NULL DEFAULT '{}',
    
    -- Audit
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_job_id UUID REFERENCES jobs(id),
    
    -- Uniqueness: same relationship from same publication is deduplicated
    UNIQUE(source_node_type, source_node_id, edge_type, target_node_type, target_node_id, source_publication_id)
);

-- Core traversal indexes
CREATE INDEX idx_edges_source ON edges(source_node_type, source_node_id);
CREATE INDEX idx_edges_target ON edges(target_node_type, target_node_id);
CREATE INDEX idx_edges_type ON edges(edge_type);
CREATE INDEX idx_edges_publication ON edges(source_publication_id);
CREATE INDEX idx_edges_active ON edges(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_edges_confidence ON edges(confidence);
CREATE INDEX idx_edges_method ON edges(extraction_method);
CREATE INDEX idx_edges_job ON edges(created_by_job_id) WHERE created_by_job_id IS NOT NULL;
CREATE INDEX idx_edges_created ON edges(created_at DESC);
CREATE INDEX idx_edges_asserted ON edges(asserted_date DESC) WHERE asserted_date IS NOT NULL;

-- Composite indexes for common traversals
CREATE INDEX idx_edges_source_type_active ON edges(source_node_type, source_node_id, edge_type) WHERE is_active = TRUE;
CREATE INDEX idx_edges_target_type_active ON edges(target_node_type, target_node_id, edge_type) WHERE is_active = TRUE;
-- ============================================================
-- ENTITY ALIASES (for resolution)
-- ============================================================
CREATE TABLE entity_aliases (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type       TEXT NOT NULL,                 -- 'company', 'manufacturer', 'product', etc.
    node_id         UUID NOT NULL,
    alias_name      TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,
    
    first_seen_publication_id UUID REFERENCES publications(id),
    confidence      REAL NOT NULL DEFAULT 1.0,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(node_type, normalized_alias)
);

CREATE INDEX idx_entity_aliases_node ON entity_aliases(node_type, node_id);
CREATE INDEX idx_entity_aliases_normalized ON entity_aliases USING gin(normalized_alias gin_trgm_ops);
CREATE INDEX idx_entity_aliases_exact ON entity_aliases(node_type, normalized_alias);
-- ============================================================
-- ENTITY MERGES (reversible)
-- ============================================================
CREATE TABLE entity_merges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    surviving_node_type TEXT NOT NULL,
    surviving_node_id UUID NOT NULL,
    
    merged_node_type TEXT NOT NULL,
    merged_node_id  UUID NOT NULL,
    
    reason          TEXT NOT NULL,
    confidence      REAL NOT NULL DEFAULT 1.0,
    source_publication_id UUID REFERENCES publications(id),
    
    merged_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    merged_by_job_id UUID REFERENCES jobs(id),
    reversed_at     TIMESTAMPTZ,
    reverse_reason  TEXT
);

CREATE INDEX idx_merges_surviving ON entity_merges(surviving_node_type, surviving_node_id);
CREATE INDEX idx_merges_merged ON entity_merges(merged_node_type, merged_node_id);
CREATE INDEX idx_merges_active ON entity_merges(reversed_at) WHERE reversed_at IS NULL;
3.5 Search
-- ============================================================
-- SEARCH INDEX (denormalized for fast global search)
-- ============================================================
CREATE TABLE search_index (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type       TEXT NOT NULL,
    node_id         UUID NOT NULL,
    display_name    TEXT NOT NULL,
    search_vector   TSVECTOR NOT NULL,
    country_code    CHAR(2),
    
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(node_type, node_id)
);

CREATE INDEX idx_search_vector ON search_index USING gin(search_vector);
CREATE INDEX idx_search_type ON search_index(node_type);
CREATE INDEX idx_search_country ON search_index(country_code) WHERE country_code IS NOT NULL;
CREATE INDEX idx_search_name_trgm ON search_index USING gin(display_name gin_trgm_ops);
4. TRIGGERS & FUNCTIONS
-- Auto-update updated_at
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN
        SELECT unnest(ARRAY[
            'countries', 'authorities', 'sources', 'users',
            'publications', 'jobs',
            'companies', 'manufacturers', 'sites', 'products',
            'active_ingredients', 'presentations', 'registrations',
            'certificates'
        ])
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at()',
            tbl, tbl
        );
    END LOOP;
END $$;
-- Search index update trigger
CREATE OR REPLACE FUNCTION fn_update_search_index()
RETURNS TRIGGER AS $$
BEGIN
    -- This is called by application code after node upserts
    -- to refresh the search index for the affected entity.
    -- Implementation in application layer for flexibility.
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
5. VIEWS FOR COMMON TRAVERSALS
-- Company timeline: all events related to a company
CREATE OR REPLACE VIEW v_company_timeline AS
SELECT
    c.id AS company_id,
    c.name AS company_name,
    e.edge_type,
    e.asserted_date,
    e.source_publication_id,
    p.publication_date,
    p.title AS publication_title,
    p.url AS publication_url,
    e.confidence,
    e.extraction_method
FROM companies c
JOIN edges e ON (
    (e.source_node_type = 'company' AND e.source_node_id = c.id)
    OR (e.target_node_type = 'company' AND e.target_node_id = c.id)
)
JOIN publications p ON p.id = e.source_publication_id
WHERE c.is_active = TRUE AND c.deleted_at IS NULL AND e.is_active = TRUE
ORDER BY p.publication_date DESC;

-- Registration details with all linked entities
CREATE OR REPLACE VIEW v_registration_details AS
SELECT
    r.id AS registration_id,
    r.registration_number,
    r.process_number,
    r.status AS registration_status,
    r.granted_date,
    r.expiry_date,
    r.resolution,
    comp.name AS company_name,
    comp.id AS company_id,
    prod.brand_name AS product_name,
    prod.id AS product_id,
    auth.name_short AS authority_name,
    ctr.name AS country_name
FROM registrations r
LEFT JOIN companies comp ON comp.id = r.company_id
LEFT JOIN products prod ON prod.id = r.product_id
LEFT JOIN authorities auth ON auth.id = r.authority_id
LEFT JOIN countries ctr ON ctr.code = r.country_code
WHERE r.is_active = TRUE AND r.deleted_at IS NULL;
6. MIGRATION STRATEGY
Migrations are numbered sequentially: 001_initial_schema.sql, 002_seed_countries.sql
Every migration includes both UP and DOWN scripts
Migrations are idempotent where possible (using IF NOT EXISTS, ON CONFLICT)
No destructive changes to existing columns
Schema changes preserve all historical records
Run via Supabase dashboard or supabase db push

---

## 📄 File 4: `ROADMAP.md`

```markdown
# ROADMAP
# Brazil Pharma Intelligence Platform
# Version: 1.0.0

---

## PHASE 0: FOUNDATION (Week 1)

### Milestone 0.1: Project Setup ✅ CURRENT
- [x] GitHub repository created
- [x] Five permanent documents written
- [ ] Supabase project created
- [ ] Database schema deployed (Migration 001)
- [ ] Seed data: countries, authorities, sources
- [ ] Backend project initialized (FastAPI)
- [ ] Frontend project initialized (Next.js)
- [ ] Docker Compose for local development
- [ ] CI/CD pipeline (GitHub Actions)

### Milestone 0.2: Authentication & Shell
- [ ] Single-user login (password-protected)
- [ ] Backend auth middleware
- [ ] Frontend login page
- [ ] Protected routes
- [ ] Basic layout (sidebar, header, content area)

---

## PHASE 1: INGESTION PIPELINE (Weeks 2-3)

### Milestone 1.1: Collector Framework
- [ ] Base collector abstract class
- [ ] Job creation and tracking
- [ ] Log system
- [ ] Checkpoint/resume mechanism
- [ ] Error handling and retry logic

### Milestone 1.2: Brazil DOU Collector
- [ ] IN.gov.br search implementation
- [ ] ANVISA section filtering
- [ ] Publication URL extraction
- [ ] Deduplication (by URL + checksum)
- [ ] Rate limiting and robots.txt compliance

### Milestone 1.3: HTML Download & Storage
- [ ] HTML downloader with retry
- [ ] Checksum computation (SHA-256)
- [ ] Plain text extraction
- [ ] Publication status transitions
- [ ] Immutable storage verification

### Milestone 1.4: ANVISA Parser
- [ ] Registration extraction (regex + XPath)
- [ ] Company name extraction
- [ ] Manufacturer extraction
- [ ] Product/ingredient extraction
- [ ] Certificate/inspection extraction
- [ ] Confidence scoring per field
- [ ] Parser test suite with real publications

### Milestone 1.5: Entity Resolution
- [ ] Name normalization (Portuguese)
- [ ] CNPJ validation and matching
- [ ] Fuzzy matching (trigram similarity)
- [ ] Alias tracking
- [ ] Merge queue for low-confidence matches
- [ ] Node upsert logic
- [ ] Edge creation with provenance

---

## PHASE 2: HISTORICAL IMPORT (Week 4)

### Milestone 2.1: Bulk Import Pipeline
- [ ] Date range iterator (2018-01-01 to present)
- [ ] Checkpoint after each day
- [ ] Resume from last checkpoint
- [ ] Progress tracking and ETA
- [ ] Error recovery (skip failed days, log errors)
- [ ] Statistics: total publications, entities, edges

---

## PHASE 3: USER INTERFACE (Weeks 5-6)

### Milestone 3.1: Dashboard
- [ ] Today's publications count
- [ ] New registrations (last 7/30 days)
- [ ] New inspections / certificates
- [ ] Failed inspections
- [ ] Pending extraction queue
- [ ] Average extraction confidence
- [ ] Error summary
- [ ] Recent searches

### Milestone 3.2: Entity Browser
- [ ] Company list with search/filter
- [ ] Manufacturer list
- [ ] Site list
- [ ] Product list
- [ ] Active ingredient list
- [ ] Registration list

### Milestone 3.3: Entity Detail + Timeline
- [ ] Company detail page
- [ ] Full chronological timeline
- [ ] Linked publications (with source links)
- [ ] Graph neighborhood visualization
- [ ] Related entities sidebar

### Milestone 3.4: Publication Browser
- [ ] All publications list
- [ ] Filter by date, status, source
- [ ] Publication detail with raw HTML viewer
- [ ] Extracted entities from publication
- [ ] Link to original IN.gov.br page

### Milestone 3.5: Global Search
- [ ] Search bar (always visible)
- [ ] Search across all node types
- [ ] Faceted results (by type, country, date)
- [ ] Result highlighting
- [ ] Every result links to original publication

### Milestone 3.6: Graph View
- [ ] Interactive graph visualization
- [ ] Node selection and expansion
- [ ] Edge labels and provenance
- [ ] Zoom and pan
- [ ] Export graph as image

---

## PHASE 4: REPORTS (Week 7)

### Milestone 4.1: Report Generation
- [ ] Company Report (HTML + PDF)
- [ ] Manufacturer Report
- [ ] Site Report
- [ ] Drug/Product Report
- [ ] Active Ingredient Report
- [ ] Timeline Report (custom date range)
- [ ] Every report links to source publications
- [ ] Reproducible (same input → same output)

---

## PHASE 5: ADMIN & OPERATIONS (Week 8)

### Milestone 5.1: Admin Panel
- [ ] Manual ingestion trigger (by date range)
- [ ] Job monitoring (status, progress, errors)
- [ ] Log viewer (filterable)
- [ ] Entity merge review queue
- [ ] System health dashboard
- [ ] Backup trigger and status

### Milestone 5.2: Automated Operations
- [ ] Daily scheduled ingestion (cron)
- [ ] Nightly database backup
- [ ] Health check endpoint
- [ ] Error alerting (in-app)

---

## PHASE 6: EXPANSION (Future)

### Milestone 6.1: Mexico
- [ ] COFEPRIS collector
- [ ] Mexican parser
- [ ] Spanish text normalization

### Milestone 6.2: Argentina
- [ ] ANMAT collector
- [ ] Argentine parser

### Milestone 6.3: Colombia
- [ ] INVIMA collector
- [ ] Colombian parser

---

## ONGOING

- Parser improvements (re-parse old publications)
- Entity resolution tuning
- Performance optimization
- New report types
- Graph visualization enhancements
