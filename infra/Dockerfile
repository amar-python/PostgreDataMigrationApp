# Dockerfile — migration runner image
#
# Builds a single image that can:
#   1. Deploy the schema (build/deploy_all.sh <env>)
#   2. Load input CSVs (input_data/load_input_data.sql)
#   3. Run the eval suite (evals/runner.py --tiers p,i,s)
#
# Entrypoint dispatches on the first arg: deploy | load | evals | shell.
#
# Build from the repo root:
#   docker build -f PostgreDataMigrationApp/infra/Dockerfile -t te-migration:dev .
#
# Run locally (against a PG container on the same network):
#   docker run --rm \
#     -e PGHOST=postgres -e PGPORT=5432 -e PGUSER=postgres \
#     -e PGPASSWORD=devpass -e PGDATABASE=te_dev \
#     -e TARGET_ENV=dev \
#     te-migration:dev deploy

FROM python:3.11-slim AS base

# psql client + bash + curl for libpq env-var support and shell scripts
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client-15 \
        bash \
        curl \
        ca-certificates \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Non-root user — never run migrations as root
RUN groupadd --gid 1001 app \
    && useradd --uid 1001 --gid app --shell /bin/bash --create-home app

WORKDIR /opt/migration

# Copy only what the runner needs (NOT the .git folder, IDE configs, etc.)
COPY --chown=app:app PostgreDataMigrationApp/build/        ./build/
COPY --chown=app:app PostgreDataMigrationApp/tests/        ./tests/
COPY --chown=app:app PostgreDataMigrationApp/evals/        ./evals/
COPY --chown=app:app PostgreDataMigrationApp/input_data/   ./input_data/
COPY --chown=app:app PostgreDataMigrationApp/infra/entrypoint.sh ./entrypoint.sh

RUN chmod +x entrypoint.sh build/deploy_all.sh build/setup.sh 2>/dev/null || true
RUN find build -name '*.sh' -exec chmod +x {} \;

USER app

# Default env values — Container Instance / GitHub Actions override these
ENV PGHOST=localhost \
    PGPORT=5432 \
    PGUSER=postgres \
    PGDATABASE=te_dev \
    TARGET_ENV=dev \
    WAIT_FOR_DB_SECONDS=60

ENTRYPOINT ["./entrypoint.sh"]
CMD ["deploy"]
