# evals/ — how to run

Data-driven evaluations for **PostgreDataMigrationApp**.

> 📖 **For the full end-to-end guide** (prerequisites, run options, troubleshooting,
> adding new scenarios, CI integration), see **[USAGE.md](USAGE.md)**.

Three tiers:

| Tier | What it tests | Needs PostgreSQL? |
|------|--------------|-------------------|
| **P** | Python CSV validator (`csv/validator.py`) — 23 scenarios | No (offline) |
| **I** | Idempotency of `environments/env_dev.sql` (deploy twice → no drift) | Yes |
| **S** | Fresh deploy + full SQL suite must report 85/85 | Yes |

## Quick start

```bash
# From the project root:
python3 evals/runner.py                  # Tier P only (default)
python3 evals/runner.py --tiers p,i,s    # all tiers (skips I/S if no PG)
python3 evals/runner.py --only 05_mixed_valid_skipped
python3 evals/runner.py --verbose
```

Each run writes a JSON summary to `evals/reports/<run_id>/summary.json`.

## How to add a new scenario

1. Create `evals/datasets/tier_<X>/<NN_name>/` and drop an `input.csv` (Tier P)
   or a `README.md` describing the action (Tier I / Tier S).
2. Create `evals/expected/tier_<X>/<NN_name>.json` with the expected outcome.
3. Run `python3 evals/runner.py --only <NN_name> --tiers <X>`.

No code edits needed for Tier P; for new Tier I/S behaviour add a branch in
`runner.py` keyed on the scenario folder name.

## Layout

```
evals/
├── PLAN.md                    # Scope, layout, phases
├── FAILURE_MODES.md           # 29 failure modes catalogued
├── README.md                  # This file
├── runner.py                  # Discovery + diff engine + report
│
├── datasets/
│   ├── tier_p/                # 20 CSV scenarios for csv/validator.py
│   ├── tier_i/                # 1 scenario: deploy twice
│   └── tier_s/                # 1 scenario: deploy + suite
│
├── expected/
│   ├── tier_p/                # 20 JSON expected outcomes
│   ├── tier_i/                # 1 JSON
│   └── tier_s/                # 1 JSON
│
└── reports/                   # generated runtime output
```

## Running on Windows

The runner is a single Python script with no external dependencies beyond
the stdlib + `psql` on PATH (Tier I/S only).

PowerShell:

```powershell
cd "C:\Users\User\OneDrive\Desktop\Migration using ai\PostgreDataMigrationApp"
python evals\runner.py --tiers p,i,s
```

If you don't have PostgreSQL set up locally, expect Tier I and S to SKIP
cleanly with a diagnostic message — that's the designed behaviour.

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | All scenarios in selected tiers passed (skips are not failures) |
| 1    | At least one scenario failed |
| 2    | Configuration error (unknown tier, missing validator script, etc.) |

The CI-friendly default makes it easy to wire into the existing
`.github/workflows/python-validator-tests.yml`.
