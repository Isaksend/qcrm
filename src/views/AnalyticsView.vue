<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { analyticsService } from '../services/analytics.service'
import { getCountryByIso2 } from '../lib/countries'
import { dealStageLabel } from '../i18n/stages'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
} from 'chart.js'
import { Bar, Doughnut } from 'vue-chartjs'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement)

const { t, locale } = useI18n()

const rawVelocity = ref<Record<string, number> | null>(null)
const rawComms = ref<Record<string, number> | null>(null)
const rawCountryRows = ref<{ country_iso2: string | null; count: number }[]>([])
const rawCityRows = ref<{ city: string; country_iso2: string | null; count: number }[]>([])
const loading = ref(true)

function commTypeLabel(type: string) {
  const k = type.toLowerCase()
  const key = `commTypes.${k}`
  const translated = t(key)
  if (translated === key) {
    return type ? type.charAt(0).toUpperCase() + type.slice(1) : type
  }
  return translated
}

const velocityData = computed(() => {
  locale.value
  if (!rawVelocity.value) return null
  const av = rawVelocity.value
  const stages = Object.keys(av)
  const labels = stages.length ? stages.map((s) => dealStageLabel(t, s)) : [t('analytics.noData')]
  const days = stages.length ? Object.values(av) : [0]
  return {
    labels,
    datasets: [
      {
        label: t('analytics.datasets.avgDays'),
        data: days,
        backgroundColor: 'rgba(99, 102, 241, 0.8)',
        borderRadius: 8,
      },
    ],
  }
})

const commData = computed(() => {
  locale.value
  if (!rawComms.value) return null
  const types = Object.keys(rawComms.value)
  const labels = types.length ? types.map((x) => commTypeLabel(x)) : [t('analytics.noData')]
  const counts = types.length ? Object.values(rawComms.value) : [0]
  return {
    labels,
    datasets: [
      {
        data: counts,
        backgroundColor: ['#6366f1', '#f59e0b', '#10b981', '#ef4444'],
        hoverOffset: 4,
      },
    ],
  }
})

const countryChartData = computed(() => {
  locale.value
  const cRows = rawCountryRows.value
  return {
    labels: cRows.length
      ? cRows.map((r) => getCountryByIso2(r.country_iso2)?.name || t('analytics.notSpecified'))
      : [t('analytics.noData')],
    datasets: [
      {
        label: t('analytics.datasets.contacts'),
        data: cRows.length ? cRows.map((r) => r.count) : [0],
        backgroundColor: 'rgba(79, 70, 229, 0.75)',
        borderRadius: 6,
      },
    ],
  }
})

const cityChartData = computed(() => {
  locale.value
  const cityRows = rawCityRows.value
  return {
    labels: cityRows.length
      ? cityRows.map(
          (r) =>
            `${r.city} (${getCountryByIso2(r.country_iso2)?.name || r.country_iso2 || '?'})`
        )
      : [t('analytics.noData')],
    datasets: [
      {
        label: t('analytics.datasets.contacts'),
        data: cityRows.length ? cityRows.map((r) => r.count) : [0],
        backgroundColor: 'rgba(14, 165, 233, 0.75)',
        borderRadius: 6,
      },
    ],
  }
})

const totalInteractions = computed(() => {
  const d = commData.value?.datasets?.[0]?.data as number[] | undefined
  if (!d?.length) return 0
  return d.reduce((a, b) => a + Number(b || 0), 0)
})

const fetchAnalytics = async () => {
  try {
    const [velocity, comms, byCountry, byCity] = await Promise.all([
      analyticsService.getSalesVelocity(),
      analyticsService.getCommunicationStats(),
      analyticsService.getContactsByCountry().catch(() => ({ rows: [], total_contacts: 0 })),
      analyticsService.getContactsByCity().catch(() => ({ rows: [] })),
    ])

    rawVelocity.value = velocity.average_days_per_stage || {}
    rawComms.value = comms.counts_by_type || {}
    rawCountryRows.value = byCountry.rows || []
    rawCityRows.value = byCity.rows || []
  } catch (error) {
    console.error('Failed to fetch analytics', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchAnalytics)

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    y: { beginAtZero: true, grid: { display: false } },
  },
}

