.PHONY: test-free test-gate test-evals test-e2e test-all \
        lint lint-diff health \
        eval-list eval-compare eval-summary select-tests \
        csv-load csv-list csv-demo \
        test-mep

# Path prefix for the relocated original engine
ENGINE := backend/migration

# ── Test tiers (original engine) ──────────────────────────────────────────────

# Free: unit + regression + security + snapshot — no database, no network.
test-free:
        pytest -m "unit or regression or security or snapshot" $(ENGINE)/tests/ -v

# Gate: everything in test-free + coverage report. CI default, blocks merge.
test-gate:
        pytest -m "unit or regression or security or snapshot" $(ENGINE)/tests/ \
            --cov=$(ENGINE)/build/csv --cov=$(ENGINE)/evals --cov-report=term-missing

# Evals: Tier P (offline) + Tier I/S (skip cleanly if no PostgreSQL).
test-evals:
        python3 $(ENGINE)/evals/runner.py --tiers p,i,s --verbose

# E2E: full pipeline tests that require a running PostgreSQL instance.
test-e2e:
        pytest -m "e2e or integration or parity" $(ENGINE)/tests/ -v

# All: every test tier including evals.
test-all:
        pytest $(ENGINE)/tests/ --cov=$(ENGINE)/build/csv --cov=$(ENGINE)/evals --cov-report=term-missing
        python3 $(ENGINE)/evals/runner.py --tiers p,i,s --verbose

# ── MEP backend tests ────────────────────────────────────────────────────────

test-mep:
        pytest backend/tests/ -v

# ── Code quality ──────────────────────────────────────────────────────────────

lint:
        bash scripts/lint.sh

lint-diff:
        bash scripts/lint_diff.sh

# ── Health & eval tooling ─────────────────────────────────────────────────────

health:
        python3 scripts/health_check.py

eval-list:
        python3 scripts/eval_list.py

eval-compare:
        python3 scripts/eval_compare.py

eval-summary:
        python3 scripts/eval_summary.py

select-tests:
        python3 scripts/select_tests.py

# ── CSV loader / utiliser ─────────────────────────────────────────────────────

csv-load:
        @if [ -z "$(FILE)" ]; then \
            echo "Usage: make csv-load FILE=path/to.csv [ENV=dev] [ENGINE=postgresql]"; \
            exit 1; \
        fi
        bash $(ENGINE)/build/csv_loader.sh "$(FILE)" --env $(or $(ENV),dev) $(if $(ENGINE_ARG),--engine $(ENGINE_ARG),)

csv-list:
        bash $(ENGINE)/build/csv_utilise.sh list --env $(or $(ENV),dev)

csv-demo:
        bash $(ENGINE)/build/csv_loader.sh $(ENGINE)/build/csv/samples/customers.csv --env $(or $(ENV),dev)
        bash $(ENGINE)/build/csv_loader.sh $(ENGINE)/build/csv/samples/orders.csv    --env $(or $(ENV),dev)
        bash $(ENGINE)/build/csv_loader.sh $(ENGINE)/build/csv/samples/inventory.csv --env $(or $(ENV),dev)
        bash $(ENGINE)/build/csv_utilise.sh list --env $(or $(ENV),dev)
