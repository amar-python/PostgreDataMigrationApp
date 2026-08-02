# ARCHITECTURE — PostgreDataMigrationApp

The project is organised into five categories. Every file in the repo belongs to exactly one of them.

```text
PostgreDataMigrationApp/
|
+-- build/             <-- production code that gets deployed (schema, adapters, CSV loader)
+-- tests/             <-- correctness coverage for the production code
+-- evals/             <-- data-driven black-box scenarios
+-- api/               <-- FastAPI REST layer over the CSV pipeline
+-- frontend/          <-- React 19 + TanStack Start web UI (calls the API only)
|
+-- scripts/           <-- launcher and dev helpers (start-api.ps1, start-frontend.ps1, ...)
+-- README.md  LICENSE  ARCHITECTURE.md  .gitignore
```

## Why the split

| Category | Question it answers | Failure means |
|----------|--------------------|---------------|
| **build** | "What do we ship at the DB layer?" | The deployed database is broken |
| **tests** | "Is the code correct?" | Some function has a bug |
| **evals** | "Does it handle real-world data correctly end-to-end?" | A whole-system behaviour regressed |
| **api** | "How does anything outside psql talk to the DB?" | The web UI (and any other client) can't reach the data |
| **frontend** | "How does a human drive the pipeline?" | The browser UI is broken (backend still works via API) |

The five layers can break independently, so we keep them physically separate. Tests live close to the code they verify; evals stay in their own folder because they're driven by data, not code. The API and frontend are new additions from the merge of the earlier `csv-table-hub-main` project — the browser never talks to Postgres directly, only to `api/`.

## What's in each folder

### `build/` — production code

| Path | What it is |
|------|-----------|
| `build/te_core_schema.sql` | PostgreSQL master schema (legacy entry point) |
| `build/te_seed_data.sql` | Seed data |
| `build/csv/` | Python CSV validator (`validator.py`), per-engine shell loaders (`loader_*.sh`), and `samples/` |
| `build/adapters/` | Per-engine deployment adapters (`adapter_postgresql.sh`, `adapter_mariadb.sh`, etc.) |
| `build/schema/` | Engine-specific DDL and seed data |
| `build/environments/` | PostgreSQL per-environment launchers. Only `env_dev.example.sql` is committed; concrete `env_<env>.sql` files are gitignored and created from it. |
| `build/terraform-github-repos/` | GitHub repository management as Infrastructure-as-Code |
| `build/setup.sh` | Interactive multi-database configuration wizard |
| `build/deploy_all.sh` | Multi-engine deployment router |
| `build/csv_loader.sh` | Schema-agnostic CSV ingestion: any CSV → auto-created table |
| `build/csv_utilise.sh` | Companion to the loader: list / describe / peek / export / drop CSV-loaded tables (PostgreSQL) |

### `tests/` — correctness coverage

| Path | What it is |
|------|-----------|
| `tests/framework/test_framework.sql` | Assertion library + results table |
| `tests/suites/test_01..05_*.sql` | 142 SQL assertions across 5 suites |
| `tests/run_all_tests.sql` | Master SQL test orchestrator |
| `tests/run_tests.sh` | Bash wrapper that sources `config.local.env` |
| `tests/run_python_tests.ps1` | Windows runner — invoked by the GitHub Actions workflow |
| `tests/conftest.py` | pytest env-var isolation between tests |
| `tests/test_csv_validator.py` | unittest for `build/csv/validator.py` |
| `tests/test_csv_utilise.py` | unit tests for `build/csv_utilise.sh` argument parsing |
| `tests/test_csv_loader_arbitrary_shapes.py` | integration: arbitrary CSV shapes through loader → PG (skips without PG) |
| `tests/test_e2e_pipeline.py` | e2e: CSV → validate → load → verify (DB half skips without PG) |
| `tests/test_parity.py` | cross-environment row-count / schema parity (skips without PG) |
| `tests/test_regression.py` | pinned tests for previously found bug classes |
| `tests/test_security.py` | static credential/SQL-pattern scans |
| `tests/test_snapshot.py` | golden-file output comparisons (`tests/snapshots/`) |
| `tests/test_evals_runner.py` | unittest for `evals/runner.py` itself |

### `api/` — FastAPI REST layer

