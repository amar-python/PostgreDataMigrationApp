# Tier S — Scenario 01: fresh_deploy_then_all_tests_pass

**What this scenario tests**

After a fresh deploy, the bundled SQL test suite (5 suites, 85 assertions) must pass with 100% green.

**What the runner does**

1. Probes for `psql` on PATH and reachable PostgreSQL via `psql -c "SELECT 1"`.
2. If PG isn't reachable, SKIPs cleanly.
3. If reachable:
   - Runs `psql -U postgres -f environments/env_dev.sql` to ensure the Dev environment is current.
   - Invokes `psql ... -f tests/run_all_tests.sql` against `te_mgmt_dev` with all the `--set` table-name overrides the README documents.
   - Captures the suite output.
4. Asserts:
   - Exit code 0.
   - The stdout contains `ALL TESTS PASSED`.
   - The "total/passed" line shows the configured minimum (default 85 / 85).

**Side effects**

Same as Tier I — re-deploys the Dev environment. Read-only after that (suites use `assert_*` functions that don't modify data).
