<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { COUNTRIES, dialForIso2 } from '../../lib/countries'
import { buildE164FromDialAndNational, normalizePhoneDigits } from '../../lib/phone'

export interface CountryPhoneModel {
  countryIso2: string
  nationalNumber: string
  city: string
}

const { t } = useI18n()
const geo = defineModel<CountryPhoneModel>({ required: true })

const dialPreview = computed(() => `+${dialForIso2(geo.value.countryIso2)}`)

const fullPhone = computed(() =>
  buildE164FromDialAndNational(dialForIso2(geo.value.countryIso2), geo.value.nationalNumber)
)

const nationalDigits = computed(() => normalizePhoneDigits(geo.value.nationalNumber))
</script>

<template>
  <div class="space-y-3">
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('countryPhone.country') }}</label>
      <select
        v-model="geo.countryIso2"
        class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white"
      >
        <option v-for="c in COUNTRIES" :key="c.iso2" :value="c.iso2">
          {{ c.name }} (+{{ c.dial }})
        </option>
      </select>
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('countryPhone.nationalNumber') }}</label>
      <div class="flex rounded-lg border border-gray-300 overflow-hidden focus-within:ring-2 focus-within:ring-indigo-500 focus-within:border-indigo-500">
        <span class="shrink-0 px-3 py-2 text-sm bg-gray-100 text-gray-600 border-r border-gray-200 font-mono">{{ dialPreview }}</span>
        <input
          v-model="geo.nationalNumber"
          type="tel"
          inputmode="numeric"
          autocomplete="tel-national"
          class="flex-1 min-w-0 px-3 py-2 text-sm outline-none"
          placeholder="771 677 41 85"
        />
      </div>
      <p class="text-[10px] text-gray-400 mt-1">
        {{ t('countryPhone.fullNumber') }} <span class="font-mono text-gray-600">{{ fullPhone || '—' }}</span>
        <span v-if="nationalDigits.length > 0" class="ml-2">({{ nationalDigits.length }} {{ t('countryPhone.digits') }})</span>
      </p>
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('countryPhone.city') }}</label>
      <input
        v-model="geo.city"
        type="text"
        class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
        :placeholder="t('countryPhone.cityPlaceholder')"
      />
    </div>
  </div>
</template>
