<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { setAppLocale, type AppLocale } from '../../i18n'

const { locale, t } = useI18n()

function onChange(e: Event) {
  const v = (e.target as HTMLSelectElement).value as AppLocale
  setAppLocale(v)
}
</script>

<template>
  <select
    id="app-locale-select"
    :value="locale"
    :aria-label="t('language.label')"
    class="text-sm border border-gray-200 rounded-lg px-2 py-1.5 bg-white text-gray-700 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 cursor-pointer"
    @change="onChange"
  >
    <option value="en">{{ t('language.en') }}</option>
    <option value="ru">{{ t('language.ru') }}</option>
    <option value="kk">{{ t('language.kk') }}</option>
  </select>
</template>
