# Migration Evaluation Platform (MEP) v2

> **MEP** is a web application that wraps the existing CSV → PostgreSQL migration engine
> with a **React frontend** and a **FastAPI backend**, turning a powerful CLI/script-based
> tool into an interactive platform for **uploading CSV files, running migrations, and
> evaluating migration quality** (completeness, integrity, business-rule conformance, and
> reconciliation reporting).

[![Status](https://img.shields.io/badge/MEP-v2%20(in%20development)-blueviolet)](#)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](#)
[![Frontend](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=white)](#)
[![Engine](https://img.shields.io/badge/Engine-CSV%20%E2%86%92%20PostgreSQL-336791?logo=postgresql&logoColor=white)](backend/migration/)

## What MEP Is

The **Migration Evaluation Platform** does not replace the proven migration engine — it
**wraps** it. The original, battle-tested SQL-first framework and CSV → PostgreSQL
loader/validator pipeline now lives, unchanged, at **[`backend/migration/`](backend/migration/)**.
The FastAPI backend shells out to / orchestrates that engine rather than reimplementing it,
and a React frontend provides a UI for the full migrate-and-evaluate workflow.

### Repository layout (MEP v2)

```
PostgreDataMigrationApp/
├── backend/
│   ├── api/            FastAPI routes (HTTP layer) — all endpoints declare Pydantic response models
│   ├── services/       Business logic (incl. the hardened CsvParser)
│   ├── migration/      ← ORIGINAL migration engine (build/ evals/ infra/ tests/), preserved
│   ├── evaluation/     Migration-quality evaluation logic
│   ├── reports/        Reconciliation / evaluation report generation
│   ├── database/       MEP metadata models (MigrationRun, UploadedFile, run lifecycle state machine)
│   └── tests/          MEP backend test suite (unit + integration)
├── frontend/           React app
├── tools/              Developer/CI tooling (workflow path verifier)
├── docker/             Dockerfiles / compose
├── docs/               Documentation (incl. docs/security/ and docs/ci/)
├── uploads/            CSV upload staging
└── .github/            CI workflows + pull request template
```

---

## MEP Backend — Reliability & Safety Features

The MEP layer ships with a set of code-quality and operational-safety guarantees
(introduced via PRs [#10](https://github.com/amar-python/PostgreDataMigrationApp/pull/10),
[#11](https://github.com/amar-python/PostgreDataMigrationApp/pull/11), and
[#12](https://github.com/amar-python/PostgreDataMigrationApp/pull/12)):

### Migration run lifecycle (state machine)

Every `MigrationRun` moves through an explicit, enforced state machine defined in
`backend/database/models.py`:

```
CREATED → UPLOADING → VALIDATING → READY → MIGRATING → COMPLETED
              ↓            ↓                    ↓
            ERROR        ERROR               FAILED
```

- States: `CREATED`, `UPLOADING`, `VALIDATING`, `READY`, `MIGRATING`, `COMPLETED`, `FAILED`, `ERROR`
- Transitions are whitelisted in `ALLOWED_TRANSITIONS`; illegal jumps raise
  `InvalidStateTransition` instead of silently corrupting run state
- Failed uploads/validations land in `ERROR`, from which a re-upload can recover
- The dashboard UI colour-codes `ready` and `error` states

### Robust CSV parsing (`backend/services/csv_parser.py`)

Uploads are parsed by a dedicated `CsvParser` service that returns a structured
`CsvParseResult` with per-issue diagnostics instead of crashing:

- Zero-byte / header-only files are rejected with a clear issue message
- Ragged rows (column-count mismatches) are detected and reported
- Encoding fallback: UTF-8 (with/without BOM) first, then latin-1
- Suspicious headers (e.g. SQL metacharacters) are flagged before any data
  reaches the database

### Production safety gate

The backend refuses to start unsafely in production:

- `ALLOW_SCHEMA_AUTO_CREATE` (default `true` for development) controls whether
  startup runs `Base.metadata.create_all`
- If `APP_ENV=production` **and** `ALLOW_SCHEMA_AUTO_CREATE=true`, `Settings`
  validation fails fast at startup — production schema changes must go through
  explicit, reviewed migrations (e.g. Alembic), never auto-creation
- Covered by `backend/tests/test_config_safety.py`

### Typed API responses

Every FastAPI endpoint declares a Pydantic `response_model`
(`backend/api/schemas.py`) — including `/`, `/api/health`, `/api/dashboard`,
execute/evaluate, and report generation. This documents the OpenAPI contract
and filters internal fields (e.g. server filesystem paths are never leaked in
report responses).

### Hardened shell scripts

The CSV loader scripts under `backend/migration/build/` validate their inputs:

- Table names must match `^[a-zA-Z_][a-zA-Z0-9_]*$` and PostgreSQL's 63-char limit
- `--env` values are validated against the known environment list
- `eval` was replaced with safe indirect variable expansion (`${!var}`)

### CI workflow path verification

`tools/verify_workflow_paths.py` (stdlib-only) parses every GitHub Actions
workflow and verifies that all referenced scripts, files, and directories
actually exist in the repository — catching stale paths after refactors before
CI does. It runs as a CI job (staged in `docs/ci/quality-gate.yml`) and locally:

```bash
python3 tools/verify_workflow_paths.py
```

### Security suppression policy

Every `# nosec` / `# noqa` suppression in the codebase is documented with a
technical justification in **[`docs/security/Rationale.md`](docs/security/Rationale.md)**.
New suppressions must add an entry there (enforced via the PR template checklist).

### Running the MEP backend tests

```bash
# From the repo root (backend suite: unit + lifecycle + parser + config safety)
pip install -r backend/requirements.txt -r requirements-dev.txt
python -m pytest backend/tests/

# Integration smoke tests only
python -m pytest backend/tests/ -m integration

# Legacy engine tests
python -m pytest backend/migration/tests/
```

With all three quality PRs applied, the backend suite has grown from 38 to
100+ tests: 28 `CsvParser` tests, run-lifecycle state-machine tests,
7 production-safety-gate tests, and API integration smoke tests — alongside the
original engine's 85 SQL assertions and 23 CSV eval scenarios described below.

> **Original engine:** everything that shipped before MEP — the multi-engine database
> framework, the CSV pipeline, the 23 eval scenarios, the 85 SQL assertions, and the Azure
> IaC — is preserved verbatim under **[`backend/migration/`](backend/migration/README.md)**.
> The documentation below describes that original engine.

---

# T&E Database Framework (original engine — now under `backend/migration/`)

> A fully parameterised, idempotent **PostgreSQL database framework** for **Test & Evaluation (T&E)** programme management — covering TEMP documents, VCRM traceability, test execution, defect reporting, and multi-environment deployment, with a built-in SQL test suite.

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Environments](https://img.shields.io/badge/Environments-Dev%20%7C%20Test%20%7C%20Staging%20%7C%20Prod-blue)](#environment-comparison)
[![Test Suites](https://img.shields.io/badge/Tests-5%20suites%20%7C%2085%20assertions-brightgreen)](#test-suite)
[![Evals](https://img.shields.io/badge/Evals-23%20CSV%20scenarios-brightgreen)](backend/migration/evals/)
[![Terraform](https://img.shields.io/badge/Terraform-1.5%2B-7B42BC?logo=terraform&logoColor=white)](https://developer.hashicorp.com/terraform)

---

## What This Is

This project provides a **production-grade SQL framework** to stand up a T&E management database from scratch — on a single PostgreSQL server or across multiple environments. It is designed to support the full T&E lifecycle as practised in Australian acquisition:

- **Program management** — test programs, TEMP versioning, DT&E / AT&E / OT&E phases
- **Requirement traceability** — system requirements linked to test cases via a VCRM (Verification Cross Reference Matrix)
- **Test execution** — events, results, verdicts, and evidence artefacts
- **Defect reporting** — deficiency reports (DRs) linked directly to failed results
- **Multi-environment isolation** — separate databases, schemas, and users for Dev, Test, Staging, and Prod
- **Automated data testing** — 85 assertions across 5 SQL test suites, all written in pure PostgreSQL
- **Data-driven evals** — 23 offline CSV validator scenarios plus PostgreSQL-backed idempotency and full-suite checks

All names (database, schema, users, every table) are controlled by a single `\set` configuration block at the top of each environment file. Rename anything in one place and the entire script updates automatically.

---

## Who Is This For?

| Role | How you use this |
|---|---|
| **T&E Engineers / Analysts** | Understand the data model — VCRM, TEMP versioning, DR lifecycle |
| **Database Administrators** | Deploy and maintain the schema across isolated environments |
| **DevOps / Platform Engineers** | Plug `deploy_all.sh` and `run_tests.sh` into CI/CD pipelines; manage repos with Terraform |
| **Students / Learners** | Study parameterised SQL, idempotent DDL patterns, SQL-native testing, and Terraform IaC |

---

## Repository Structure

The engine is organised into three categories: `build/` (everything that ships), `tests/` (correctness coverage), `evals/` (data-driven black-box scenarios). See **`ARCHITECTURE.md`** for the rationale.

> **Note:** in MEP v2 the entire engine tree below lives under
> **`backend/migration/`** (e.g. `backend/migration/build/`,
> `backend/migration/tests/`, `backend/migration/evals/`). All commands in the
> sections that follow use the full `backend/migration/...` paths.

```text
backend/migration/
│
├── build/                             ← everything that ships
│   ├── te_core_schema.sql             ← PostgreSQL master schema (legacy entry point)
│   ├── te_seed_data.sql               ← Seed data
│   │
│   ├── adapters/                      ← Engine-specific deployment adapters
│   │   ├── adapter_postgresql.sh
│   │   ├── adapter_mariadb.sh
│   │   ├── adapter_sqlite.sh
│   │   ├── adapter_influxdb.sh
│   │   ├── adapter_redis.sh
│   │   └── adapter_teradata.sh
│   │
│   ├── csv/                           ← Python validator + per-engine loaders
│   │   ├── validator.py
│   │   ├── validator.sh
│   │   └── loader_<engine>.sh
│   │
│   ├── schema/                        ← Engine-specific DDL and seed data
│   │   ├── postgresql/
│   │   │   └── te_core_schema.sql
│   │   ├── mariadb/
│   │   │   └── te_core_schema.sql
│   │   ├── sqlite/
│   │   │   └── te_core_schema.sql
│   │   ├── influxdb/
│   │   │   └── te_seed_data.lp
│   │   ├── redis/
│   │   │   └── te_seed_data.sh
│   │   └── teradata/
│   │       ├── te_core_schema.sql
│   │       └── te_seed_data.sql
│   │
│   ├── environments/                  ← PostgreSQL per-environment launchers
│   │   ├── env_dev.sql
│   │   ├── env_test.sql
│   │   ├── env_staging.sql
│   │   └── env_prod.sql
│   │
│   ├── terraform-github-repos/        ← GitHub repos as Infrastructure as Code
│   │
│   ├── setup.sh                       ← Interactive multi-database configuration wizard
│   └── deploy_all.sh                  ← Multi-engine deployment router
│
├── tests/                             ← correctness coverage for build/
│   ├── framework/
│   │   └── test_framework.sql         ← Assertion library + results table
│   ├── suites/
│   │   ├── test_01_organisations_personnel.sql
│   │   ├── test_02_programs_phases.sql
│   │   ├── test_03_requirements_vcrm.sql
│   │   ├── test_04_execution_defects.sql
│   │   └── test_05_schema_and_business_rules.sql
│   ├── run_all_tests.sql              ← Master SQL test orchestrator
│   ├── run_tests.sh                   ← Bash wrapper (reads config.local.env)
│   ├── run_python_tests.ps1           ← Windows test runner (CI)
│   ├── test_csv_validator.py          ← unittest for build/csv/validator.py
│   └── test_evals_runner.py           ← unittest for evals/runner.py
│
├── evals/                             ← data-driven black-box scenarios
│   ├── PLAN.md  USAGE.md  FAILURE_MODES.md  README.md  HANDOFF.md
│   ├── runner.py                      ← Scenario discovery, diff engine, JSON reports
│   ├── datasets/tier_p/               ← 23 offline CSV validator scenarios
│   ├── datasets/tier_i/               ← Idempotency scenarios (needs PG)
│   ├── datasets/tier_s/               ← SQL suite integration scenarios
│   ├── expected/tier_*/               ← Expected outcomes
│   └── reports/                       ← Runtime output (gitignored)
│
└── README.md                          ← Engine-level documentation
```

(`ARCHITECTURE.md`, `LICENSE`, and `.gitignore` live at the repository root.)

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| PostgreSQL | 13+ | Extensions used: `uuid-ossp`, `pg_trgm`, `dblink` |
| psql client | Matching server | Must support `\set`, `\if`, `\i` metacommands |
| bash | 4.0+ | For `deploy_all.sh`, `setup.sh`, and `run_tests.sh` |
| Superuser access | — | Required to create databases and roles |
| Terraform | 1.5+ | For GitHub repo management (`terraform-github-repos/`) |
| GitHub PAT | — | Required by Terraform — scope: `repo` |
| MariaDB / MySQL | 10.6+ / 8.0+ | For `DB_ENGINE=mariadb` — requires `mysql` CLI on PATH |
| SQLite | 3.35+ | For `DB_ENGINE=sqlite` — requires `sqlite3` CLI on PATH |
| InfluxDB | 2.x | For `DB_ENGINE=influxdb` — requires `influx` CLI v2 on PATH |
| Redis | 7.x | For `DB_ENGINE=redis` — requires `redis-cli` on PATH |
| Teradata | Vantage 17+ | For `DB_ENGINE=teradata` — requires `bteq` (TTU) on PATH |

> **Windows users:** Use [WSL2](https://learn.microsoft.com/en-us/windows/wsl/) or [Git Bash](https://gitforwindows.org/) to run the shell scripts. The `.sql` files work natively on any platform via `psql`.

---

## Verify Before You Deploy

Before running any deployment — local or Azure — confirm your environment is
ready. This repository has evolved over time, so always verify which files and
tools are actually present rather than assuming.

### 1. Confirm the required tools are installed

```powershell
az version          # Azure CLI (only needed for Azure deployment)
terraform version   # Terraform 1.5+
psql --version      # PostgreSQL client
python --version    # Python 3.10+
```

If any command is not recognised, install that tool before continuing. On
Windows, add `psql` to PATH permanently:

```powershell
setx PATH "$($env:PATH);C:\Program Files\PostgreSQL\17\bin"
```

### 2. Locate the deployment scripts actually present in your copy

```powershell
Get-ChildItem -Recurse -Filter "deploy-all.ps1" | Select-Object FullName
Get-ChildItem -Recurse -Filter "main.tf"        | Select-Object FullName
Get-ChildItem -Recurse -Filter "deploy_all.sh"  | Select-Object FullName
```

Use the paths these return — do not assume a folder name. Azure automation may
live under `azure-automation/` or `infra/` depending on your version.

### 3. Confirm PostgreSQL is reachable (before DB-backed steps)

```powershell
psql -c '\l'
```

If this fails, local deploys and Tiers I + S of the eval suite will skip — the
database must be installed and running first.

### 4. Confirm no secrets are tracked

```powershell
git ls-files | Select-String -Pattern "config.local.env$|\.tfvars$|\.pgpass"
```

This should return nothing. If it lists a file, remove it from tracking before
pushing.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/amar-python/PostgreDataMigrationApp.git
cd PostgreDataMigrationApp
```

### 2. Run the interactive setup wizard

```bash
cd backend/migration/build
chmod +x setup.sh
./setup.sh
```

The wizard prompts you to select a database engine and configure all settings, then writes `config.local.env`:

```text
  ╔══════════════════════════════════════════════════════════════╗
  ║       PostgreDataMigrationApp — Database Setup Wizard        ║
  ║   Supports: PostgreSQL · MariaDB · SQLite · InfluxDB         ║
  ║             Redis · Teradata                                  ║
  ╚══════════════════════════════════════════════════════════════╝

  1)  postgresql  — PostgreSQL 15  (relational, ACID, recommended)
  2)  mariadb     — MariaDB 10.x   (relational, MySQL-compatible)
  3)  mysql       — MySQL 8.x      (relational, MySQL protocol)
  4)  sqlite      — SQLite 3       (embedded, file-based, no server)
  5)  influxdb    — InfluxDB 2.x   (time-series, metrics & events)
  6)  redis       — Redis 7.x      (in-memory key-value / cache)
  7)  teradata    — Teradata Vantage (enterprise data warehouse)
```

Or skip the wizard and accept all defaults:

```bash
./setup.sh --defaults                 # use all defaults
./setup.sh --engine teradata          # pre-select engine
./setup.sh --engine sqlite --env dev  # pre-select engine + environment
```

### 3. Deploy an environment

```bash
# Dev only (includes realistic seed data)
psql -U postgres -f backend/migration/build/environments/env_dev.sql

# Or deploy all 4 environments at once
chmod +x backend/migration/build/deploy_all.sh
./backend/migration/build/deploy_all.sh
```

### 3. Run the test suite

```bash
chmod +x backend/migration/tests/run_tests.sh
./backend/migration/tests/run_tests.sh dev        # test Dev
./backend/migration/tests/run_tests.sh            # test all 4 environments
```

### 4. Connect and explore

```bash
psql -U te_dev_user -d te_mgmt_dev

-- VCRM coverage for CYB9131
SELECT r.req_identifier, r.title, COUNT(v.tc_id) AS tc_mapped
FROM   te_dev.requirements   r
LEFT   JOIN te_dev.vcrm_entries v ON v.req_id = r.req_id
GROUP  BY r.req_identifier, r.title
ORDER  BY r.req_identifier;
```

---

## CSV Loader

`csv_loader.sh` validates CSV files, derives the target table name from the filename unless `--table` is supplied, writes accepted/skipped row outputs under `csv/logs/`, and routes valid rows to the selected engine-specific loader.

```bash
# Load into the engine from config.local.env
./backend/migration/build/csv_loader.sh data/customers.csv

# Specify engine/environment
./backend/migration/build/csv_loader.sh data/orders.csv --engine postgresql --env dev

# Validate only
./backend/migration/build/csv_loader.sh data/products.csv --engine sqlite --dry-run

# Override the target table name
./backend/migration/build/csv_loader.sh data/export_2025.csv --engine mariadb --table invoices
```

CSV inputs must have a header row, use comma delimiters, and be UTF-8 encoded with or without a BOM. The shared Python validator skips empty rows and row/header column-count mismatches, warns on duplicate headers, preserves quoted commas/newlines, and writes rejected rows with an `_skip_reason` column.

Supported loader backends are PostgreSQL, MariaDB/MySQL, SQLite, InfluxDB, Redis, and Teradata. PostgreSQL uses `COPY`, MariaDB/MySQL uses `LOAD DATA LOCAL INFILE`, SQLite uses Python `csv` + `sqlite3`, InfluxDB writes line protocol via the `influx` CLI, Redis writes hashes through `redis-cli`, and Teradata uses BTEQ/FastLoad tooling.

### Load any CSV

The loader is schema-agnostic — drop any CSV file in front of it and a matching table is auto-created in the target environment's database. Every CSV-loaded table is tagged with two marker columns: `_csv_row_id BIGSERIAL PRIMARY KEY` and `_loaded_at TIMESTAMPTZ`. All other columns start as `TEXT`; `ALTER TABLE` afterwards if you need stricter types.

Three sample CSVs ship under `backend/migration/build/csv/samples/` (`customers.csv`, `orders.csv`, `inventory.csv`) — deliberately off-domain from the T&E schema to demonstrate that any shape is accepted.

```bash
# Single-command happy-path proof (loads all three samples into dev, lists them)
make csv-demo

# Load any CSV
make csv-load FILE=path/to/anything.csv          # ENV defaults to dev
make csv-load FILE=path/to/anything.csv ENV=test ENGINE=postgresql

# Use loaded data — companion script: backend/migration/build/csv_utilise.sh (PostgreSQL only)
./backend/migration/build/csv_utilise.sh list                       # all CSV-loaded tables in the env
./backend/migration/build/csv_utilise.sh describe customers         # columns + row count
./backend/migration/build/csv_utilise.sh peek orders --limit 5      # first N rows
./backend/migration/build/csv_utilise.sh export inventory dump.csv  # round-trip back to CSV
./backend/migration/build/csv_utilise.sh drop customers --yes       # remove a CSV-loaded table
```

`csv_utilise.sh` only sees tables that carry the marker columns, so it cannot accidentally touch the rigid te_core_schema tables.

---

## How Parameterisation Works

Every environment file contains **only a `\set` configuration block** followed by `\i te_core_schema.sql`. All logic lives in the core schema — the environment file is pure configuration.

```sql
-- environments/env_dev.sql — the ONLY file you edit for Dev
\set env_label          DEV
\set db_name            te_mgmt_dev       ← rename the database here
\set schema_name        te_dev            ← rename the schema here
\set app_user           te_dev_user
\set app_password       Dev@Local#2025!
\set tbl_test_cases     test_cases        ← rename any table here
\set include_seed_data  true              ← toggle seed data on/off

\i te_core_schema.sql                     ← unchanged core logic
```

**psql variable syntax used throughout the core schema:**

| Syntax | Expands to | Used for |
|---|---|---|
| `:'varname'` | `'quoted string'` | String literals, WHERE clauses, DO blocks |
| `:"varname"` | `"quoted identifier"` | Table and schema names in DDL/DML |

---

## Environment Comparison

| Setting | Dev | Test | Staging | Prod |
|---|---|---|---|---|
| Database | `te_mgmt_dev` | `te_mgmt_test` | `te_mgmt_staging` | `te_mgmt_prod` |
| Schema | `te_dev` | `te_test` | `te_staging` | `te_prod` |
| App User | `te_dev_user` | `te_test_user` | `te_stg_user` | `te_prod_user` |
| Connection Limit | 10 | 15 | 20 | 50 |
| Seed Data | ✅ Full | ✅ Full | ❌ Empty | ❌ Empty |

Each environment is fully isolated. All four can run on the same PostgreSQL instance.

To deploy to a remote host:

```bash
PGHOST=my-db-server PGPORT=5432 PGUSER=postgres ./backend/migration/build/deploy_all.sh staging
```

---

## Schema Reference — 12 Tables

```text
organisations ──< personnel
      │
      └──< test_programs ──< temp_documents
                  │
                  └──< test_phases ──< test_cases ──< vcrm_entries >── requirements
                              │
                              └──< test_events ──< test_results ──< evidence_artifacts
                                                         │
                                                         └──< defect_reports
```

| Table | Purpose |
|---|---|
| `organisations` | agencies, prime contractors, test units |
| `personnel` | T&E workforce with clearance levels and roles |
| `test_programs` | Top-level programmes (e.g. CYB9131, LAND 400 Ph3) |
| `temp_documents` | Versioned TEMP documents (draft → approved → superseded) |
| `test_phases` | DT&E, AT&E, OT&E and other phase types within a program |
| `requirements` | System requirements subject to T&E verification |
| `test_cases` | Individual test cases with steps and expected results |
| `vcrm_entries` | VCRM — maps requirements ↔ test cases (many-to-many) |
| `test_events` | Scheduled/completed test events (lab, field trial, TTX) |
| `test_results` | Execution outcomes — one row per test case run per event |
| `defect_reports` | Deficiency Reports (DRs) raised against failed results |
| `evidence_artifacts` | Logs, screenshots, reports attached to test results |

### Key enumerated values

```sql
-- personnel.te_role
'test_director' | 'test_manager' | 'test_engineer' |
'te_analyst' | 'safety_engineer' | 'config_manager' | 'observer'

-- personnel.clearance  (Australian security clearance levels)
'baseline' | 'NV1' | 'NV2' | 'PV'

-- test_programs.classification  (ISM-aligned)
'UNCLASSIFIED' | 'PROTECTED' | 'SECRET' | 'TOP SECRET'

-- test_phases.phase_type
'DT&E' | 'AT&E' | 'OT&E' | 'IOT&E' | 'LFT&E' | 'FOLLOW_ON'

-- test_results.verdict
'pass' | 'fail' | 'blocked' | 'not_run' | 'inconclusive'

-- defect_reports.severity
'critical' | 'major' | 'minor' | 'observation'
```

---

## Seed Data (Dev & Test Only)

Realistic Australian T&E data is loaded automatically when `include_seed_data` is `true`.

| Table | Records | Highlights |
|---|---|---|
| `organisations` | 5 | CASG, DST Group, Leidos, BAE Systems, JSTF |
| `personnel` | 6 | Roles from test_director to safety_engineer; NV1–PV clearances |
| `test_programs` | 2 | CYB9131 (PROTECTED), LAND 400 Ph3 (SECRET) |
| `temp_documents` | 3 | Approved v1.0 + draft amendment for CYB9131; draft for LAND 400 |
| `test_phases` | 3 | CYB9131 DT&E (completed), OT&E (active), LAND400 AT&E (planned) |
| `requirements` | 8 | 6 × CYB9131 (security, performance, functional, compliance), 2 × LAND400 |
| `test_cases` | 8 | Security, performance, acceptance TCs against CYB9131 OT&E |
| `vcrm_entries` | 8 | 100% VCRM coverage for CYB9131; LAND400 intentionally uncovered |
| `test_events` | 3 | EV01 completed, EV02 in-progress, EV03 planned |
| `test_results` | 7 | 4 pass, 2 fail, 1 inconclusive — realistic mix |
| `defect_reports` | 3 | DR-CYB-0001 (audit gap), 0002 (TLS 1.2), 0003 (session timeout) |

---

## Test Suite

### Run it

```bash
# Against a single environment
./backend/migration/tests/run_tests.sh dev

# Against all environments
./backend/migration/tests/run_tests.sh

# Run Python tests
python -m unittest discover -s backend/migration/tests -p "test*.py" -v

# Run data-driven CSV validator evals
python backend/migration/evals/runner.py --tiers p

# Run all eval tiers; PostgreSQL-backed tiers skip cleanly if PG is unavailable
python backend/migration/evals/runner.py --tiers p,i,s

# Manually via psql
psql -U postgres -d te_mgmt_dev \
  --set schema_name=te_dev \
  --set tbl_organisations=organisations \
  --set tbl_personnel=personnel \
  --set tbl_test_programs=test_programs \
  --set tbl_temp_documents=temp_documents \
  --set tbl_test_phases=test_phases \
  --set tbl_requirements=requirements \
  --set tbl_test_cases=test_cases \
  --set tbl_vcrm_entries=vcrm_entries \
  --set tbl_test_events=test_events \
  --set tbl_test_results=test_results \
  --set tbl_defect_reports=defect_reports \
  --set tbl_evidence_artifacts=evidence_artifacts \
  -f backend/migration/tests/run_all_tests.sql
```

```powershell
# Windows/PowerShell runner for Python tests
powershell -NoProfile -ExecutionPolicy Bypass -File "backend/migration/tests/run_python_tests.ps1"
# Optional: run a custom test path
powershell -NoProfile -ExecutionPolicy Bypass -File "backend/migration/tests/run_python_tests.ps1" -TestPath "backend/migration/tests/test_csv_validator.py"
```

### Windows / Cursor AI notes

- `setup.sh`, `deploy_all.sh`, and `run_tests.sh` (all under `backend/migration/`) are bash scripts.
- On Windows, run shell scripts via WSL2 or Git Bash.
- The Python unit tests and Tier P evals are Windows-native and do not require WSL.
- Tier I and Tier S evals require a reachable PostgreSQL instance and `psql` on PATH; if unavailable, they skip cleanly.
- Required for Python tests and offline evals:
  - Python on PATH (`python --version`)
  - PowerShell available (`pwsh` or `powershell`)
- Recommended Windows command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "backend/migration/tests/run_python_tests.ps1"
python backend\migration\evals\runner.py --tiers p
```

### CI validation (Windows)

A GitHub Actions workflow is included for Windows validation of the Python tests:

- Workflow file: `.github/workflows/python-validator-tests.yml`
- Runner: `windows-latest`
- Python version: `3.11`
- Command executed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "backend/migration/tests/run_python_tests.ps1"
```

### Data-driven evals

The `evals/` package complements the SQL and unit tests with scenario fixtures and expected JSON outputs.

| Tier | What it validates | Database required? |
|---|---|---|
| P | `csv/validator.py` across 23 CSV edge cases, including malformed rows, BOM, CRLF, Unicode, quoted newlines, long fields, missing env vars, and invalid UTF-8 bytes | No |
| I | Dev deployment idempotency by deploying twice and comparing seed row counts | Yes |
| S | Fresh Dev deploy followed by the full SQL suite, expecting all 85 assertions to pass | Yes |

Run examples:

```powershell
python backend\migration\evals\runner.py                  # Tier P only
python backend\migration\evals\runner.py --tiers p,i,s    # all tiers; I/S skip if PostgreSQL is unavailable
python backend\migration\evals\runner.py --only 14_quoted_newline --tiers p
```

Each eval run writes a JSON report under `backend/migration/evals/reports/<run_id>/summary.json`; that folder is intentionally gitignored.

### Coverage — 85 assertions across 5 suites

| Suite | Assertions | What is tested |
|---|---|---|
| 01 — Organisations & Personnel | 17 | Row counts, FK integrity, CHECK/UNIQUE/NOT NULL constraints |
| 02 — Programs, TEMP & Phases | 19 | Date rules, classification markings, status enums |
| 03 — Requirements & VCRM | 21 | 100% VCRM coverage check, per-program gap detection |
| 04 — Execution & Defects | 28 | Verdict counts, DR linkage to fail results, resolved_at logic |
| 05 — Schema & Business Rules | 20 | Table/index existence, trigger firing, cross-table rules |

### Assertion functions

| Function | Purpose |
|---|---|
| `assert_equals(suite, name, expected, actual)` | Exact value match |
| `assert_not_equals(suite, name, expected, actual)` | Values must differ |
| `assert_row_count(suite, name, query, n)` | COUNT of query = N |
| `assert_true(suite, name, sql_expr)` | Expression is TRUE |
| `assert_false(suite, name, sql_expr)` | Expression is FALSE |
| `assert_not_null(suite, name, query)` | Query returns a value |
| `assert_null(suite, name, query)` | Query returns NULL |
| `assert_raises(suite, name, query)` | Query must throw an exception |

### Sample output

```text
============================================================
 T&E TEST SUITE   Schema: te_dev
============================================================

REPORT 1: Suite Summary
─────────────────────────────────────────────────────────────
 suite             total  passed  failed  pass_rate  status
 ──────────────── ──────  ──────  ──────  ─────────  ──────────────
 business_rules       8       8       0   100.0%     ✓ ALL PASS
 defect_reports      12      12       0   100.0%     ✓ ALL PASS
 organisations        8       8       0   100.0%     ✓ ALL PASS
 personnel            9       9       0   100.0%     ✓ ALL PASS
 programs            13      13       0   100.0%     ✓ ALL PASS
 requirements        11      11       0   100.0%     ✓ ALL PASS
 schema              20      20       0   100.0%     ✓ ALL PASS
 temp_documents       6       6       0   100.0%     ✓ ALL PASS
 test_cases           9       9       0   100.0%     ✓ ALL PASS
 test_events          8       8       0   100.0%     ✓ ALL PASS
 test_phases          6       6       0   100.0%     ✓ ALL PASS
 test_results         9       9       0   100.0%     ✓ ALL PASS
 vcrm                10      10       0   100.0%     ✓ ALL PASS

REPORT 4: Overall Result
─────────────────────────────────────────────────────────────
 total  passed  failed  pass_rate  overall
 ─────  ──────  ──────  ─────────  ───────────────────────
    85      85       0   100.0%    ✓ ALL TESTS PASSED
```

---

## Idempotency

The entire framework is safe to re-run against an existing database:

- `CREATE DATABASE` / `CREATE ROLE` — wrapped in `DO $$ IF NOT EXISTS $$` guards
- `CREATE TABLE` — uses `IF NOT EXISTS`
- `CREATE INDEX` — uses `IF NOT EXISTS`
- `CREATE EXTENSION` — uses `IF NOT EXISTS`
- Seed data — uses `ON CONFLICT DO NOTHING`
- Triggers — `DROP TRIGGER IF EXISTS` before `CREATE TRIGGER`

---

## Production Guidance

- **Never commit real passwords** — use a secrets manager (Azure Key Vault, HashiCorp Vault, AWS Secrets Manager) and inject `app_password` at deploy time.
- **Staging and Prod have seed data disabled** — load your own anonymised snapshot after deployment.
- **Connection limits** per user are set conservatively by default — tune `conn_limit` to your workload.
- The `evidence_artifacts` table is schema-only — wire it to your document store (SharePoint, S3, Azure Blob) via the `file_path` column.

---

## Terraform — GitHub Repository Management

The `terraform-github-repos/` folder manages this repository (and any future ones) as **Infrastructure as Code**. Instead of manually configuring repositories on GitHub, you define them in code and apply changes with a single command.

### Prerequisites

- [Terraform 1.5+](https://developer.hashicorp.com/terraform/install)
- A GitHub Personal Access Token (PAT) with `repo` scope — [generate one here](https://github.com/settings/tokens)

### Setup

```bash
cd terraform-github-repos
```

Set your token as an environment variable (never hard-code it):

```powershell
# PowerShell (Windows)
$env:TF_VAR_github_token="ghp_yourtoken"
```

```bash
# Mac / Linux / Git Bash
export TF_VAR_github_token="ghp_yourtoken"
```

### Run

```bash
terraform init     # download the GitHub provider (run once)
terraform plan     # preview what will change
terraform apply    # apply changes to GitHub
```

### Add a new repository

**Step 1** — Add an entry to `variables.tf`:

```hcl
"MyNewProject" = {
  description = "Description of my new project"
  visibility  = "public"
  topics      = ["python", "automation", "devops"]
}
```

**Step 2** — Add a resource block in `main.tf`:

```hcl
resource "github_repository" "my_new_project" {
  name        = "MyNewProject"
  description = var.repos["MyNewProject"].description
  visibility  = var.repos["MyNewProject"].visibility
  has_issues  = true
  auto_init   = false
  lifecycle { prevent_destroy = true }
}

resource "github_repository_topics" "my_new_project" {
  repository = github_repository.my_new_project.name
  topics     = var.repos["MyNewProject"].topics
}
```

**Step 3** — Apply:

```bash
terraform plan    # confirm what will be created
terraform apply   # create the repo on GitHub
```

### Key features

- `prevent_destroy = true` — protects repos from accidental `terraform destroy`
- `sensitive = true` on the token — prevents it appearing in plan output or logs
- `terraform.tfvars` is in `.gitignore` — credentials are never committed
- All repo config lives in one place: `variables.tf`

### Useful commands

```bash
terraform output          # print all repository URLs
terraform show            # show current managed state
terraform fmt             # auto-format .tf files
terraform validate        # check configuration for errors
```

---

## Contributing

Contributions are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and add or update tests:
   - MEP backend changes → `backend/tests/`
   - Engine SQL changes → `backend/migration/tests/suites/`
4. Verify everything still passes:
   - Backend suite: `python -m pytest backend/tests/`
   - Engine SQL assertions: `./backend/migration/tests/run_tests.sh dev`
5. Verify CI workflow paths: `python3 tools/verify_workflow_paths.py`
6. Open a Pull Request — the repository's
   **[pull request template](.github/pull_request_template.md)** will pre-fill a
   quality checklist. In particular, complete the **Tests Added** and
   **Verified Workflow Paths** sections.

**Guidelines:**

- Keep the framework idempotent — every change must be safe to re-run
- Add at least one test (pytest or SQL assertion) for any new behaviour, table
  column, or constraint
- New/changed API endpoints must declare a Pydantic `response_model`
- Run-status changes must go through the `RunStatus` lifecycle
  (`ALLOWED_TRANSITIONS` in `backend/database/models.py`)
- Do not add `# nosec` / `# noqa` suppressions without documenting them in
  `docs/security/Rationale.md`
- Follow the existing naming convention for tables (`tbl_*`), indexes (`idx_*`), and triggers (`trg_*`)
- Do not commit passwords, real classified data, or environment-specific connection strings

---

## License

MIT — see [LICENSE](LICENSE) for full text.
