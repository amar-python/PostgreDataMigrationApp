# MEP User Guide

## What is MEP?

The **Migration Evaluation Platform (MEP)** is a web application that helps you
migrate CSV data into PostgreSQL and automatically evaluates the quality of the
migration. It wraps a proven CSV-to-PostgreSQL engine with a modern React UI,
REST API, schema discovery, validation, quality scoring, and downloadable reports.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- A modern web browser (Chrome, Firefox, Edge)

### Launch the Application

```bash
cp .env.example .env        # use defaults or customise
docker compose up --build    # starts frontend, backend, database
```

Open **http://localhost:3000** in your browser.

## Application Walkthrough

### 1. Dashboard

The home page shows an overview of all migration activity:

- **Stat cards** — total runs, files, rows, and data size
- **Status breakdown** — how many runs are in each state
- **Recent runs table** — quick access to your latest migrations

### 2. Create a Migration (New Migration)

A 3-step wizard:

#### Step 1 — Configure
- Enter a **name** for the migration (e.g. "Q3 Customer Data")
- Select an **environment** (Development / Staging / Production)
- Add an optional **description**
- Click **Create & Continue**

#### Step 2 — Upload CSV Files
- **Drag and drop** CSV files onto the upload zone, or click to browse
- Upload supports multiple files at once
- After selecting files, click **Upload** — a progress bar tracks the transfer
- The uploaded files table shows filename, size, row count, column count, and upload time
- You can **delete** individual files if needed
- Click **Continue to Summary**

#### Step 3 — Summary
- Review the migration name, environment, file count, total size, and total rows
- Proceed to **Validation** to check data quality

### 3. Schema Discovery & Validation

Navigate to the **Validation** page:

1. Select a migration run from the dropdown
2. Click **Run Validation**
3. For each file, MEP shows:

**Inferred Schema:**

| Column | Type | Nullable | Unique | Nulls | Samples |
|--------|------|----------|--------|-------|---------|
| id | integer | — | ✓ | 0/100 | 1, 2, 3 |
| name | text | ✓ | ✓ | 3/100 | Alice, Bob |
| price | decimal | — | — | 0/100 | 10.5, 20.3 |

**Supported Types:** integer, decimal, date, boolean, text

**Validation Issues:**
- 🔴 **Errors** — duplicate column names, empty headers
- 🟡 **Warnings** — null values, duplicate rows, mixed types
- 🔵 **Info** — passing checks

The summary shows total errors, warnings, and a PASS/FAIL verdict.

### 4. Migration Runs

The **Migration Runs** page lists all runs with status, file count, and size.

**Actions per run:**

| Button | Action |
|--------|--------|
| ▶ Play | **Execute** — creates staging tables in PostgreSQL and loads CSV data |
| 📊 Chart | **Evaluate** — compares source CSVs against loaded tables, produces quality score |
| 🗑 Delete | Removes the run and all its files |

**Execution** creates tables named `staging_{run_id}_{filename}` with columns
matching the inferred schema.

**Evaluation** produces a quality score (0–100) based on:
- Row count match (source vs target)
- Null percentage per column
- Duplicate row detection

Verdict: **PASS** (≥70) or **FAIL** (<70).

### 5. Reports

Generate downloadable reports:

1. Select a migration run
2. Choose format: **HTML** (styled, self-contained) or **JSON** (machine-readable)
3. Click **Generate Report**
4. Click **Download** to save the report

Reports include upload details, validation results, and evaluation scores.

### 6. History

A chronological log of all migration runs showing ID, name, environment,
status, files, size, creation and update timestamps.

### 7. Administration

Platform settings and system information:

- **Database Connection** — test the PostgreSQL connection
- **Platform Configuration** — adjust max upload size, quality thresholds, etc.
- **Security** — authentication and RBAC toggles (planned for future release)
- **System Information** — version, stack details

## End-to-End Workflow

```
Upload CSVs → Schema Discovery → Validation → Execute Migration
    → Evaluate Quality → Generate Report → View on Dashboard
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Drag & Drop | Upload files on the New Migration page |
| Click sidebar item | Navigate between pages |
| Click status chip | No action (display only) |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API Status shows "Disconnected" | Check `docker compose up` is running, backend on port 8000 |
| Upload fails | Check file is `.csv` format, under 100 MB |
| Execute returns error | Requires PostgreSQL (Docker), not available with SQLite |
| Quality score is FAIL | Review evaluation details — check row counts and null percentages |
