# CSV Loader — PostgreDataMigrationApp

Accepts any CSV file, validates it, loads valid rows into any supported
database engine, and produces a detailed report of what was loaded and
what was skipped.

---

## Quick Start

```bash
# Load a CSV into the default engine (from config.local.env)
./csv_loader.sh data/customers.csv

# Specify engine and environment
./csv_loader.sh data/orders.csv --engine postgresql --env dev

# Validate only — do not load
./csv_loader.sh data/products.csv --engine sqlite --dry-run

# Override the table name
./csv_loader.sh data/export_2025.csv --engine mariadb --table invoices
```

---

## How It Works

```
csv_loader.sh (router)
    │
    ├── 1. Reads config.local.env for engine and connection settings
    ├── 2. Derives table name from CSV filename
    │       customers.csv  →  customers
    │       order_items.csv →  order_items
    │
    ├── 3. Runs csv/validator.sh
    │       - Removes BOM characters
    │       - Checks column count consistency
    │       - Skips empty rows
    │       - Writes valid rows to a temp file
    │       - Writes skipped rows + reason to logs/
    │
    ├── 4. Routes to engine-specific loader
    │       csv/loader_postgresql.sh   — COPY command
    │       csv/loader_mariadb.sh      — LOAD DATA LOCAL INFILE
    │       csv/loader_sqlite.sh       — Python csv + sqlite3
    │       csv/loader_influxdb.sh     — Line protocol via influx CLI
    │       csv/loader_redis.sh        — HSET per row via redis-cli
    │       csv/loader_teradata.sh     — BTEQ INSERT or FastLoad
    │
    └── 5. Writes 3 output files to csv/logs/
            <table>_loaded_<timestamp>.log
            <table>_skipped_<timestamp>.csv
            <table>_report_<timestamp>.txt
```

---

## CSV Format Requirements

| Requirement | Detail |
|---|---|
| First row | Must be column headers |
| Delimiter | Comma (`,`) |
| Quoting | Double quotes (`"`) for fields containing commas or newlines |
| Encoding | UTF-8 (with or without BOM) |
| Line endings | LF or CRLF (both handled) |
| Extension | `.csv` or `.CSV` |

---

## Table Auto-Creation

All loaders automatically create the target table if it does not exist.
All columns default to `TEXT` / `VARCHAR` type. If you need specific
data types, alter the table after the first load:

```sql
-- PostgreSQL: change a column type after load
ALTER TABLE te_dev.customers
   ALTER COLUMN age TYPE INTEGER USING age::INTEGER;

-- MariaDB
ALTER TABLE te_mgmt_dev.customers
   MODIFY COLUMN age INT;

-- SQLite (requires recreating the table)
CREATE TABLE customers_new AS SELECT * FROM customers;
```

---

## Output Files

Every run produces three files in `csv/logs/`:

| File | Contents |
|---|---|
| `<table>_loaded_<ts>.log` | Full load log including SQL executed |
| `<table>_skipped_<ts>.csv` | Rejected rows with `_skip_reason` column |
| `<table>_report_<ts>.txt` | Summary: totals, duration, file paths |

---

## Validation Rules

The shared validator (`csv/validator.sh`) checks every row:

| Rule | Action on failure |
|---|---|
| Row has wrong number of columns | Skip + log reason |
| Row is entirely empty | Skip + log reason |
| Row has all blank values | Skip + log reason |
| File has BOM character | Stripped silently |
| Duplicate column names | Warning logged, load continues |

---

## Engine-Specific Notes

### PostgreSQL
- Uses `COPY FROM STDIN` for high-performance loading
- Connects using `PG_DB_<ENV>` and `PG_SCHEMA_<ENV>` from config

### MariaDB / MySQL
- Uses `LOAD DATA LOCAL INFILE` — requires `--local-infile=1` enabled on server
- Connects using `MYSQL_DB_<ENV>` from config

### SQLite
- Uses Python's built-in `csv` + `sqlite3` modules — no CLI dependency beyond Python 3
- Database file: `SQLITE_DIR/SQLITE_DB_<ENV>`

### InfluxDB
- CSV rows become measurements — table name = measurement name
- Column named `time` or `timestamp` is used as the timestamp field
- Requires `influx` CLI v2 on PATH

### Redis
- Each row stored as a Redis Hash: `{prefix}:{table}:{row_number}`
- Row index maintained in a Redis Set: `{prefix}:{table}:_index`
- Requires `redis-cli` on PATH

### Teradata
- Uses BTEQ INSERT for files < 1,000 rows
- Uses FastLoad for files >= 1,000 rows
- Requires `bteq` and `fastload` (Teradata TTU) on PATH

---

## Adding Custom Validation

To add your own validation rules, edit `csv/validator.sh` and add
checks inside the Python block. Example — reject rows where `email`
column doesn't contain `@`:

```python
# Inside the Python block in validator.sh
if 'email' in cols:
   email_idx = cols.index('email')
   if '@' not in row[email_idx]:
      writer_s.writerow(row + ['invalid email format'])
      skip_count += 1
      continue
```

---

## Example: Full Load Session

```bash
$ ./csv_loader.sh data/personnel.csv --engine postgresql --env dev

────────────────────────────────────────────────────────────
  PostgreDataMigrationApp — CSV Loader
  File        : data/personnel.csv
  Table       : personnel
  Engine      : postgresql
  Environment : dev
  Dry Run     : false
────────────────────────────────────────────────────────────
[i] Step 1/3 — Validating CSV...
  [validator ✓] Header: 6 columns detected — person_id | name | email | role | clearance | org_id
  [validator ✓] Validation complete — 6 rows processed.
  [validator ✓]   Valid rows   : 5
  [validator ⚠]   Skipped rows : 1 — written to: csv/logs/personnel_skipped_20250506_143022.csv
[✓] Validation complete — 5 valid, 1 skipped of 6 total rows.
[i] Step 2/3 — Loading 5 valid rows into 'personnel' via postgresql...
  [pg ✓] Target: te_mgmt_dev.te_dev.personnel on localhost:5432
  [pg ✓] Columns: person_id, name, email, role, clearance, org_id
  [pg ✓] Table ready: te_dev.personnel
  [pg ✓] COPY complete.
  [pg ✓] Rows now in te_dev.personnel: 5
[i] Step 3/3 — Writing summary report...
[✓] Report written to: csv/logs/personnel_report_20250506_143022.txt

────────────────────────────────────────────────────────────
  Load Summary
  Total rows    : 6
  Loaded        : 5
  Skipped       : 1 — see: csv/logs/personnel_skipped_20250506_143022.csv
  Duration      : 2s
  Report        : csv/logs/personnel_report_20250506_143022.txt
```
