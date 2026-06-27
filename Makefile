.PHONY: test-free test-gate test-evals test-e2e test-all \
        lint lint-diff health \
        eval-list eval-compare eval-summary select-tests

# ── Test tiers ────────────────────────────────────────────────────────────────

# Free: unit + regression + security + snapshot — no database, no network.
# Mirrors: bun test (free tier in gstack)
test-free:
	pytest -m "unit or regression or security or snapshot" tests/ -v

# Gate: everything in test-free + coverage report. CI default, blocks merge.
# Mirrors: bun run test:gate
test-gate:
	pytest -m "unit or regression or security or snapshot" tests/ \
	    --cov=build/csv --cov=evals --cov-report=term-missing

# Evals: Tier P (offline) + Tier I/S (skip cleanly if no PostgreSQL).
# Mirrors: bun run test:evals
test-evals:
	python3 evals/runner.py --tiers p,i,s --verbose

# E2E: full pipeline tests that require a running PostgreSQL instance.
# Mirrors: bun run test:e2e
test-e2e:
	pytest -m "e2e or integration or parity" tests/ -v

# All: every test tier including evals.
# Mirrors: bun run test:evals:all
test-all:
	pytest tests/ --cov=build/csv --cov=evals --cov-report=term-missing
	python3 evals/runner.py --tiers p,i,s --verbose

# ── Code quality ──────────────────────────────────────────────────────────────

# Full flake8 + bandit scan over all Python source.
# Mirrors: bun run slop
lint:
	bash scripts/lint.sh

# Lint only Python files changed on this branch vs origin/main.
# Mirrors: bun run slop:diff
lint-diff:
	bash scripts/lint_diff.sh

# ── Health & eval tooling ─────────────────────────────────────────────────────

# Component health dashboard — walks every expected file and reports PASS/FAIL.
# Mirrors: bun run skill:check
health:
	python3 scripts/health_check.py

# List all past eval runs.
# Mirrors: bun run eval:list
eval-list:
	python3 scripts/eval_list.py

# Compare two eval runs side-by-side (auto-picks the two most recent).
# Mirrors: bun run eval:compare
eval-compare:
	python3 scripts/eval_compare.py

# Aggregate pass/fail/skip stats across all stored eval runs.
# Mirrors: bun run eval:summary
eval-summary:
	python3 scripts/eval_summary.py

# Show which pytest tests would run given the current git diff.
# Mirrors: bun run eval:select
select-tests:
	python3 scripts/select_tests.py
