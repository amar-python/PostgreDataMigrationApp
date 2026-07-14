# MEP Architecture

The Migration Evaluation Platform (MEP) is a 3-tier web application that wraps
the existing CSV → PostgreSQL migration engine with a modern UI and API.

## Overview

```
┌──────────────┐      HTTP/JSON      ┌──────────────┐      SQL       ┌──────────────┐
│   Frontend   │  ───────────────▶   │   Backend    │  ──────────▶   │  PostgreSQL  │
│ React + MUI  │                     │   FastAPI    │                │   Database   │
│ (nginx :80)  │  ◀───────────────   │  (uvicorn    │  ◀──────────   │   (:5432)    │
│              │      responses      │   :8000)     │     rows       │              │
└──────────────┘                     └──────────────┘                └──────────────┘
```

### 1. Presentation tier — React + TypeScript (`frontend/`)
- Vite-built single-page application styled with Material UI to resemble the
  Azure Portal.
- Served in production by nginx, which also proxies `/api` calls to the backend.

### 2. Application tier — FastAPI (`backend/`)
- Python 3.11 service run with uvicorn on port 8000.
- Exposes the REST API (health today; migration/evaluation/reporting later).
- CORS enabled for local development.
- Configuration is environment-driven via `pydantic-settings` (see `backend/config.py`).

### 3. Data tier — PostgreSQL
- `postgres:15-alpine`, provisioned by Docker Compose with a named volume for
  persistence.

## Migration engine location

The original, battle-tested migration engine is preserved **unchanged** at
`backend/migration/`:

- `backend/migration/build/` — SQL-first, multi-engine framework and the
  CSV → PostgreSQL loader/validator pipeline.
- `backend/migration/evals/` — data-driven black-box scenarios and the runner.
- `backend/migration/infra/` — containerization and Azure Terraform IaC.
- `backend/migration/tests/` — SQL assertions and Python test modules.

The FastAPI backend (`backend/api/`, `backend/services/`) **wraps and
orchestrates** this engine rather than reimplementing its logic.

## Key design decisions

- **Wrap, don't rewrite.** The proven CSV → PostgreSQL engine is retained as-is;
  new value is added around it.
- **Monorepo layout.** Frontend, backend, engine, docs, and infra live in one
  repository for atomic changes and simple onboarding.
- **Container-first.** The whole stack (React + FastAPI + PostgreSQL) is
  reproducible via a single `docker compose up`.
- **Config via environment.** No secrets in code; all runtime config flows
  through environment variables / `.env`.

See the `docs/ADR/` directory for detailed Architecture Decision Records.
