# Defence T&E Database Framework

> A fully parameterised, idempotent **PostgreSQL database framework** for Defence **Test & Evaluation (T&E)** programme management — covering TEMP documents, VCRM traceability, test execution, defect reporting, and multi-environment deployment, with a built-in SQL test suite.

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Environments](https://img.shields.io/badge/Environments-Dev%20%7C%20Test%20%7C%20Staging%20%7C%20Prod-blue)]()
[![Test Suites](https://img.shields.io/badge/Tests-5%20suites%20%7C%2085%20assertions-brightgreen)]()

---

## What This Is

This project provides a **production-grade SQL framework** to stand up a Defence T&E management database from scratch — on a single PostgreSQL server or across multiple environments. It is designed to support the full T&E lifecycle as practised in Australian Defence acquisition:

- **Program management** — test programs, TEMP versioning, DT&E / AT&E / OT&E phases
- **Requirement traceability** — system requirements linked to test cases via a VCRM (Verification Cross Reference Matrix)
- **Test execution** — events, results, verdicts, and evidence artefacts
- **Defect reporting** — deficiency reports (DRs) linked directly to failed results
- **Multi-environment isolation** — separate databases, schemas, and users for Dev, Test, Staging, and Prod
- **Automated data testing** — 85 assertions across 5 SQL test suites, all written in pure PostgreSQL

All names (database, schema, users, every table) are controlled by a single `\set` configuration block at the top of each environment file. Rename anything in one place and the entire script updates automatically.

---

## Who Is This For?

| Role | How you use this |
|---|---|
| **T&E Engineers / Analysts** | Understand the data model — VCRM, TEMP versioning, DR lifecycle |
| **Database Administrators** | Deploy and maintain the schema across isolated environments |
| **DevOps / Platform Engineers** | Plug `deploy_all.sh` and `run_tests.sh` into CI/CD pipelines |
| **Students / Learners** | Study parameterised SQL, idempotent DDL patterns, and SQL-native testing |

---

## Repository Structure

```
PostgreDataMigrationApp/
│
├── te_core_schema.sql              ← Master schema — all DDL, triggers, seed data
│                                     Do NOT run directly; called by environment files
│
├── environments/
│   ├── env_dev.sql                 ← Dev     │ DB: te_mgmt_dev     │ Seed: ON
│   ├── env_test.sql                ← Test    │ DB: te_mgmt_test    │ Seed: ON
│   ├── env_staging.sql             ← Staging │ DB: te_mgmt_staging │ Seed: OFF
│   └── env_prod.sql                ← Prod    │ DB: te_mgmt_prod    │ Seed: OFF
│
├── tests/
│   ├── framework/
│   │   └── test_framework.sql      ← Assertion library + results table
│   ├── suites/
│   │   ├── test_01_organisations_personnel.sql
│   │   ├── test_02_programs_phases.sql
│   │   ├── test_03_requirements_vcrm.sql
│   │   ├── test_04_execution_defects.sql
│   │   └── test_05_schema_and_business_rules.sql
│   ├── run_all_tests.sql           ← Master test orchestrator
│   └── run_tests.sh                ← Bash wrapper (coloured output + summary)
│
├── deploy_all.sh                   ← Deploy one or all environments
├── .gitignore
├── LICENSE
└── README.md
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| PostgreSQL | 13+ | Extensions used: `uuid-ossp`, `pg_trgm`, `dblink` |
| psql client | Matching server | Must support `\set`, `\if`, `\i` metacommands |
| bash | 4.0+ | For `deploy_all.sh` and `run_tests.sh` |
| Superuser access | — | Required to create databases and roles |

> **Windows users:** Use [WSL2](https://learn.microsoft.com/en-us/windows/wsl/) or [Git Bash](https://gitforwindows.org/) to run the shell scripts. The `.sql` files work natively on any platform via `psql`.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/PostgreDataMigrationApp.git
cd PostgreDataMigrationApp
```

### 2. Deploy an environment

```bash
# Dev only (includes realistic seed data)
psql -U postgres -f environments/env_dev.sql

# Or deploy all 4 environments at once
chmod +x deploy_all.sh
./deploy_all.sh
```

### 3. Run the test suite

```bash
chmod +x tests/run_tests.sh
./tests/run_tests.sh dev        # test Dev
./tests/run_tests.sh            # test all 4 environments
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
PGHOST=my-db-server PGPORT=5432 PGUSER=postgres ./deploy_all.sh staging
```

---

## Schema Reference — 12 Tables

```
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
| `organisations` | Defence agencies, prime contractors, test units |
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

Realistic Australian Defence T&E data is loaded automatically when `include_seed_data` is `true`.

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
./tests/run_tests.sh dev

# Against all environments
./tests/run_tests.sh

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
  -f tests/run_all_tests.sql
```

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

```
============================================================
 DEFENCE T&E TEST SUITE   Schema: te_dev
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

## Contributing

Contributions are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and add or update tests in `tests/suites/`
4. Verify all 85 assertions still pass: `./tests/run_tests.sh dev`
5. Open a Pull Request with a clear description of what changed and why

**Guidelines:**
- Keep the framework idempotent — every change must be safe to re-run
- Add at least one test assertion for any new table column or constraint
- Follow the existing naming convention for tables (`tbl_*`), indexes (`idx_*`), and triggers (`trg_*`)
- Do not commit passwords, real classified data, or environment-specific connection strings

---

## License

MIT — see [LICENSE](LICENSE) for full text.

---

## Acknowledgements

Built with Australian Defence T&E practice in mind, referencing:
- ASDEFCON Test & Evaluation framework
- Australian Signals Directorate (ASD) Information Security Manual (ISM)
- Defence Science and Technology (DST) Group T&E methodology
- VCRM principles aligned with MIL-STD-882 and AS/NZS ISO 31000
