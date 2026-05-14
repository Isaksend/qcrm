/** Список IANA-идентификаторов для выбора часового пояса компании. */
export function getSortedTimeZones(): string[] {
  try {
    const iv = Intl as unknown as { supportedValuesOf?: (key: string) => string[] }
    if (typeof iv.supportedValuesOf === 'function') {
      return [...iv.supportedValuesOf('timeZone')].sort((a, b) => a.localeCompare(b))
    }
  } catch {
    /* ignore */
  }
  return [
    'UTC',
    'Asia/Almaty',
    'Asia/Aqtau',
    'Asia/Aqtobe',
    'Asia/Oral',
    'Asia/Qyzylorda',
    'Asia/Tashkent',
    'Asia/Baku',
    'Asia/Tbilisi',
    'Asia/Yerevan',
    'Europe/Moscow',
    'Europe/Minsk',
    'Europe/Kyiv',
    'Europe/Warsaw',
    'Europe/Berlin',
    'Europe/London',
    'America/New_York',
    'America/Los_Angeles',
  ]
}
