# MEP Testing Strategy

## Overview

The Migration Evaluation Platform uses a multi-layered testing approach
covering unit, integration, API, and data-quality levels. Tests run
automatically in CI on every push and pull request.

## Test Pyramid

```
        ┌──────────┐
        │  E2E/UI  │   Planned: Playwright
        ├──────────┤
        │  API     │   38 tests (pytest + TestClient)
        ├──────────┤
        │  Unit    │   Service-level logic tests
        └──────────┘
```

## Test Stack

| Layer | Tool | Location |
|-------|------|----------|
| Backend API tests | pytest + FastAPI TestClient | `backend/tests/` |
| Frontend type check | TypeScript (`npm run build`) | `frontend/` |
| CI pipeline | GitHub Actions | `.github/workflows/ci.yml` |
| Original engine tests | pytest + SQL assertions | `backend/migration/tests/` |

## Backend Test Architecture

### Database

Tests use **SQLite** (file-based, not in-memory) so they run without
PostgreSQL. A shared `conftest.py` configures:

- A single `test_engine` + `TestSession`
- Dependency override: `app.dependency_overrides[get_db]`
- `autouse` fixture that creates tables before each test and drops them after
- Temporary upload/report directories via `tempfile.mkdtemp()`

### Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `test_health.py` | 2 | Root route, health endpoint |
| `test_migrations.py` | 17 | CRUD runs, file upload, metadata parsing, 404s |
| `test_schema_validation.py` | 19 | Schema inference (int/decimal/date/bool/text), nullability, uniqueness, sample values, validation checks (duplicates, nulls, duplicate columns), dashboard stats |

**Total: 38 tests**

### Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

### What the Tests Cover

#### Migration Run CRUD
- Create run (full / minimal / invalid name)
- List runs (empty / populated)
- Get run (found / not found)
- Delete run (found / not found / cascading file deletion)

#### File Upload
- Single file upload with metadata extraction
- Multi-file upload
- Upload to nonexistent run (404)
- File listing and deletion
- File count / total size aggregation on run

#### Schema Discovery
- Integer, decimal, date, boolean, text type inference
- Nullable detection with null counts
- Uniqueness detection
- Sample values capping (max 5)

#### Validation Checks
- Clean CSV passes all checks
- Null values generate appropriate severity warnings
- Duplicate rows produce warnings
- Duplicate column names produce errors
- Empty runs handled gracefully
- Multi-file validation with summary counts

#### Dashboard
- Empty dashboard stats
- Stats with runs and files
- Row count and size aggregation

## Data-Quality Validation Checks

The validation engine (`services/schema_service.py`) implements 5 automated checks:

| Check | Severity | Description |
|-------|----------|-------------|
| `duplicate_column` | Error | Column name appears more than once in header |
| `empty_column_name` | Error | Column header is blank or whitespace-only |
| `null_values` | Error/Warning/Info | Null/empty values with severity based on percentage (>50% error, >10% warning, else info) |
| `duplicate_rows` | Warning | Identical data rows detected |
| `mixed_types` | Warning | Column has both numeric and text values |

## Evaluation Quality Checks

The evaluation engine (`services/evaluation_service.py`) compares source CSVs
against loaded PostgreSQL staging tables:

| Check | Scoring Impact | Description |
|-------|---------------|-------------|
| Row count match | Up to -30 points | Source vs target row counts |
| Null percentage | Up to -20 points | Average null % across columns |
| Duplicate rows | Up to -10 points | Duplicate row groups in target |

**Overall score:** 0–100, **PASS** ≥ 70, **FAIL** < 70.

## CI/CD Integration

The GitHub Actions pipeline runs:

1. **Backend Tests** — `pytest tests/ -v` on Python 3.11
2. **Frontend Build** — `npm ci && npm run build` on Node 20
3. **Docker Build** — `docker compose build` (depends on both above passing)

## Future Testing Plans

- **Playwright E2E tests** — automated browser tests for the full upload → validate → migrate → report flow
- **Performance tests** — using k6 for load testing the upload and migration endpoints
- **Migration engine integration tests** — connecting the original engine's 85 SQL assertions to the new API layer
