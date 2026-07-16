# Security Suppression Rationale

This document records every linter/security-scanner suppression (`# nosec`,
`# noqa`, `shellcheck disable`, etc.) in the codebase, with a technical
justification for why the finding is a false positive or an accepted risk.

**Policy:** a suppression comment is only acceptable when it is accompanied by
an entry in this file. PRs that add a new suppression must update this document
(see the PR template checklist).

---

## Active Suppressions

### 1. `backend/database/connection.py` — `# noqa: BLE001` (broad exception in health check)

```python
except Exception as exc:  # noqa: BLE001 - health check must never raise
```

- **Rule suppressed:** BLE001 (blind `except Exception`).
- **Justification:** `check_db_connection()` is used by the `/api/health`
  endpoint and the startup hook. Its contract is *"return False on any
  failure, never raise"*. The set of exceptions SQLAlchemy/psycopg2 can raise
  during a connection attempt is broad and driver-dependent (OperationalError,
  DBAPIError, socket/DNS errors, ...). Catching a narrower set risks the
  health endpoint returning HTTP 500 instead of a controlled
  `"database": "disconnected"` payload.
- **Risk accepted:** silently swallowing an unexpected programming error in
  this small, side-effect-free function. Mitigated by the failure being
  surfaced in the health payload and startup logs.

### 2. `backend/migration/evals/runner.py` — `# nosec B608` (SQL string composition)

```python
# runner.py:309 (inside _count_dev_rows)
query = 'SELECT count(*) FROM te_dev."' + tbl + '";'  # nosec B608
```

- **Rule suppressed:** Bandit B608 (possible SQL injection via string
  concatenation).
- **Justification:** `tbl` is not user input. It iterates over the hardcoded
  `_DEV_SEED_TABLES` constant defined in the same module; no external or
  request-derived value can reach this string. Table names cannot be bound as
  query parameters in PostgreSQL, so string composition is the only option
  here, and the identifier is double-quoted against a fixed allowlist.
- **Risk accepted:** none in the current call graph. If the eval runner is
  ever refactored to accept table names from configuration or user input,
  this suppression MUST be revisited and the identifier quoted/validated
  (e.g. `psycopg2.sql.Identifier`).

### 3. `backend/migration/evals/runner.py` — `# noqa: BLE001` (broad exception in eval loop)

- **Rule suppressed:** BLE001 (blind `except Exception`).
- **Justification:** the eval runner executes a batch of independent eval
  cases; one case failing for any reason (bad fixture, DB hiccup, assertion
  bug) must be recorded as a failed case rather than aborting the whole run.
  The exception is captured into the eval report, not discarded.
- **Risk accepted:** an unexpected error is downgraded to a failed eval case.
  Acceptable for a developer-facing tool; the full traceback is preserved in
  the report output.

---

## Adding a New Suppression (template)

Copy this template into the "Active Suppressions" section:

```markdown
### N. `<file>:<line>` — `<suppression comment>` (<short description>)

- **Rule suppressed:** <rule id and meaning>.
- **Justification:** <why the finding is a false positive, or why the pattern
  is required here>.
- **Risk accepted:** <what residual risk remains and how it is mitigated>.
```

Guidelines:

1. Prefer fixing the finding over suppressing it.
2. Scope suppressions to a single line — never file-wide or rule-wide
   disables.
3. Include the rule ID in the comment (`# noqa: BLE001`, not bare `# noqa`).
4. Re-review entries here whenever the suppressed code changes.
