# Tier I — Scenario 01: deploy_dev_twice

**What this scenario tests**

Running `psql -U postgres -f environments/env_dev.sql` twice in a row must:

1. Succeed both times (exit 0).
2. Leave the row counts of every seeded table **unchanged** between the first and second run.

This is the load-bearing claim of the README's "Idempotency" section: re-running deployment must be a no-op.

**What the runner does**

1. Probes for `psql` on PATH and a reachable PostgreSQL via `psql -c "SELECT 1"`.
2. If PG isn't reachable, the scenario SKIPs cleanly (not a fail).
3. If reachable:
   - Runs `psql -U postgres -f environments/env_dev.sql` (first deploy).
   - Counts rows in every table under schema `te_dev`.
   - Runs the same command again (second deploy).
   - Counts rows again.
4. Diffs counts and exit codes against `expected/tier_i/01_deploy_dev_twice.json`.

**Env vars consumed**

`PGHOST`, `PGPORT`, `PGUSER` (default: `postgres`), `PGPASSWORD`, and `PGDATABASE` — all standard libpq vars. The runner does **not** drop the database; it expects `env_dev.sql` to create-if-missing.

**Side effects**

This scenario will deploy or re-deploy the **Dev** environment (`te_mgmt_dev` database, `te_dev` schema, `te_dev_user` role) on whatever PG instance `psql` connects to. Make sure that's a development/throwaway machine before running.
