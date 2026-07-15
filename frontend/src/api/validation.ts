/**
 * API client for schema discovery, validation, execution, evaluation,
 * reports, and dashboard endpoints.
 */
import apiClient from './client';

// ---------------------------------------------------------------------------
// Validation / Schema types
// ---------------------------------------------------------------------------

export interface ColumnSchema {
  name: string;
  inferred_type: string;
  nullable: boolean;
  unique: boolean;
  sample_values: string[];
  null_count: number;
  total_count: number;
}

export interface ValidationIssue {
  severity: 'error' | 'warning' | 'info';
  check: string;
  column: string | null;
  message: string;
}

export interface FileValidationResult {
  file_id: number;
  filename: string;
  schema: ColumnSchema[];
  issues: ValidationIssue[];
}

export interface ValidationSummary {
  total_files: number;
  errors: number;
  warnings: number;
  passed: boolean;
}

export interface ValidationResponse {
  run_id: number;
  status: string;
  files: FileValidationResult[];
  summary: ValidationSummary;
}

// ---------------------------------------------------------------------------
// Execution types
// ---------------------------------------------------------------------------

export interface MigrationFileResult {
  file_id: number;
  filename: string;
  status: string;
  table_name: string | null;
  rows_loaded: number;
  error: string | null;
}

export interface ExecutionResponse {
  run_id: number;
  status: string;
  files: MigrationFileResult[];
  summary: {
    total_files: number;
    total_rows_loaded: number;
    tables_created: number;
    success: boolean;
  };
}

// ---------------------------------------------------------------------------
// Evaluation types
// ---------------------------------------------------------------------------

export interface EvalCheck {
  check: string;
  status: string;
  detail: string;
  columns?: { column: string; null_pct: number }[];
}

export interface EvalFileResult {
  file_id: number;
  filename: string;
  table_name: string;
  source_rows: number;
  target_rows: number;
  score: number;
  checks: EvalCheck[];
  status: string;
}

export interface EvaluationResponse {
  run_id: number;
  status: string;
  files: EvalFileResult[];
  summary: {
    total_files: number;
    overall_score: number;
    verdict: string;
    total_source_rows: number;
    total_target_rows: number;
  };
}

// ---------------------------------------------------------------------------
// Dashboard types
// ---------------------------------------------------------------------------

export interface DashboardStats {
  total_runs: number;
  runs_by_status: Record<string, number>;
  total_files: number;
  total_rows: number;
  total_size: number;
  recent_runs: {
    id: number;
    name: string;
    environment: string;
    description: string | null;
    status: string;
    created_at: string;
    updated_at: string;
    file_count: number;
    total_size: number;
  }[];
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function validateRun(runId: number): Promise<ValidationResponse> {
  const resp = await apiClient.post(`/migrations/${runId}/validate`);
  return resp.data;
}

export async function executeMigration(runId: number): Promise<ExecutionResponse> {
  const resp = await apiClient.post(`/migrations/${runId}/execute`, null, { timeout: 120_000 });
  return resp.data;
}

export async function evaluateRun(runId: number): Promise<EvaluationResponse> {
  const resp = await apiClient.post(`/migrations/${runId}/evaluate`, null, { timeout: 60_000 });
  return resp.data;
}

export async function generateReport(runId: number, format: 'json' | 'html' = 'json'): Promise<{ run_id: number; format: string; download_url: string }> {
  const resp = await apiClient.post(`/reports/${runId}/generate?format=${format}`);
  return resp.data;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const resp = await apiClient.get('/dashboard');
  return resp.data;
}
