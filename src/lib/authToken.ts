/** Treat corrupted browser storage from older bugs as empty */
export function normalizeStoredToken(raw: string | null): string | null {
  if (raw == null || raw === '' || raw === 'undefined' || raw === 'null') return null
  return raw
}
