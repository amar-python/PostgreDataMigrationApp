# MEP Deployment Guide

## Environments

| Environment | Purpose | Database |
|-------------|---------|----------|
| Local (Docker Compose) | Development & demos | PostgreSQL in container |
| CI (GitHub Actions) | Automated testing | SQLite (backend tests) |
| Production | Live deployment | Managed PostgreSQL |

## Local Development (Docker Compose)

### Prerequisites

- Docker 24+ and Docker Compose v2
- Git

### Quick Start

```bash
git clone https://github.com/amar-python/PostgreDataMigrationApp.git
cd PostgreDataMigrationApp

cp .env.example .env        # customise if needed
docker compose up --build
```

| Service | URL | Port |
|---------|-----|------|
| Frontend (React/Nginx) | http://localhost:3000 | 3000 |
| Backend (FastAPI) | http://localhost:8000 | 8000 |
| API Docs (Swagger) | http://localhost:8000/docs | 8000 |
| Database (PostgreSQL) | localhost:5432 | 5432 |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://mep_user:mep_password@db:5432/mep_db` | SQLAlchemy connection string |
| `APP_ENV` | `development` | Runtime environment |
| `DEBUG` | `true` | Enable verbose logging |
| `POSTGRES_DB` | `mep_db` | Database name |
| `POSTGRES_USER` | `mep_user` | Database user |
| `POSTGRES_PASSWORD` | `mep_password` | Database password |

### Stopping

```bash
docker compose down          # stop containers
docker compose down -v       # stop + delete database volume
```

## Running Without Docker

### Backend

```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL="postgresql://user:pass@localhost:5432/mep_db"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # dev server on http://localhost:5173, proxies /api to :8000
```

### Frontend Production Build

```bash
cd frontend
npm run build   # outputs to dist/
```

Serve `dist/` with Nginx or any static file server. Configure reverse proxy
for `/api` → `http://backend:8000`.

## Docker Images

### Backend Dockerfile (`backend/Dockerfile`)

- Base: `python:3.11-slim`
- Installs `requirements.txt`
- Runs: `uvicorn main:app --host 0.0.0.0 --port 8000`

### Frontend Dockerfile (`frontend/Dockerfile`)

- Stage 1: `node:20-alpine` — `npm ci && npm run build`
- Stage 2: `nginx:alpine` — serves `dist/` with custom config
- Nginx proxies `/api` to backend service

## Production Deployment

### Option A: Azure Container Apps

```bash
# Build and push images
docker build -t mep-backend ./backend
docker build -t mep-frontend ./frontend
docker tag mep-backend <acr>.azurecr.io/mep-backend:latest
docker tag mep-frontend <acr>.azurecr.io/mep-frontend:latest
docker push <acr>.azurecr.io/mep-backend:latest
docker push <acr>.azurecr.io/mep-frontend:latest

# Deploy via Azure CLI or Terraform (see infra/)
```

### Option B: Any Docker Host

```bash
docker compose -f docker-compose.yml up -d
```

### Production Checklist

- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Set `APP_ENV=production` and `DEBUG=false`
- [ ] Use managed PostgreSQL (Azure Database, AWS RDS, etc.)
- [ ] Configure HTTPS termination (reverse proxy / load balancer)
- [ ] Set up database backups
- [ ] Configure log aggregation
- [ ] Replace `allow_origins=["*"]` with specific domains in CORS config

## CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/ci.yml`) runs on every push
and pull request to `main` and `develop`:

1. **Backend Tests** — Python 3.11, `pytest tests/ -v`
2. **Frontend Build** — Node 20, `npm ci && npm run build`
3. **Docker Build** — `docker compose build` (only if both above pass)

## Health Checks

| Endpoint | Expected | Purpose |
|----------|----------|---------|
| `GET /` | `{"message": "MEP API is running"}` | API alive |
| `GET /api/health` | `{"status": "healthy", "database": "connected"}` | Full health |

Docker Compose includes a `pg_isready` healthcheck for the database container,
and the backend service waits for the database to be healthy before starting.