const horizontalBarOptions = {
  indexAxis: 'y' as const,
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    x: { beginAtZero: true, grid: { display: true } },
    y: { grid: { display: false } },
  },
}

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' as const },
  },
}
</script>

<template>
  <div class="p-8 bg-gray-50 min-h-screen">
    <header class="mb-10">
      <h1 class="text-3xl font-extrabold text-gray-900">{{ t('analytics.title') }}</h1>
      <p class="text-gray-500 mt-2">{{ t('analytics.subtitle') }}</p>
    </header>

    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div v-for="i in 4" :key="i" class="h-80 bg-white rounded-2xl animate-pulse"></div>
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
        <div class="flex items-center justify-between mb-8">
          <h2 class="text-xl font-bold text-gray-800">{{ t('analytics.salesVelocity') }}</h2>
          <span class="text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-1 rounded">{{ t('analytics.avgDaysBadge') }}</span>
        </div>
        <div class="h-64">
          <Bar v-if="velocityData" :data="velocityData" :options="barOptions" />
        </div>
        <p class="text-sm text-gray-400 mt-6 italic">
          {{ t('analytics.velocityHint') }}
        </p>
      </div>

      <div class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
        <div class="flex items-center justify-between mb-8">
          <h2 class="text-xl font-bold text-gray-800">{{ t('analytics.communication') }}</h2>
          <span class="text-xs font-medium text-amber-600 bg-amber-50 px-2 py-1 rounded">{{ t('analytics.last45') }}</span>
        </div>
        <div class="h-64">
          <Doughnut v-if="commData" :data="commData" :options="doughnutOptions" />
        </div>
        <p class="text-sm text-gray-400 mt-6 italic">{{ t('analytics.commHint') }}</p>
      </div>

      <div class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
        <div class="flex items-center justify-between mb-8">
          <h2 class="text-xl font-bold text-gray-800">{{ t('analytics.byCountry') }}</h2>
          <span class="text-xs font-medium text-violet-600 bg-violet-50 px-2 py-1 rounded">{{ t('analytics.crmBadge') }}</span>
        </div>
        <div class="h-72">
          <Bar v-if="countryChartData" :data="countryChartData" :options="horizontalBarOptions" />
        </div>
        <p class="text-sm text-gray-400 mt-6 italic">{{ t('analytics.byCountryHint') }}</p>
      </div>

      <div class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
        <div class="flex items-center justify-between mb-8">
          <h2 class="text-xl font-bold text-gray-800">{{ t('analytics.topCities') }}</h2>
          <span class="text-xs font-medium text-sky-600 bg-sky-50 px-2 py-1 rounded">{{ t('analytics.topLimit') }}</span>
        </div>
        <div class="h-72">
          <Bar v-if="cityChartData" :data="cityChartData" :options="horizontalBarOptions" />
        </div>
        <p class="text-sm text-gray-400 mt-6 italic">{{ t('analytics.citiesHint') }}</p>
      </div>

      <div class="lg:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
        <div class="bg-indigo-600 p-6 rounded-2xl text-white shadow-lg shadow-indigo-200">
          <div class="text-indigo-100 text-sm font-medium">{{ t('analytics.efficiency') }}</div>
          <div class="text-3xl font-bold mt-1">A+</div>
          <div class="text-indigo-200 text-xs mt-2">{{ t('analytics.efficiencySub') }}</div>
        </div>
        <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <div class="text-gray-400 text-sm font-medium">{{ t('analytics.totalInteractions') }}</div>
          <div class="text-3xl font-bold text-gray-900 mt-1">{{ totalInteractions }}</div>
          <div class="text-green-500 text-xs mt-2">{{ t('analytics.interactionsPeriod') }}</div>
        </div>
        <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <div class="text-gray-400 text-sm font-medium">{{ t('analytics.stagesInReport') }}</div>
          <div class="text-3xl font-bold text-gray-900 mt-1">
            {{ velocityData?.labels?.length ?? 0 }}
          </div>
          <div class="text-indigo-500 text-xs mt-2">{{ t('analytics.velocityFoot') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
