# ADR-003: Upload & Migration Workflow Design

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-07-15 |
| Deciders | MEP Team |

## Context

MEP needs a clear, staged workflow for moving CSV data into PostgreSQL.
The workflow must support multiple files per run, automated schema discovery,
data-quality validation, and post-migration evaluation — all while keeping the
existing migration engine's approach of staging tables intact.

## Decision

We adopt a **6-stage linear pipeline** that each migration run progresses through:

```
Upload → Schema Discovery → Validation → Execute → Evaluate → Report
```

### Stage Details

| Stage | Trigger | What Happens | Status Set |
|-------|---------|-------------|------------|
| **Upload** | User drops CSV files | Files saved to `uploads/{run_id}/`, metadata extracted (rows, columns, headers) | `uploading` |
| **Schema Discovery** | User clicks "Validate" | Infer column types (integer/decimal/date/boolean/text), detect nullability, uniqueness | `validating` |
| **Validation** | Runs with discovery | Check duplicate columns, empty headers, null violations, duplicate rows, mixed types | `validating` |
| **Execute** | User clicks "Execute" | Create `staging_{run_id}_{file}` tables, bulk-INSERT CSV data | `migrating` |
| **Evaluate** | User clicks "Evaluate" | Compare source CSV vs staging table: row counts, null %, duplicates → quality score | stays `completed` |
| **Report** | User clicks "Generate" | Aggregate validation + evaluation into JSON or HTML report | no change |

### Key Design Choices

1. **Staging tables, not direct-to-target** — Every CSV loads into its own
   staging table (`staging_{run_id}_{sanitized_name}`). This follows the
   enterprise pattern of raw → clean → target and makes debugging easier.

2. **Schema auto-inference** — Rather than requiring users to define a mapping
   upfront, MEP samples up to 200 values per column to infer the most likely
   PostgreSQL type. This eliminates the need for a separate mapping engine for
   the MVP while still producing typed staging tables.

3. **Quality score with PASS/FAIL** — The evaluation engine produces a score
   from 0–100 based on three weighted checks (row count match, null percentage,
   duplicate rows). Threshold: ≥70 = PASS. This gives stakeholders a single
   number to assess migration trustworthiness.

4. **File-on-disk storage** — Uploaded CSVs are stored on the filesystem
   (`uploads/`) rather than in the database. This keeps the DB lean and allows
   re-reading files for schema inference and evaluation without BLOB overhead.

5. **Validation is non-blocking** — Validation reports issues but does not
   prevent execution. Users can choose to proceed with warnings. Only the
   evaluation score after migration provides the authoritative quality gate.

## Consequences

### Benefits
- Users get immediate value from schema discovery without manual configuration
- The staging-table approach aligns with the original migration engine's design
- Quality scores provide an objective, auditable migration metric
- Each stage is independently callable via the REST API

### Trade-offs
- No manual column mapping UI (auto-inference handles it; can be added later)
- Schema inference may misclassify ambiguous columns (e.g., ZIP codes as integers)
- Quality score weights are fixed (not user-configurable in v1.0)

## Alternatives Considered

1. **Require explicit mapping before migration** — Rejected for MVP; adds
   complexity without proportional value when CSVs create their own tables.

2. **Store CSVs as BLOBs in PostgreSQL** — Rejected; filesystem storage is
   simpler, faster for large files, and easier to debug.

3. **Block migration on validation failure** — Rejected; many real-world
   migrations proceed with known warnings, and the evaluation score provides
   the true quality gate.
