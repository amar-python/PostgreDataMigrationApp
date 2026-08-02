// API client for the PostgreDataMigrationApp FastAPI backend.
//
// This file used to contain TanStack server functions talking to Supabase.
// It now exposes the SAME function names and call signatures, implemented as
// fetch() calls to the local API — so the UI components did not need rewiring.
//
// Backend: api/ (FastAPI, http://localhost:8000). All database access happens
// server-side in the API; the frontend never talks to Postgres directly.

const API_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

const API_KEY: string = (import.meta.env.VITE_API_KEY as string | undefined) ?? "";

// One-time diagnostic on module load so an API_KEY / VITE_API_KEY mismatch is
// easy to spot in the browser console. The API logs a parallel fingerprint at
// startup (see api/main.py). Fixes BUG-006 in BUG_REPORT.md.
if (typeof window !== "undefined") {
  if (API_KEY) {
    const fp = API_KEY.length >= 4 ? `${API_KEY.slice(0, 4)}...` : "***";

    console.info(
      `[csv.functions] VITE_API_KEY is set (fingerprint: ${fp}, length: ${API_KEY.length}). ` +
        `Backend API_KEY fingerprint must match — check the API startup log if requests 401.`,
    );
  } else {
    console.info(
      "[csv.functions] VITE_API_KEY is empty. Fine if the backend's API_KEY is also unset. " +
        "If requests return 401, set VITE_API_KEY in frontend/.env to match the backend's API_KEY.",
    );
  }
}

// ── Types (unchanged public contract) ────────────────────────────────────────

export type ColumnType = "int8" | "numeric" | "date" | "timestamptz" | "boolean" | "text";

export type RowError = {
  rowNumber: number; // 1-based data row number (excluding header)
  column?: string;
  value?: string;
  reason: string;
};

export type ProcessingLog = {
  ts: number;
  step:
    | "receive"
    | "hash"
    | "duplicate_check"
    | "parse"
    | "validate_columns"
    | "create_table"
    | "cast_rows"
    | "insert"
    | "register"
    | "overwrite"
    | "done"
    | "error";
  level: "info" | "warn" | "error";
  message: string;
  count?: number;
  sql?: string;
};

export type InvalidReason = "empty" | "header_only" | "no_columns";

export type UploadResult =
  | {
      status: "ok";
      fileId: string;
      tableName: string;
      totalRows: number;
      insertedRows: number;
      duplicateRowsSkipped: number;
      failedRows: number;
      columns: string[];
      types: ColumnType[];
      rowErrors: RowError[];
      logs: ProcessingLog[];
      overwritten?: boolean;
      replacedFileName?: string;
    }
  | {
      status: "duplicate_file";
      reason: "content" | "name";
      existingFileName: string;
      tableName: string;
      existingRowCount?: number;
      logs: ProcessingLog[];
    }
  | {
      status: "invalid_structure";
      reason: InvalidReason;
      message: string;
      logs: ProcessingLog[];
    }
  | { status: "error"; message: string; rowErrors?: RowError[]; logs: ProcessingLog[] };

export type CsvFileSummary = {
  id: string;
  file_name: string;
  table_name: string;
  mode?: "dynamic" | "te";
  row_count: number;
  column_names: string[];
  created_at: string;
};

// ── Helpers ──────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new Error(
      `Cannot reach the API at ${API_URL}. Is it running? Start it with scripts/start-api.ps1`,
    );
  }
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

// ── Public API (same names/signatures as the old server functions) ──────────

export type UploadInput = {
  fileName: string;
  content: string;
  types?: ColumnType[];
  overwrite?: boolean;
  mode?: "dynamic" | "te";
  targetTable?: string;
};

export async function uploadCsv(opts: { data: UploadInput }): Promise<UploadResult> {
  return apiFetch<UploadResult>("/api/csv/upload", {
    method: "POST",
    body: JSON.stringify({
      fileName: opts.data.fileName,
      content: opts.data.content,
      types: opts.data.types,
      overwrite: opts.data.overwrite ?? false,
      mode: opts.data.mode ?? "dynamic",
      targetTable: opts.data.targetTable,
    }),
  });
}

export async function listCsvFiles(): Promise<CsvFileSummary[]> {
  return apiFetch<CsvFileSummary[]>("/api/csv/files");
}

export async function previewCsvTable(opts: {
  data: { tableName: string; limit?: number };
}): Promise<{ rows: Record<string, string | number | boolean | null>[] }> {
  const limit = opts.data.limit ?? 50;
  return apiFetch(`/api/csv/tables/${encodeURIComponent(opts.data.tableName)}/rows?limit=${limit}`);
}

// ── Extras exposed by the new backend (not in the Supabase version) ─────────

export type ServerPreview =
  | {
      status: "ok";
      headers: string[];
      columns: string[];
      inferredTypes: ColumnType[];
      sampleRows: string[][];
      totalRowsApprox: number;
      teTableMatch: string | null;
    }
  | { status: "invalid_structure"; reason: InvalidReason };

export async function previewCsvContent(opts: {
  data: { fileName: string; content: string };
}): Promise<ServerPreview> {
  return apiFetch<ServerPreview>("/api/csv/preview", {
    method: "POST",
    body: JSON.stringify(opts.data),
  });
}

export type TeTableStatus = { table: string; exists: boolean; rowCount: number };

export async function listTeTables(): Promise<TeTableStatus[]> {
  return apiFetch<TeTableStatus[]>("/api/te/tables");
}

export async function apiHealth(): Promise<{
  status: string;
  database?: string;
  host?: string;
  postgres?: string;
  error?: string;
}> {
  return apiFetch("/api/health");
}
