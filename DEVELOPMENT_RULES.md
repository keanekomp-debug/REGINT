# DEVELOPMENT RULES
# Brazil Pharma Intelligence Platform
# Version: 1.0.0
# These rules are NON-NEGOTIABLE.

---

## 1. CODE QUALITY

- No duplicated code.
- No hardcoded values.
- No magic numbers.
- No TODO comments.
- No placeholder functions.
- No mock data.
- No fake APIs.
- No example data.
- Everything must be production ready.
- PEP8 compliant (Python).
- ESLint compliant (TypeScript).
- Strong typing everywhere.
- Modular architecture.
- Reusable services.
- Unit tests for all logic.
- Fully documented.

---

## 2. DATABASE INTEGRITY

- Every database migration must be reversible (UP + DOWN).
- Every schema change must preserve historical records.
- Never delete data. Soft deletes only (`deleted_at`).
- Never overwrite source data. Publications are immutable.
- All source publications are immutable once downloaded.
- All AI extractions are versioned.
- Every entity relationship is auditable (provenance on every edge).
- Every merge is reversible (entity_merges table).
- Every database model must have indexes on foreign keys, search fields, and filter columns.

---

## 3. TESTING

- Every API endpoint must have tests.
- Tests must use real logic, not mocks.
- Integration tests against test database.
- Parser tests against real publication HTML samples.

---

## 4. BACKGROUND WORKERS

- Every background worker must be resumable (checkpoint-based).
- Every scheduled task must survive server restart.
- Job state persisted in database, not memory.
- Idempotent operations (re-running produces no duplicates).

---

## 5. LOGGING

- Every exception must be logged (full stack trace + context).
- Every crawler action must be logged (URL, status, duration, bytes).
- Every AI extraction must record:
  - Prompt (full input to model)
  - Model (name + version)
  - Confidence (0.0 to 1.0)
  - Timestamp (ISO 8601)
  - Text span citations (exact source text used)
- Every parser action must be logged.
- Every entity resolution decision must be logged.

---

## 6. OUTPUT STANDARDS

- Every report must be reproducible (same inputs → same output).
- Every search result must link back to the original government publication.
- Every entity detail must show source publications with direct URLs.
- Every timeline entry must be traceable to a specific publication.

---

## 7. ENTITY GRAPH RULES

- The Entity Graph is the product.
- Every fact is a node or an edge.
- Every publication enriches the graph.
- Nothing is duplicated (entity resolution before insert).
- Everything is connected (every node reachable via edges).
- Every edge has provenance (source publication + text span + confidence + method).
- Aliases are tracked.
- Merges are logged and reversible.

---

## 8. PIPELINE RULES

- Pipeline is unidirectional: Country → Source → Collector → Date → Search → Results → Publication → HTML → Parser → Entities → Relationships.
- Pipeline is date-driven.
- Pipeline is resumable at every stage.
- Pipeline is idempotent.
- HTML is stored before parsing (never modifies source).
- Parser uses regex/XPath first; AI only for unparseable fields.

---

## 9. SECURITY

- Single user. Password protected.
- No public access.
- No API keys in client code.
- All endpoints authenticated.

---

## 10. EXPANSION

- Adding a new country requires ONLY a new collector.
- Zero database schema changes for new countries.
- Zero API changes for new countries.
- Collector is the only country-specific code.
