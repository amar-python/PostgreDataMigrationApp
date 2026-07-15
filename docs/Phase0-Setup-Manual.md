# Migration Evaluation Platform (MEP) — Phase 0 Setup Manual

> **Purpose:** This manual documents every step taken to transform the existing `PostgreDataMigrationApp` (a CLI-based CSV-to-PostgreSQL migration engine) into an enterprise-grade web application foundation.
>
> **Audience:** Developers, QA engineers, or anyone replicating this setup on a similar project.
>
> **Outcome:** A running 3-tier application (React + FastAPI + PostgreSQL) with CI/CD, documentation, and a clean Git workflow — ready for feature development.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Step 1 — Repository Assessment](#2-step-1--repository-assessment)
3. [Step 2 — Repository Restructure](#3-step-2--repository-restructure)
4. [Step 3 — FastAPI Backend Setup](#4-step-3--fastapi-backend-setup)
5. [Step 4 — React + TypeScript Frontend Setup](#5-step-4--react--typescript-frontend-setup)
6. [Step 5 — Docker Compose Orchestration](#6-step-5--docker-compose-orchestration)
7. [Step 6 — GitHub Actions CI/CD Pipeline](#7-step-6--github-actions-cicd-pipeline)
8. [Step 7 — Documentation](#8-step-7--documentation)
9. [Step 8 — Git Commit, Push & Pull Request](#9-step-8--git-commit-push--pull-request)
10. [Post-Setup Verification](#10-post-setup-verification)
11. [Known Issues & Workarounds](#11-known-issues--workarounds)
12. [What's Next — Phase 1](#12-whats-next--phase-1)

---

## 1. Prerequisites

Before starting, ensure you have:

| Tool | Version | Purpose |
|------|---------|---------|
| Git | 2.30+ | Version control |
| Docker | 20.10+ | Containerisation |
| Docker Compose | 2.0+ | Multi-container orchestration |
| Python | 3.11+ | Backend development |
| Node.js | 20+ | Frontend development |
| npm | 9+ | Frontend package management |
| GitHub account | — | Repository hosting |

---

## 2. Step 1 — Repository Assessment

**Goal:** Understand the existing codebase before making any changes.

### What we assessed

We cloned the existing repository and documented:

```bash
git clone https://github.com/amar-python/PostgreDataMigrationApp.git
cd PostgreDataMigrationApp
```

### Key findings

| Area | Details |
|------|---------|
| **Migration engine** | Bash + Python pipeline: `build/csv/validator.py` validates CSVs, `build/csv_loader.sh` routes to engine-specific loaders, `build/csv/loader_postgresql.sh` uses PostgreSQL `COPY` for high-performance loading |
| **Database support** | PostgreSQL (primary), MariaDB, SQLite, InfluxDB, Redis, Teradata |
| **Testing** | 85 SQL assertions across 5 suites, 9 Python test modules, 23 CSV edge-case eval scenarios |
| **Infrastructure** | Dockerfile (python:3.11-slim), Terraform configs for Azure, GitHub Actions CI |
| **Configuration** | Environment-variable driven via `config.local.env` (gitignored) |
| **Web framework** | None — purely CLI/script-based |

### Output

A detailed assessment was saved to `repo_assessment.md` for reference.

### Why this matters

- Prevents accidentally deleting or breaking existing functionality
- Identifies what can be reused (the migration engine) vs. what needs to be built (web layer)
- Informs the restructuring strategy

---

## 3. Step 2 — Repository Restructure

**Goal:** Reorganise the repository into an enterprise monorepo layout while preserving all existing code.

### 2.1 Create a feature branch

```bash
git checkout -b feature/foundation-setup
```

> **Rule:** Never work directly on `main`. Every change goes through a feature branch → PR → review → merge.

### 2.2 Move existing code into `backend/migration/`

```bash
# Preserve git history with git mv
git mv build/ backend/migration/build/
git mv evals/ backend/migration/evals/
git mv infra/ backend/migration/infra/
git mv tests/ backend/migration/tests/
```

> **Important:** We used `git mv` (not `mv`) to preserve file history in Git.

### 2.3 Create the new directory structure

```bash
# Backend directories
mkdir -p backend/api/routes
mkdir -p backend/services
mkdir -p backend/evaluation
mkdir -p backend/reports
mkdir -p backend/database

# Frontend, Docker, Docs, Uploads
mkdir -p frontend
mkdir -p docker
mkdir -p docs/ADR
mkdir -p uploads
```

### 2.4 Add `.gitkeep` files

Empty directories are not tracked by Git. Place a `.gitkeep` file in each:

```bash
touch frontend/.gitkeep
touch docker/.gitkeep
touch uploads/.gitkeep
touch backend/services/.gitkeep
touch backend/evaluation/.gitkeep
touch backend/reports/.gitkeep
touch backend/database/.gitkeep
```

### 2.5 Create `backend/migration/README.md`

Document that this directory contains the original engine:

```markdown
# Original Migration Engine

This directory contains the original PostgreDataMigrationApp codebase,
preserved and relocated here as part of the MEP v2 restructure.

The FastAPI backend (backend/api/, backend/services/) wraps and
orchestrates this engine rather than reimplementing it.
```

### 2.6 Update root `README.md`

Update to introduce MEP v2 with a link to the original engine at `backend/migration/`.

### 2.7 Update `.gitignore`

Add entries for:

```gitignore
# Frontend
node_modules/
frontend/node_modules/
frontend/build/
frontend/dist/

# Python
__pycache__/
*.py[cod]
.env
.env.*

# Uploads
uploads/*
!uploads/.gitkeep
```

### Final directory structure after this step

```
PostgreDataMigrationApp/
├── backend/
│   ├── api/                  ← new (empty placeholder)
│   ├── services/             ← new (empty placeholder)
│   ├── migration/            ← existing code moved here
│   │   ├── build/
│   │   ├── evals/
│   │   ├── infra/
│   │   └── tests/
│   ├── evaluation/           ← new (empty placeholder)
│   ├── reports/              ← new (empty placeholder)
│   └── database/             ← new (empty placeholder)
├── frontend/                 ← new (empty placeholder)
├── docker/                   ← new (empty placeholder)
├── docs/                     ← new (empty placeholder)
├── uploads/                  ← new (empty placeholder)
├── .github/workflows/        ← existing (preserved)
├── .gitignore                ← updated
└── README.md                 ← updated
```

---

## 4. Step 3 — FastAPI Backend Setup

**Goal:** Create a working API server with a health endpoint that proves the stack is functional.

### 3.1 Create the backend files

#### `backend/config.py` — Application settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://mep_user:mep_password@db:5432/mep_db"
    APP_ENV: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
```

#### `backend/database/connection.py` — Database layer

```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

#### `backend/database/models.py` — Base ORM model

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

#### `backend/api/routes/health.py` — Health check endpoint

```python
from fastapi import APIRouter
from config import settings
from database.connection import check_db_connection

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.APP_ENV,
        "database": "connected" if check_db_connection() else "disconnected"
    }
```

#### `backend/main.py` — Application entrypoint

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.health import router as health_router

app = FastAPI(title="Migration Evaluation Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "MEP API is running", "version": "0.1.0"}
```

### 3.2 Create `backend/requirements.txt`

```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.0
alembic>=1.13.0
pydantic-settings>=2.0.0
python-multipart
python-dotenv
psycopg2-binary
pytest
httpx
pytest-asyncio
```

### 3.3 Create `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.4 Create backend tests

#### `backend/tests/test_health.py`

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### 3.5 Verify

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

Expected output:
```
tests/test_health.py::test_root PASSED
tests/test_health.py::test_health PASSED
```

---

## 5. Step 4 — React + TypeScript Frontend Setup

**Goal:** Create a professional UI shell that looks like Azure Portal — enterprise-grade navigation with no business logic yet.

### 4.1 Scaffold the project

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
```

### 4.2 Install dependencies

```bash
npm install @mui/material @emotion/react @emotion/styled @mui/icons-material
npm install react-router-dom
npm install axios
npm install @fontsource/roboto
```

### 4.3 Create the application structure

```
frontend/src/
├── main.tsx                  ← Entry point (ThemeProvider + BrowserRouter)
├── App.tsx                   ← Top-level routing
├── theme.ts                  ← MUI theme (Azure Blue #0078D4)
├── components/
│   └── Layout/
│       ├── AppLayout.tsx     ← Sidebar + TopBar + content area
│       ├── Sidebar.tsx       ← Collapsible nav drawer
│       └── TopBar.tsx        ← App bar with API status indicator
├── pages/
│   ├── Dashboard.tsx         ← Placeholder page
│   ├── MigrationRuns.tsx     ← Placeholder page
│   ├── NewMigration.tsx      ← Placeholder page
│   ├── Validation.tsx        ← Placeholder page
│   ├── Reports.tsx           ← Placeholder page
│   ├── History.tsx           ← Placeholder page
│   └── Administration.tsx    ← Placeholder page
└── api/
    └── client.ts             ← Axios instance → http://localhost:8000
```

### 4.4 Key design decisions

| Decision | Detail |
|----------|--------|
| **Primary colour** | `#0078D4` (Azure Blue) |
| **Typography** | Segoe UI / Roboto |
| **Sidebar** | Dark background, collapsible to icon-only rail |
| **Navigation items** | Dashboard, Migration Runs, New Migration, Validation, Reports, History, Administration |
| **API status** | Green/red dot in TopBar — pings `GET /api/health` on load |
| **Routing** | React Router v6 with nested routes |

### 4.5 Configure Vite proxy

#### `frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### 4.6 Create `frontend/Dockerfile` (multi-stage)

```dockerfile
# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 4.7 Create `frontend/nginx.conf`

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location /api {
        proxy_pass http://backend:8000;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 4.8 Verify

```bash
cd frontend
npm run build
```

Expected: Build completes successfully with no errors.

---

## 6. Step 5 — Docker Compose Orchestration

**Goal:** One command (`docker compose up`) starts the entire application.

### 5.1 Create `docker-compose.yml` (repo root)

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: mep_db
      POSTGRES_USER: mep_user
      POSTGRES_PASSWORD: mep_password
    ports:
      - "5432:5432"
    volumes:
      - mep_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mep_user -d mep_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://mep_user:mep_password@db:5432/mep_db
      APP_ENV: development
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./uploads:/app/uploads

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  mep_pgdata:
```

### 5.2 Create `.env.example` (repo root)

```env
DATABASE_URL=postgresql://mep_user:mep_password@db:5432/mep_db
APP_ENV=development
DEBUG=true
POSTGRES_DB=mep_db
POSTGRES_USER=mep_user
POSTGRES_PASSWORD=mep_password
```

### 5.3 Verify

```bash
docker compose up --build
```

Expected results:
- PostgreSQL starts and passes health check
- FastAPI starts on port 8000
- React/Nginx starts on port 3000
- Visit `http://localhost:3000` → see the MEP UI shell
- Visit `http://localhost:8000/api/health` → see health JSON

---

## 7. Step 6 — GitHub Actions CI/CD Pipeline

**Goal:** Automated testing on every push and pull request.

### 6.1 Create `.github/workflows/ci.yml`

```yaml
name: MEP CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci && npm run build

  docker-build:
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-build]
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
```

### 6.2 Pipeline flow

```
Push / PR
  ├── backend-test    → Python 3.11 → pytest
  ├── frontend-build  → Node 20 → npm build
  └── docker-build    → docker compose build (runs after both pass)
```

> **Note:** If using the Abacus AI GitHub App to push, the `workflows` permission may not be available. In that case, the CI file should be placed at `docs/ci/ci.yml.pending` and manually moved to `.github/workflows/ci.yml` via the GitHub web UI (see [Known Issues](#11-known-issues--workarounds)).

---

## 8. Step 7 — Documentation

**Goal:** Professional engineering documentation that demonstrates architectural thinking.

### 7.1 Files created

| File | Purpose |
|------|---------|
| `docs/Architecture.md` | 3-tier architecture overview (React → FastAPI → PostgreSQL), existing engine location, design decisions |
| `docs/DeveloperGuide.md` | How to run locally, prerequisites, environment setup, branch strategy, how to run tests |
| `docs/API.md` | Current API endpoints (`GET /` and `GET /api/health`) with request/response examples |
| `docs/ADR/ADR-001-Technology-Choices.md` | Why React + MUI, FastAPI, PostgreSQL were chosen |
| `docs/ADR/ADR-002-Repository-Structure.md` | Why monorepo layout was chosen, how existing engine was preserved |

### 7.2 Documentation conventions

- **Architecture Decision Records (ADRs):** Numbered sequentially (ADR-001, ADR-002, ...). Each new major decision gets its own ADR.
- **Keep documentation alongside code:** All docs live in the `docs/` directory within the repo.
- **Update as you go:** Each phase should add/update relevant docs.

---

## 9. Step 8 — Git Commit, Push & Pull Request

**Goal:** Get all changes onto GitHub with a proper PR workflow.

### 8.1 Stage and commit

```bash
git add -A
git commit -m "feat(foundation): Phase 0 complete — MEP project foundation

- Restructured repo: existing engine preserved in backend/migration/
- FastAPI backend skeleton with health endpoint
- React + TypeScript frontend shell with Azure Portal UI
- Docker Compose stack (React + FastAPI + PostgreSQL)
- GitHub Actions CI/CD pipeline
- Documentation (Architecture, DeveloperGuide, API, ADRs)"
```

### 8.2 Push the branch

```bash
git push -u origin feature/foundation-setup
```

### 8.3 Create a Pull Request

On GitHub, create a PR:
- **From:** `feature/foundation-setup`
- **To:** `main`
- **Title:** `feat(foundation): Phase 0 — MEP project foundation`
- **Description:** Include what's in the PR, acceptance criteria, and any manual steps needed

### 8.4 Review and merge

> **Rule:** Never merge your own PRs without review. On a team, another developer would review. For a solo project, at minimum review the diff yourself on GitHub before merging.

---

## 10. Post-Setup Verification

After merging, verify everything works:

### Checklist

- [ ] `git clone` the repo fresh → all files present
- [ ] `docker compose up --build` → all 3 services start
- [ ] `http://localhost:3000` → frontend loads with navigation
- [ ] `http://localhost:8000` → API root responds with version
- [ ] `http://localhost:8000/api/health` → health check with DB status
- [ ] `pytest backend/tests/ -v` → 2 tests pass
- [ ] `cd frontend && npm run build` → build succeeds
- [ ] GitHub Actions CI triggers on push/PR and passes

---

## 11. Known Issues & Workarounds

### Issue 1: GitHub App cannot push workflow files

**Problem:** The Abacus AI GitHub App (or similar CI tools) may lack the `workflows` permission, causing a 403 error when pushing `.github/workflows/ci.yml`.

**Error message:**
```
remote rejected — refusing to allow a GitHub App to create or update workflow
without `workflows` permission
```

**Workaround:**
1. Place the CI file at `docs/ci/ci.yml.pending` in your commit
2. Push the branch (this will succeed)
3. Manually create `.github/workflows/ci.yml` via the GitHub web UI:
   - Navigate to your branch on GitHub
   - Click **Add file → Create new file**
   - Name: `.github/workflows/ci.yml`
   - Paste the CI content
   - Commit directly to the branch

### Issue 2: Database shows "disconnected" in health check

**Expected behaviour** when running the backend without Docker Compose. The health endpoint returns 200 regardless — it reports DB status but doesn't fail if the DB is unreachable. Run `docker compose up` to start PostgreSQL alongside the backend.

---

## 12. What's Next — Phase 1

Phase 0 provides the **foundation**. No business logic exists yet.

### Phase 1: CSV Upload (Complete Vertical Slice)

The next phase will deliver:

| Layer | Feature |
|-------|---------|
| **Frontend** | Drag-and-drop file upload, multi-file support (10+ CSVs), progress indicators, file removal |
| **Backend** | Upload API endpoint, file storage, metadata persistence, validation |
| **Database** | `MigrationRun` and `UploadedFile` tables |
| **Tests** | API tests, UI tests (Playwright), integration tests |
| **CI** | Extended pipeline with migration-specific tests |

**Acceptance Criteria for Phase 1:**
A user can create a migration run, upload 10 CSV files, see file metadata, delete files, and refresh the page without losing uploaded file information.

### Remaining Phases

| Phase | Feature | Tag |
|-------|---------|-----|
| 2 | Schema Discovery | v0.2 |
| 3 | Mapping Engine | v0.3 |
| 4 | Validation Engine | v0.4 |
| 5 | Migration Engine (wrap existing code) | v0.5 |
| 6 | Evaluation Engine | v0.6 |
| 7 | Reports (PDF/HTML/JSON) | v0.7 |
| 8 | Dashboard & History | v1.0 |

---

## Appendix: Git Branch Strategy

```
main                ← production-ready, tagged releases
  │
  ├── develop       ← integration branch
  │     │
  │     ├── feature/foundation-setup     (Phase 0)
  │     ├── feature/upload-ui            (Phase 1)
  │     ├── feature/upload-api           (Phase 1)
  │     ├── feature/schema-engine        (Phase 2)
  │     ├── feature/mapping-engine       (Phase 3)
  │     ├── feature/evaluation-engine    (Phase 6)
  │     └── feature/dashboard            (Phase 8)
```

**Every feature:**
- Has its own branch
- Has its own pull request
- Passes CI
- Is merged only after review

---

*Document generated: 15 July 2026*
*Project: Migration Evaluation Platform (MEP) v0.1.0*
*Repository: https://github.com/amar-python/PostgreDataMigrationApp*