| Path | What it is |
|------|-----------|
| `api/main.py` | App entrypoint — CORS, lifespan (pool init/bootstrap/close), health endpoint, optional `require_api_key` global dependency |
| `api/config.py` | Env-var-driven `Settings` (libpq vars, `CORS_ORIGINS`, `API_KEY`, `MAX_UPLOAD_BYTES`, `API_ALLOW_DESTRUCTIVE`) + `TE_TABLES` whitelist |
| `api/db.py` | `psycopg2.pool.SimpleConnectionPool` + `Conn` context manager + `bootstrap()` for the `csv_uploads` schema and `csv_files` registry |
| `api/auth.py` | Optional `X-API-Key` dependency; no-ops when `API_KEY` env var is unset |
| `api/routers/csv_routes.py` | `POST /api/csv/preview`, `POST /api/csv/upload`, `GET /api/csv/files`, `GET /api/csv/tables/{table_name}/rows`, `DELETE /api/csv/files/{id}` |
| `api/routers/te_routes.py` | `GET /api/te/tables` — existence + row counts for the 12 fixed T&E tables |
| `api/services/csv_parse.py` | Pure-Python CSV parser + type inference (mirrors the frontend's original TS logic) |
| `api/services/dynamic_loader.py` | Creates `csv_uploads.csv_<sha256[:16]>` tables from any CSV, with typed columns + `_id`/`_row_hash`/`_created_at` metadata and `ON CONFLICT DO NOTHING` dedup |
| `api/services/te_loader.py` | Validates CSV columns are a subset of a fixed T&E table, then inserts row-by-row with `SAVEPOINT`/`ROLLBACK TO SAVEPOINT` |
| `api/requirements.txt` | `fastapi`, `uvicorn[standard]`, `psycopg2-binary`, `python-multipart`, `pydantic` |

All dynamic SQL uses `psycopg2.sql.Identifier()` / `sql.SQL()` — no f-string interpolation of identifiers (project rule from `CLAUDE.md`).

### `frontend/` — React 19 + TanStack Start UI

| Path | What it is |
|------|-----------|
| `frontend/src/routes/__root.tsx` | Root route + `errorComponent` fallback |
| `frontend/src/routes/_authenticated/route.tsx` | Passthrough layout (auth removed — folder name kept so the generated route tree is unchanged) |
| `frontend/src/routes/_authenticated/index.tsx` | Main CSV Migrator page |
| `frontend/src/lib/csv.functions.ts` | `fetch`-based API client (`uploadCsv`, `listCsvFiles`, `previewCsvTable`, `previewCsvContent`, `listTeTables`, `apiHealth`); sends `X-API-Key` when `VITE_API_KEY` is set |
| `frontend/src/routeTree.gen.ts` | Auto-generated by TanStack Router — do not hand-edit |
| `frontend/vite.config.ts` | Dev server pinned to port `5173` |
| `frontend/.env` | `VITE_API_URL=http://localhost:8000`, optional `VITE_API_KEY=` |
| `frontend/package.json` | React 19, `@tanstack/react-start`, `@tanstack/react-router`, Tailwind v4, shadcn/radix components |

The frontend has **no** Supabase, direct-DB, or `createServerFn` code paths — it only issues `fetch()` calls to the FastAPI backend.

### `evals/` — data-driven scenarios

| Path | What it is |
|------|-----------|
| `evals/PLAN.md` | Scope, layout, phases, tier rationale |
| `evals/USAGE.md` | End-to-end run instructions |
| `evals/FAILURE_MODES.md` | Catalogue of 29 failure modes |
| `evals/USAGE.md` | Quick-start |
| `evals/HANDOFF.md` | What was delivered + next steps |
| `evals/runner.py` | Scenario discovery + diff engine + JSON report writer |
| `evals/datasets/tier_p/*` | 23 CSV scenarios for `build/csv/validator.py` |
| `evals/datasets/tier_i/*` | Idempotency scenarios (run `build/environments/env_dev.sql` twice) |
| `evals/datasets/tier_s/*` | SQL suite integration scenarios |
| `evals/expected/tier_*/*.json` | Expected outcome per scenario |
| `evals/reports/` | Runtime output (gitignored) |

## Dependency direction

```text
frontend/  --reads--->  api/         (HTTP only, via fetch)

api/       --reads--->  PostgreSQL   (psycopg2 pool)
                        NOTHING in build/, tests/, or evals/

evals/     --reads--->  build/csv/validator.py
                        build/environments/env_dev.sql
                        tests/run_all_tests.sql

tests/     --reads--->  build/csv/validator.py
                        evals/runner.py  (just to verify it imports cleanly)

build/     --reads--->  nothing in tests/, evals/, api/, or frontend/
```

`build/` has no dependency on any of the other layers. `api/` and `frontend/` are additive — they consume the deployed database created by `build/`, but neither `build/` nor `tests/`/`evals/` depend on them. That's the property to defend on every change.

## When you add a new file, ask yourself

1. Does this run in production DB deployment? → `build/<engine-or-folder>/`
2. Does this assert that some function is correct? → `tests/`
3. Does this drive a scenario through the deployed system from outside? → `evals/`
4. Is this a REST endpoint or a service the API needs? → `api/`
5. Is this a React component, route, or client-side helper? → `frontend/src/`

If a file would fit two of those, split it — the test belongs in `tests/`, the production code in `build/`, the HTTP handler in `api/`.

## What's not part of any layer

- `README.md`, `LICENSE`, `ARCHITECTURE.md`, `.gitignore` — repo metadata
- `_norton_/`, `extend to Oracle dbs/` — exploratory user folders, not currently wired up
- `scripts/insert_random_test_data.sql` — auxiliary helper not yet categorised

These are left at the repo root and excluded from the layer model. They can move into one of the three folders if their role becomes clear.

## Path conventions inside the layers

- Code inside `evals/runner.py` computes `PROJECT_ROOT = Path(__file__).resolve().parent.parent` and reaches into `build/csv/validator.py`, `build/environments/env_dev.sql`, `tests/run_all_tests.sql` from there.
- Code inside `tests/test_csv_validator.py` does `Path(__file__).resolve().parents[1] / "build" / "csv" / "validator.py"`.
- Shell scripts inside `build/` cd into their own directory and use relative paths (`./adapters/...`, `./schema/...`).
- Nothing in `build/` references `tests/` or `evals/`.

If a new file has to break these rules, document why in this
