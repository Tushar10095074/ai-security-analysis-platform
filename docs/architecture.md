# Foundation architecture

This repository begins with a provider-neutral FastAPI boundary for normalized security events.

## Current local foundation

- FastAPI exposes liveness, readiness, service metadata, event submission, and event retrieval.
- Pydantic validates a canonical event envelope and rejects unknown fields.
- Event submission returns HTTP 202 with an event identifier.
- Events, risk assessments, and AI analyses are persisted in SQLite (`DATABASE_PATH`, default `data/security.db`) for local, single-node use.
- A deterministic risk engine produces the authoritative score and level; a local `MockAIAnalysisProvider` adds explanatory analysis without changing the score and without calling any external AI service.
- Docker builds a minimal Python 3.14 runtime image and runs as non-root user `app` (UID/GID 1000).
- GitHub Actions runs lint, tests, Bandit, and dependency auditing.

## Planned cloud evolution (not provisioned)

Security sources -> authenticated ingestion API / Pub/Sub -> Cloud Run analysis worker -> context enrichment -> deterministic risk engine + Vertex AI -> persisted assessment and recommendations.

Cloud resources, IAM bindings, billing, and deployment are intentionally deferred. Terraform must be reviewed and approved before any apply.

## Production requirements before go-live

Replace local SQLite with a managed, horizontally scalable store; add idempotency and replay handling; enforce authentication and authorization; configure request size limits at the edge; add rate limiting; validate and redact untrusted evidence; implement structured audit logging; add retries and dead-letter handling; define retention and data residency; and add integration, load, resilience, and security tests.
