/**
 * API client for migration run and file upload endpoints.
 */
import apiClient from './client';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MigrationRun {
  id: number;
  name: string;
  environment: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  file_count: number;
  total_size: number;
}

export interface MigrationRunCreate {
  name: string;
  environment?: string;
  description?: string;
}

export interface UploadedFile {
  id: number;
  migration_run_id: number;
  original_filename: string;
  stored_filename: string;
  file_size: number;
  content_type: string | null;
  row_count: number | null;
  column_count: number | null;
  columns: string | null;
  uploaded_at: string;
}

// ---------------------------------------------------------------------------
// Migration Runs
// ---------------------------------------------------------------------------

export async function createMigrationRun(data: MigrationRunCreate): Promise<MigrationRun> {
  const resp = await apiClient.post('/migrations', data);
  return resp.data;
}

export async function listMigrationRuns(): Promise<{ runs: MigrationRun[]; total: number }> {
  const resp = await apiClient.get('/migrations');
  return resp.data;
}

export async function getMigrationRun(runId: number): Promise<MigrationRun> {
  const resp = await apiClient.get(`/migrations/${runId}`);
  return resp.data;
}

export async function deleteMigrationRun(runId: number): Promise<void> {
  await apiClient.delete(`/migrations/${runId}`);
}

// ---------------------------------------------------------------------------
// File Uploads
// ---------------------------------------------------------------------------

export async function uploadFiles(
  runId: number,
  files: File[],
  onProgress?: (percent: number) => void,
): Promise<UploadedFile[]> {
  const formData = new FormData();
  files.forEach((f) => formData.append('files', f));

  const resp = await apiClient.post(`/migrations/${runId}/files`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120_000, // 2 min for large uploads
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
  return resp.data;
}

export async function listFiles(runId: number): Promise<{ files: UploadedFile[]; total: number }> {
  const resp = await apiClient.get(`/migrations/${runId}/files`);
  return resp.data;
}

export async function deleteFile(fileId: number): Promise<void> {
  await apiClient.delete(`/migrations/files/${fileId}`);
}
