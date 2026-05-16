/**
 * Join backend origin and path (exported for unit tests).
 */
export function joinApiPath(origin: string | undefined | null, path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`
  const o = (origin ?? '').trim().replace(/\/$/, '')
  return o ? `${o}${p}` : p
}

/**
 * Backend base URL for API calls.
 * - Leave VITE_API_BASE_URL unset or empty for same-origin (Docker/nginx: `/api/...`).
 * - Local `vite` / `vite preview`: при пустом значении запросы идут на тот же порт, что и SPA;
 *   в репозитории для dev и preview настроен proxy `/api` → uvicorn (см. vite.config.ts).
 * - Явный бэкенд: `VITE_API_BASE_URL=http://127.0.0.1:8000` (удобно без proxy или другой порт).
 */
export function getBackendOrigin(): string {
  const raw = import.meta.env.VITE_API_BASE_URL
  if (raw === undefined || raw === null || String(raw).trim() === '') {
    return ''
  }
  return String(raw).replace(/\/$/, '')
}

/** Absolute or root-relative URL (e.g. `/api/auth/login` or `http://host:8000/api/...`). */
export function apiUrl(path: string): string {
  return joinApiPath(getBackendOrigin(), path)
}

/** Prefix for `/api/*` routes. */
export function apiPrefix(): string {
  return apiUrl('/api')
}
