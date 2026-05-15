import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import { i18n } from '../i18n'
import { formatYearMonthFromYm } from '../i18n/dates'

const STORAGE_KEY = 'crm_period_ym'

function currentYearMonth(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  return `${y}-${m}`
}

function parseYearMonth(ym: string): { year: number; month: number } {
  const [y, m] = ym.split('-').map(Number)
  return { year: y || new Date().getFullYear(), month: m || new Date().getMonth() + 1 }
}

export function dealReferenceDate(deal: { createdAt?: string | null; closedAt?: string | null }): Date {
  const raw = deal.createdAt || deal.closedAt
  if (raw) {
    const d = new Date(raw)
    if (!Number.isNaN(d.getTime())) return d
  }
  return new Date()
}

export function isDealInYearMonth(
  deal: { createdAt?: string | null; closedAt?: string | null },
  year: number,
  month: number,
): boolean {
  const d = dealReferenceDate(deal)
  return d.getFullYear() === year && d.getMonth() + 1 === month
}

export const usePeriodFilterStore = defineStore('periodFilter', () => {
  const yearMonth = ref(localStorage.getItem(STORAGE_KEY) || currentYearMonth())

  const year = computed(() => parseYearMonth(yearMonth.value).year)
  const month = computed(() => parseYearMonth(yearMonth.value).month)

  /** Localized label for the selected month (reacts to app language). */
  const displayLabel = computed(() => {
    const loc = i18n.global.locale.value
    return formatYearMonthFromYm(yearMonth.value, loc)
  })

  function setYearMonth(ym: string) {
    yearMonth.value = ym
    localStorage.setItem(STORAGE_KEY, ym)
  }

  function shiftMonth(delta: number) {
    const { year: y, month: m } = parseYearMonth(yearMonth.value)
    const d = new Date(y, m - 1 + delta, 1)
    const next = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    setYearMonth(next)
  }

  watch(yearMonth, (v) => localStorage.setItem(STORAGE_KEY, v))

  return { yearMonth, displayLabel, year, month, setYearMonth, shiftMonth, parseYearMonth }
})
