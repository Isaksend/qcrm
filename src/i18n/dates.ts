import type { AppLocale } from './index'

const BCP47: Record<AppLocale, string> = {
  en: 'en-US',
  ru: 'ru-RU',
  kk: 'kk-KZ',
}

export function localeToBcp47(loc: string): string {
  if (loc === 'ru' || loc === 'kk' || loc === 'en') return BCP47[loc]
  return BCP47.en
}

export function formatYearMonthLong(year: number, month: number, loc: string): string {
  const d = new Date(year, month - 1, 1)
  return d.toLocaleDateString(localeToBcp47(loc), { month: 'long', year: 'numeric' })
}

export function formatYearMonthFromYm(ym: string, loc: string): string {
  const [y, m] = ym.split('-').map(Number)
  return formatYearMonthLong(y || new Date().getFullYear(), m || 1, loc)
}

export function formatMonthShort(date: Date, loc: string): string {
  return date.toLocaleDateString(localeToBcp47(loc), { month: 'short' })
}
