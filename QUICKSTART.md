# Quick Start — PostgreDataMigrationApp

A 10-minute walkthrough to deploy the Dev environment, run the eval suite, and
view the auto-generated VCRM gap report.

For the full architecture and rationale see `ARCHITECTURE.md`, `VCRM.md`, and
`evals/PLAN.md`.

## Prerequisites

- PostgreSQL 14 or later running locally (default port 5432)
- Python 3.10 or later on PATH
- `psql` client on PATH (Windows: under `C:\Program Files\PostgreSQL\<ver>\bin`)
- Git Bash, WSL, or PowerShell (examples below use PowerShell)

## Install

- Clone or extract the project to a working folder
- Open PowerShell and `cd` into the `PostgreDataMigrationApp` folder
- Confirm `psql --version` returns a 14+ build
- Confirm `python --version` returns 3.10+

## Configure connection

- Set the standard libpq environment variables once per session
- Use a role that can create databases, schemas, and roles
- For first-time setup, the superuser `postgres` works fine

```powershell
$env:PGHOST     = 'localhost'
$env:PGPORT     = '5432'
$env:PGUSER     = 'postgres'
$env:PGPASSWORD = '<your password>'
```

## Deploy the Dev environment

From the project root:

```powershell
cd "$env:USERPROFILE\OneDrive\Desktop\Migration using ai\PostgreDataMigrationApp"
bash build\deploy_all.sh dev
```

On success you should see `ALL ENVIRONMENTS DEPLOYED` and the new database
`te_dev` with schema `te_dev` containing the 6 core tables.

## Run the eval suite

The single entry point is `evals\runner.py`. Three tiers run by default:

- **Tier P** — 23 Python validator scenarios (no DB required, ~5 seconds)
- **Tier I** — 1 idempotency scenario (PG required)
- **Tier S** — 1 SQL suite integration scenario (PG required, ~30 seconds)

```powershell
python evals\runner.py --tiers p,i,s
```

Expected outcome with PG available: `total: 25, passed: 25, failed: 0`.
Without PG, Tier P passes and Tiers I + S skip cleanly with a diagnostic.

## View the auto-generated gap report

Every run writes two files under `evals\reports\<run_id>\`:

- `summary.json` — machine-readable scenario outcomes
- `VCRM_GAPS_<run_id>.md` — per-run mapping of the 22 business requirements
  to this run's evidence, with REGRESSION / VERIFIED / PARTIAL / SKIPPED /
  UNVERIFIED / DEFERRED status per BR

Open the latest report in your editor:

```powershell
$latest = Get-ChildItem evals\reports -Directory |
          Sort-Object LastWriteTime -Descending |
          Select-Object -First 1
code "evals\reports\$($latest.Name)\VCRM_GAPS_$($latest.Name).md"
```

## Regenerate a gap report after the fact

If you want to rebuild the gap report for an earlier run without rerunning
the suite:

```powershell
python evals\gap_report.py evals\reports\20260605T102805Z-a83461\
```

Replace the timestamp with any folder name under `evals\reports\`.

## Expected results by tier

| Tier | Scenarios | Pass criteria | Typical wall-clock |
| --- | --- | --- | --- |
| P | 23 | All exit-code + stderr diffs match expected | ~5 s |
| I | 1 | Two deploys back-to-back, identical row counts | ~10 s |
| S | 1 | 85/85 assertions, "ALL TESTS PASSED" in stdout | ~30 s |
| X | deferred | Cross-engine schema equivalence | n/a |
| E | deferred | Cross-environment structural parity | n/a |

## Run ID format

Each run gets a timestamped folder under `evals\reports\`. The pattern is
`<UTC-timestamp>-<6-char-hash>`, for example `20260605T102805Z-a83461`.

| Segment | Meaning | Example |
| --- | --- | --- |
| `20260605` | UTC date `YYYYMMDD` | June 5, 2026 |
| `T102805Z` | UTC time `HHMMSS` + `Z` | 10:28:05 UTC |
| `-a83461` | 6-char random suffix | disambiguates concurrent runs |

## Troubleshooting

- **`psql: command not found`** — add the PG `bin` folder to PATH or use the
  full path `C:\Program Files\PostgreSQL\17\bin\psql.exe`
- **`FATAL: password authentication failed`** — recheck `$env:PGPASSWORD`
  matches the role you set during PG install
- **Tier I + S show SKIP** — PG is not reachable; verify `psql -c '\l'` works
  before rerunning
- **Tier S row-count drift** — check `actual.row_counts_first` vs
  `actual.row_counts_second` in `summary.json` to pinpoint the table whose
  seed inserts are missing `ON CONFLICT DO NOTHING`

## Next steps

- Read `evals\USAGE.md` for runner flags and CI integration
- Read `VCRM_GAPS.md` for the four open gaps and remediation effort
- Read `TEST_CONDITIONS.md` for the full catalogue of test conditions
- Read `evals\HANDOFF.md` for what is deferred and why
