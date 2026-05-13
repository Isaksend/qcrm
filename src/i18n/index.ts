import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import ru from './locales/ru.json'
import kk from './locales/kk.json'

export type AppLocale = 'en' | 'ru' | 'kk'

export const LOCALE_STORAGE_KEY = 'tiny_crm_locale'

function readStoredLocale(): AppLocale | null {
  if (typeof localStorage === 'undefined') return null
  const s = localStorage.getItem(LOCALE_STORAGE_KEY)
  if (s === 'en' || s === 'ru' || s === 'kk') return s
  return null
}

function browserLocale(): AppLocale {
  if (typeof navigator === 'undefined') return 'en'
  const lang = navigator.language?.slice(0, 2).toLowerCase()
  if (lang === 'ru') return 'ru'
  if (lang === 'kk') return 'kk'
  return 'en'
}

export function getInitialLocale(): AppLocale {
  return readStoredLocale() ?? browserLocale()
}

export const i18n = createI18n({
  legacy: false,
  locale: getInitialLocale(),
  fallbackLocale: 'en',
  messages: { en, ru, kk },
  globalInjection: true,
})

export function setAppLocale(loc: AppLocale): void {
  i18n.global.locale.value = loc
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(LOCALE_STORAGE_KEY, loc)
  }
  if (typeof document !== 'undefined') {
    document.documentElement.lang = loc
  }
}

if (typeof document !== 'undefined') {
  document.documentElement.lang = getInitialLocale()
}
