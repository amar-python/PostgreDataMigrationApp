# MEP Developer Guide

How to run, develop, and test the Migration Evaluation Platform locally.

## Prerequisites

- **Docker** and **Docker Compose** (v2, `docker compose`)
- For running the tiers outside containers:
  - **Python 3.11+**
  - **Node.js 20+**

## Environment setup

1. Copy the example environment file and adjust if needed:

   ```bash
   cp .env.example .env
   ```

   | Variable            | Default                                                  | Purpose                         |
   | ------------------- | -------------------------------------------------------- | ------------------------------- |
   | `DATABASE_URL`      | `postgresql://mep_user:mep_password@db:5432/mep_db`      | Backend → PostgreSQL connection |
   | `APP_ENV`           | `development`                                            | Runtime environment             |
   | `DEBUG`             | `true`                                                   | Verbose logging                 |
   | `POSTGRES_DB`       | `mep_db`                                                 | Database name                   |
   | `POSTGRES_USER`     | `mep_user`                                               | Database user                   |
   | `POSTGRES_PASSWORD` | `mep_password`                                            | Database password               |

## Run locally (recommended — Docker Compose)

```bash
docker compose up --build
```

Services:

- Frontend → http://localhost:3000
- Backend  → http://localhost:8000 (docs at http://localhost:8000/docs)
- Postgres → localhost:5432

Stop with `Ctrl+C`, or `docker compose down` (add `-v` to also drop the DB volume).

## Run tiers individually (optional)

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Running tests

### Backend (pytest)

```bash
cd backend
pytest tests/ -v
```

### Frontend build check

```bash
cd frontend
npm run build
```

## Branch strategy

- `main` — production-ready, protected. Releases are cut from here.
- `develop` — integration branch for completed features.
- `feature/*` — one branch per feature/fix, branched from `develop`,
  merged back via pull request.

CI (GitHub Actions, `.github/workflows/ci.yml`) runs backend tests, the
frontend build, and a Docker build on every push/PR to `main` and `develop`.
