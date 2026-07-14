# Migration Engine

Original migration engine — wrapped by FastAPI.

This directory contains the original `PostgreDataMigrationApp` codebase, preserved
unchanged and relocated here as part of the Migration Evaluation Platform (MEP) v2
restructure. Nothing here was rewritten — files were only moved.

## Contents

| Path | Description |
|------|-------------|
| `build/` | "Everything that ships" — the SQL-first, multi-engine database framework and the CSV → PostgreSQL loader/validator pipeline (`csv_loader.sh`, `csv/validator.py`, `csv/loader_postgresql.sh`). |
| `evals/` | Data-driven black-box scenarios (23 CSV edge-case scenarios across tiers P/I/S) plus the eval runner and VCRM gap report generator. |
| `infra/` | Containerisation (`Dockerfile`, `entrypoint.sh`) and Azure Terraform IaC. |
| `tests/` | Correctness coverage — 85 SQL assertions across 5 suites plus 9 Python test modules. |

## Role within MEP

The reusable "migration engine" is the `build/csv_loader.sh` + `build/csv/validator.py`
+ `build/csv/loader_postgresql.sh` pipeline (CSV → PostgreSQL via `COPY`). The MEP
FastAPI backend (`backend/api/`, `backend/services/`) wraps this engine rather than
reimplementing CSV → PostgreSQL loading.

> **Note:** Internal path references inside `evals/runner.py` and `tests/*` were written
> relative to the original repository root (e.g. `Path(__file__).parents[1] / "build"`).
> Because `build/`, `evals/`, `infra/` and `tests/` were moved together into
> `backend/migration/`, their relative layout is preserved. Any absolute-from-root
> references should be re-verified when the FastAPI wrapper is wired up.
