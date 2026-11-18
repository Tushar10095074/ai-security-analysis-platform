# AI Security Analysis Platform

A reusable, production-oriented foundation for ingesting normalized security events. Cloud resources and billing are intentionally deferred while local development is completed.

## Current capabilities

- FastAPI service with `/`, `/health`, `/ready`, `/docs`, and `/api/v1/events` endpoints.
- Canonical, strict Pydantic security event schema.
- HTTP 202 event acknowledgement and local event lookup.
- Docker image using a non-root runtime user.
- GitHub Actions CI: Ruff, pytest, Bandit, and pip-audit.

> The current event store is in-memory for local development only. It is not durable, multi-worker safe, or production storage.

## Local setup

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

## Run the API

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080/docs` for interactive API documentation.

## Run checks

```bash
ruff check .
pytest
bandit -q -r app
pip-audit -r requirements-dev.txt
```

## Run with Docker

```bash
docker build -t security-ai-platform:local .
docker run --rm -p 8080:8080 security-ai-platform:local
```

## Example event

```bash
curl -X POST http://127.0.0.1:8080/api/v1/events \
  -H 'Content-Type: application/json' \
  -d '{
    "source": "security_command_center",
    "source_event_id": "finding-123",
    "event_type": "vulnerability",
    "severity": "high",
    "title": "Publicly exposed vulnerable VM",
    "description": "A production VM has a publicly reachable vulnerable service.",
    "resource": {
      "provider": "gcp",
      "resource_type": "compute.googleapis.com/Instance",
      "resource_id": "projects/demo/zones/us-east1-b/instances/web-01",
      "project_id": "demo-project",
      "region": "us-east1"
    },
    "observed_at": "2026-11-17T10:00:00+05:30"
  }'
```

## Cloud deployment

Not configured or deployed yet. Do not run Terraform apply or create cloud resources until the GCP project, billing, IAM, region, and expected costs have been explicitly reviewed and approved.
