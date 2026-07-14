import axios from 'axios';

/**
 * Shared axios instance for the MEP backend (FastAPI).
 *
 * In dev, Vite proxies `/api` → http://localhost:8000 (see vite.config.ts),
 * and in production nginx routes `/api` to the backend. We therefore use a
 * relative `/api` baseURL so the same build works in both environments.
 *
 * `VITE_API_BASE_URL` can override this if a fully-qualified backend URL is
 * required (e.g. a separately hosted API).
 */
const baseURL = import.meta.env.VITE_API_BASE_URL ?? '/api';

const apiClient = axios.create({
  baseURL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/** Ping the backend health endpoint. Returns true when reachable & healthy. */
export async function checkHealth(): Promise<boolean> {
  try {
    const { data, status } = await apiClient.get('/health');
    return status === 200 && data?.status === 'healthy';
  } catch {
    return false;
  }
}

export default apiClient;
