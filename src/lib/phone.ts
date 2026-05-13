/** Только цифры — для сравнения номеров в разных форматах (+7, 8, пробелы). */
export function normalizePhoneDigits(phone: string | null | undefined): string {
  if (!phone) return ''
  return phone.replace(/\D/g, '')
}

/** Сохраняем в едином виде: + и цифры (если есть минимум 10 цифр). */
export function canonicalPhoneForStorage(phone: string): string {
  const d = normalizePhoneDigits(phone)
  if (d.length >= 10) return `+${d}`
  return phone.trim()
}

/** Полный E.164 из кода страны (цифры) и национальной части (только цифры, без кода страны). */
export function buildE164FromDialAndNational(dialDigits: string, nationalRaw: string): string {
  const dial = normalizePhoneDigits(dialDigits)
  const national = normalizePhoneDigits(nationalRaw)
  if (!dial || !national) return ''
  return `+${dial}${national}`
}
