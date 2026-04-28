# PostgreDataMigrationApp

> A fully parameterised, multi-database **Defence Test & Evaluation (T&E) management framework** — supporting PostgreSQL, MariaDB, SQLite, InfluxDB, Redis, and Teradata across Dev, Test, Staging, and Prod environments, with an interactive setup wizard, 85-assertion SQL test suite, and Terraform-managed GitHub repository configuration.

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![MariaDB](https://img.shields.io/badge/MariaDB-10.6%2B-003545?logo=mariadb&logoColor=white)](https://mariadb.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3.35%2B-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![InfluxDB](https://img.shields.io/badge/InfluxDB-2.x-22ADF6?logo=influxdb&logoColor=white)](https://www.influxdata.com/)
[![Redis](https://img.shields.io/badge/Redis-7.x-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Teradata](https://img.shields.io/badge/Teradata-Vantage_17%2B-F37440)](https://www.teradata.com/)
[![Terraform](https://img.shields.io/badge/Terraform-1.5%2B-7B42BC?logo=terraform&logoColor=white)](https://developer.hashicorp.com/terraform)
[![Tests](https://img.shields.io/badge/Tests-85%20assertions%20%7C%20100%25%20pass-brightgreen)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What This Is

A **production-grade database framework** for Australian Defence Test & Evaluation programme management. It supports the full T&E data lifecycle across six database engines, managed through a single interactive setup wizard and deployed with one command.

**Core capabilities:**

- **Program management** — test programs, TEMP document versioning, DT&E / AT&E / OT&E phases
- **Requirement traceability** — system requirements linked to test cases via a VCRM (Verification Cross Reference Matrix)
- **Test execution** — events, results, verdicts, and evidence artefacts
- **Defect reporting** — deficiency reports (DRs) linked directly to failed test results
- **Multi-engine support** — PostgreSQL, MariaDB, SQLite, InfluxDB, Redis, Teradata
- **Multi-environment isolation** — Dev, Test, Staging, and Prod each with separate databases, schemas, and users
- **Automated data testing** — 85 assertions across 5 SQL test suites, written in pure PostgreSQL

---

## Who Is This For?

| Role | How you use this |
|---|---|
| **T&E Engineers / Analysts** | Understand the data model — VCRM, TEMP versioning, DR lifecycle |
| **Database Administrators** | Deploy and maintain the schema across isolated environments and engines |
| **DevOps / Platform Engineers** | Integrate `deploy_all.sh` and `run_tests.sh` into CI/CD pipelines; manage repos with Terraform |
| **Students / Learners** | Study parameterised SQL, idempotent DDL, SQL-native testing, and multi-engine adapter patterns |

---

## Repository Structure

```
PostgreDataMigrationApp/
│
├── adapters/                           ← Engine-specific deployment adapters
│   ├── adapter_postgresql.sh           ← PostgreSQL 15 (psql + \set variables)
│   ├── adapter_mariadb.sh              ← MariaDB / MySQL (mysql CLI + sed substitution)
│   ├── adapter_sqlite.sh               ← SQLite 3 (sqlite3 CLI + sed substitution)
│   ├── adapter_influxdb.sh             ← InfluxDB 2.x (influx CLI + line protocol)
│   ├── adapter_redis.sh                ← Redis 7.x (redis-cli HSET/SADD)
│   └── adapter_teradata.sh             ← Teradata Vantage (BTEQ + sed substitution)
│
├── schema/                             ← Engine-specific DDL and seed data
│   ├── postgresql/
│   │   ├── te_core_schema.sql          ← PostgreSQL DDL (uuid-ossp, pg_trgm, triggers)
│   │   └── te_seed_data.sql            ← PostgreSQL seed data (psql \set variables)
│   ├── mariadb/
│   │   ├── te_core_schema.sql          ← MariaDB DDL (InnoDB, ENUM, ON UPDATE)
│   │   └── te_seed_data.sql            ← MariaDB seed data ({{placeholder}} substitution)
│   ├── sqlite/
│   │   ├── te_core_schema.sql          ← SQLite DDL (WAL, CHECK constraints, triggers)
│   │   └── te_seed_data.sql            ← SQLite seed data ({{placeholder}} substitution)
│   ├── influxdb/
│   │   └── te_seed_data.lp             ← InfluxDB line protocol seed data
│   ├── redis/
│   │   └── te_seed_data.sh             ← Redis seed data (HSET/SADD bash script)
│   └── teradata/
│       ├── te_core_schema.sql          ← Teradata DDL (SET TABLE, PRIMARY INDEX, BTEQ)
│       └── te_seed_data.sql            ← Teradata seed data (BTEQ INSERT statements)
│
├── environments/                       ← PostgreSQL per-environment launchers
│   ├── env_dev.sql                     ← Dev     | DB: te_mgmt_dev     | Seed: ON
│   ├── env_test.sql                    ← Test    | DB: te_mgmt_test    | Seed: ON
│   ├── env_staging.sql                 ← Staging | DB: te_mgmt_staging | Seed: OFF
│   └── env_prod.sql                    ← Prod    | DB: te_mgmt_prod    | Seed: OFF
│
├── tests/
│   ├── framework/
│   │   └── test_framework.sql          ← Assertion library + results table + reporters
│   ├── suites/
│   │   ├── test_01_organisations_personnel.sql
│   │   ├── test_02_programs_phases.sql
│   │   ├── test_03_requirements_vcrm.sql
│   │   ├── test_04_execution_defects.sql
│   │   └── test_05_schema_and_business_rules.sql
│   ├── run_all_tests.sql               ← Master test orchestrator
│   └── run_tests.sh                    ← Bash wrapper (reads config.local.env)
│
├── terraform-github-repos/             ← GitHub repos as Infrastructure as Code
│   ├── main.tf                         ← GitHub provider + repository resources
│   ├── variables.tf                    ← All repo config (edit here to add repos)
│   ├── outputs.tf                      ← Repository URLs printed after apply
│   ├── terraform.tfvars.example        ← Token template — copy to terraform.tfvars
│   ├── .gitignore
│   └── README.md
│
├── setup.sh                            ← Interactive multi-database configuration wizard
├── deploy_all.sh                       ← Multi-engine deployment router
├── config.env                          ← Central config template (all 6 engines)
├── te_core_schema.sql                  ← PostgreSQL master schema (legacy entry point)
├── .gitignore
├── LICENSE
└── README.md
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| PostgreSQL | 15 | Extensions: `uuid-ossp`, `pg_trgm`, `dblink` |
| psql client | Matching server | Must support `\set`, `\if`, `\i` metacommands |
| bash | 4.0+ | For `setup.sh`, `deploy_all.sh`, `run_tests.sh` |
| Superuser access | — | Required to create databases and roles |
| Terraform | 1.5+ | For GitHub repo management (`terraform-github-repos/`) |
| GitHub PAT | — | Required by Terraform — scope: `repo` |
| MariaDB / MySQL | 10.6+ / 8.0+ | `DB_ENGINE=mariadb` — requires `mysql` CLI on PATH |
| SQLite | 3.35+ | `DB_ENGINE=sqlite` — requires `sqlite3` CLI on PATH |
| InfluxDB | 2.x | `DB_ENGINE=influxdb` — requires `influx` CLI v2 on PATH |
| Redis | 7.x | `DB_ENGINE=redis` — requires `redis-cli` on PATH |
| Teradata | Vantage 17+ | `DB_ENGINE=teradata` — requires `bteq` (TTU) on PATH |

> **Windows users:** Use [WSL2](https://learn.microsoft.com/en-us/windows/wsl/) or [Git Bash](https://gitforwindows.org/) to run the shell scripts. The `.sql` files work natively on any platform via `psql`.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/amar-python/PostgreDataMigrationApp.git
cd PostgreDataMigrationApp
```

### 2. Run the interactive setup wizard

```bash
chmod +x setup.sh
./setup.sh
```

The wizard prompts you to select a database engine and configure all connection settings, then writes `config.local.env` (gitignored — never committed):

```
  ╔══════════════════════════════════════════════════════════════╗
  ║       PostgreDataMigrationApp — Database Setup Wizard        ║
  ║   Supports: PostgreSQL · MariaDB · SQLite · InfluxDB         ║
  ║             Redis · Teradata                                  ║
  ╚══════════════════════════════════════════════════════════════╝

  1)  postgresql  — PostgreSQL 15      (relational, ACID, recommended)
  2)  mariadb     — MariaDB 10.x       (relational, MySQL-compatible)
  3)  mysql       — MySQL 8.x          (relational, MySQL protocol)
  4)  sqlite      — SQLite 3           (embedded, file-based, no server)
  5)  influxdb    — InfluxDB 2.x       (time-series, metrics & events)
  6)  redis       — Redis 7.x          (in-memory key-value / cache)
  7)  teradata    — Teradata Vantage   (enterprise data warehouse)
```

Or skip the wizard and use flags:

```bash
./setup.sh --defaults                  # accept all defaults silently
./setup.sh --engine teradata           # pre-select engine
./setup.sh --engine sqlite --env dev   # pre-select engine + environment
```

### 3. Deploy an environment

```bash
# Deploy Dev only (with seed data)
./deploy_all.sh dev

# Deploy all 4 environments
./deploy_all.sh

# Override the engine inline
DB_ENGINE=sqlite ./deploy_all.sh dev

# Target a remote host
PGHOST=my-db-server ./deploy_all.sh staging
```

### 4. Run the test suite (PostgreSQL)

```bash
chmod +x tests/run_tests.sh

./tests/run_tests.sh dev   # test Dev environment
./tests/run_tests.sh       # test all 4 environments
```

### 5. Connect and explore (PostgreSQL)

```bash
psql -U te_dev_user -d te_mgmt_dev

-- VCRM coverage for CYB9131
SELECT r.req_identifier, r.title, COUNT(v.tc_id) AS tc_mapped
FROM   te_dev.requirements  r
LEFT   JOIN te_dev.vcrm_entries v ON v.req_id = r.req_id
GROUP  BY r.req_identifier, r.title
ORDER  BY r.req_identifier;
```

---

## Database Engine Support

### Adapter routing

`deploy_all.sh` reads `DB_ENGINE` from `config.local.env` and routes to the correct adapter:

```
deploy_all.sh
    ├── DB_ENGINE=postgresql  →  adapters/adapter_postgresql.sh
    │                              schema/postgresql/te_core_schema.sql
    │                              schema/postgresql/te_seed_data.sql
    ├── DB_ENGINE=mariadb     →  adapters/adapter_mariadb.sh
    │                              schema/mariadb/te_core_schema.sql
    │                              schema/mariadb/te_seed_data.sql
    ├── DB_ENGINE=sqlite      →  adapters/adapter_sqlite.sh
    │                              schema/sqlite/te_core_schema.sql
    │                              schema/sqlite/te_seed_data.sql
    ├── DB_ENGINE=influxdb    →  adapters/adapter_influxdb.sh
    │                              schema/influxdb/te_seed_data.lp
    ├── DB_ENGINE=redis       →  adapters/adapter_redis.sh
    │                              schema/redis/te_seed_data.sh
    └── DB_ENGINE=teradata    →  adapters/adapter_teradata.sh
                                   schema/teradata/te_core_schema.sql
                                   schema/teradata/te_seed_data.sql
```

### Engine feature comparison

| Feature | PostgreSQL | MariaDB | SQLite | InfluxDB | Redis | Teradata |
|---|---|---|---|---|---|---|
| Schema DDL | ✅ | ✅ | ✅ | N/A | N/A | ✅ |
| Seed data | ✅ | ✅ | ✅ | ✅ (LP) | ✅ (bash) | ✅ |
| 4 environments | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| FK constraints | ✅ | ✅ | ✅ | N/A | N/A | ✅ |
| Auto-update triggers | ✅ | ✅ | ✅ | N/A | N/A | ❌ (app-side) |
| SQL test suite | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Placeholder syntax | `\set` | `{{var}}` | `{{var}}` | CLI flags | env vars | `{{var}}` |

---

## Environment Configuration

| Setting | Dev | Test | Staging | Prod |
|---|---|---|---|---|
| PostgreSQL DB | `te_mgmt_dev` | `te_mgmt_test` | `te_mgmt_staging` | `te_mgmt_prod` |
| PostgreSQL Schema | `te_dev` | `te_test` | `te_staging` | `te_prod` |
| App User | `te_dev_user` | `te_test_user` | `te_stg_user` | `te_prod_user` |
| Connection Limit | 10 | 15 | 20 | 50 |
| Seed Data | ✅ ON | ✅ ON | ❌ OFF | ❌ OFF |

All four environments can run on the same database server instance — fully isolated by database name, schema, and user.

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

## Seed Data

Realistic Australian Defence T&E data loaded automatically for Dev and Test environments:

| Table | Records | Highlights |
|---|---|---|
| `organisations` | 5 | CASG, DST Group, Leidos, BAE Systems, JSTF |
| `personnel` | 6 | Full range from test_director (PV clearance) to safety_engineer (NV1) |
| `test_programs` | 2 | CYB9131 (PROTECTED/active), LAND400-P3 (SECRET/active) |
| `temp_documents` | 3 | CYB9131: approved v1.0 + in_review v1.1; LAND400: draft v0.5 |
| `test_phases` | 3 | CYB9131 DT&E (completed), OT&E (active), LAND400 AT&E (planned) |
| `requirements` | 8 | 6 × CYB9131 (security, performance, functional, compliance), 2 × LAND400 |
| `test_cases` | 8 | MFA, AES-256, availability soak, audit log, RBAC, ISM, TLS |
| `vcrm_entries` | 8 | 100% VCRM coverage for CYB9131; LAND400 intentionally uncovered |
| `test_events` | 3 | EV01 (completed), EV02 (in_progress), EV03 (planned) |
| `test_results` | 7 | 4 pass, 2 fail, 1 inconclusive — realistic mix with DR linkage |
| `defect_reports` | 3 | DR-CYB-0001 (major), DR-CYB-0002 (major), DR-CYB-0003 (minor) |
| `evidence_artifacts` | 0 | Intentionally empty — no evidence files uploaded yet |

---

## Test Suite (PostgreSQL)

### Run

```bash
./tests/run_tests.sh dev    # single environment
./tests/run_tests.sh        # all environments
```

### 85 assertions across 5 suites

| Suite | Assertions | What is tested |
|---|---|---|
| 01 — Organisations & Personnel | 17 | Row counts, FK integrity, CHECK/UNIQUE/NOT NULL constraints |
| 02 — Programs, TEMP & Phases | 19 | Date rules, classification markings, status enums |
| 03 — Requirements & VCRM | 21 | 100% coverage check, per-program gap detection |
| 04 — Execution & Defects | 28 | Verdict counts, DR linkage to fail results, resolved_at logic |
| 05 — Schema & Business Rules | 20 | Table/index existence, trigger firing, cross-table rules |

### Assertion library

| Function | Purpose |
|---|---|
| `assert_equals(suite, name, expected, actual)` | Exact value match (any type) |
| `assert_not_equals(suite, name, expected, actual)` | Values must differ |
| `assert_row_count(suite, name, query, n)` | COUNT of query must equal N |
| `assert_true(suite, name, sql_expression)` | SQL expression must be TRUE |
| `assert_false(suite, name, sql_expression)` | SQL expression must be FALSE |
| `assert_not_null(suite, name, query)` | Query must return a value |
| `assert_null(suite, name, query)` | Query must return NULL |
| `assert_raises(suite, name, query)` | Query must throw an exception |

---

## Terraform — GitHub Repository Management

Manages this repository as Infrastructure as Code using the official GitHub Terraform provider.

```bash
cd terraform-github-repos

# Set your GitHub PAT
export TF_VAR_github_token="ghp_yourtoken"   # Mac/Linux/Git Bash
$env:TF_VAR_github_token="ghp_yourtoken"     # PowerShell

terraform init     # download provider (run once)
terraform plan     # preview changes
terraform apply    # apply to GitHub
terraform output   # print repo URLs
```

Full instructions in [`terraform-github-repos/README.md`](terraform-github-repos/README.md).

---

## Idempotency

The entire framework is safe to re-run against an existing database:

- `CREATE DATABASE` / `CREATE ROLE` — wrapped in `IF NOT EXISTS` guards
- `CREATE TABLE` — uses `IF NOT EXISTS`
- `CREATE INDEX` — uses `IF NOT EXISTS`
- `CREATE EXTENSION` — uses `IF NOT EXISTS`
- Seed data — uses `ON CONFLICT DO NOTHING` (PostgreSQL)
- Triggers — `DROP TRIGGER IF EXISTS` before `CREATE TRIGGER`

---

## Production Guidance

- **Never commit `config.local.env`** — it contains real passwords and is gitignored
- **Use a secrets manager** for production passwords — Azure Key Vault, HashiCorp Vault, or AWS Secrets Manager
- **Staging and Prod have seed data disabled** — load your own anonymised snapshot after deployment
- The `evidence_artifacts` table is schema-only — wire it to your document store (SharePoint, S3, Azure Blob) via the `file_path` column

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and add or update tests in `tests/suites/`
4. Verify all 85 assertions still pass: `./tests/run_tests.sh dev`
5. Open a Pull Request with a clear description of what changed and why

**Guidelines:**
- Keep the framework idempotent — every change must be safe to re-run
- Add at least one assertion for any new table column or constraint
- Follow the existing naming convention: tables (`tbl_*`), indexes (`idx_*`), triggers (`trg_*`)
- Do not commit passwords, real classified data, or environment-specific connection strings

---

## License

MIT — see [LICENSE](LICENSE) for full text.

---

## Acknowledgements

Built for Australian Defence T&E practice, referencing:
- ASDEFCON Test & Evaluation framework
- Australian Signals Directorate (ASD) Information Security Manual (ISM)
- Defence Science and Technology (DST) Group T&E methodology
- VCRM principles aligned with MIL-STD-882 and AS/NZS ISO 31000
