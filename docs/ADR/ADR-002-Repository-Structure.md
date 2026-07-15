# ADR-002: Repository Structure

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

MEP adds a frontend, backend, and infrastructure around an existing migration
engine that already lives in this repository. We must decide whether to split
these into multiple repositories or keep a single one, and how to preserve the
existing engine.

## Decision

Adopt a **monorepo** with the following top-level layout:

```
PostgreDataMigrationApp/
├── backend/              # FastAPI application
│   └── migration/        # Existing engine, preserved unchanged
├── frontend/             # React + TypeScript SPA
├── docs/                 # Architecture, guides, ADRs
├── uploads/              # Runtime CSV uploads (gitignored)
├── docker-compose.yml    # Full-stack local orchestration
└── .github/workflows/    # CI/CD
```

The original engine is moved verbatim into `backend/migration/` so its internal
relative paths (`build/`, `evals/`, `infra/`, `tests/`) remain valid.

## Consequences

- Atomic commits can span frontend, backend, and engine together.
- Single clone and one `docker compose up` for the whole stack simplifies onboarding.
- The engine is preserved without code changes, minimizing regression risk.
- A shared CI pipeline covers all components.
- Trade-off: a larger repo and coarser-grained access control than split repos,
  acceptable at the current team size.
