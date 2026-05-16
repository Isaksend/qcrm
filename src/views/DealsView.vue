<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useContactsStore } from '../stores/contacts'
import { useDealsStore } from '../stores/deals'
import { usePeriodFilterStore } from '../stores/periodFilter'
import DealsTable from '../components/deals/DealsTable.vue'
import DealsKanban from '../components/deals/DealsKanban.vue'
import DealForm from '../components/deals/DealForm.vue'
import PeriodMonthFilter from '../components/deals/PeriodMonthFilter.vue'

const { t } = useI18n()
const dealsStore = useDealsStore()
const contactsStore = useContactsStore()
const periodFilter = usePeriodFilterStore()
const showForm = ref(false)
const viewMode = ref<'kanban' | 'table'>('kanban')

function formatCurrency(val: number): string {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}

const maxMonthly = computed(() =>
  Math.max(1, ...dealsStore.monthlyWonRevenue.map((m) => m.value)),
)

function monthlyBarHeight(value: number): string {
  const pct = (value / maxMonthly.value) * 100
  return value > 0 ? `${Math.max(pct, 6)}%` : '0%'
}

onMounted(() => {
  dealsStore.fetchDeals()
  contactsStore.fetchContacts()
})
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ t('deals.title') }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ t('deals.subtitle') }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <PeriodMonthFilter />
        <div class="bg-gray-100 p-1 rounded-lg flex items-center">
          <button
            @click="viewMode = 'kanban'"
            class="px-3 py-1.5 text-sm font-medium rounded-md transition-colors"
            :class="viewMode === 'kanban' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
          >
            {{ t('deals.kanban') }}
          </button>
          <button
            @click="viewMode = 'table'"
            class="px-3 py-1.5 text-sm font-medium rounded-md transition-colors"
            :class="viewMode === 'table' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
          >
            {{ t('deals.list') }}
          </button>
        </div>
        <button @click="showForm = true" class="btn-primary">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          {{ t('deals.newDeal') }}
        </button>
      </div>
    </div>

    <p class="text-xs text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-lg px-3 py-2 mb-4">
      {{ t('deals.periodHint', { period: periodFilter.displayLabel }) }}
    </p>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <div class="card">
        <div class="text-xs text-gray-500 mb-1">{{ t('deals.totalPipeline') }}</div>
        <div class="text-xl font-bold text-gray-900">{{ formatCurrency(dealsStore.totalValue) }}</div>
        <div class="text-xs text-gray-400 mt-1">
          {{ t('deals.dealsCount', { n: dealsStore.dealsInPeriod.length }) }}
        </div>
      </div>
      <div class="card">
        <div class="text-xs text-gray-500 mb-1">{{ t('deals.wonRevenue') }}</div>
        <div class="text-xl font-bold text-green-600">{{ formatCurrency(dealsStore.wonValue) }}</div>
        <div class="text-xs text-gray-400 mt-1">
          {{
            t('deals.dealsCount', {
              n: dealsStore.dealsInPeriod.filter((d) => d.stage === 'Closed Won').length,
            })
          }}
        </div>
      </div>
      <div class="card">
        <div class="text-xs text-gray-500 mb-1">{{ t('deals.lostRevenue') }}</div>
        <div class="text-xl font-bold text-red-500">{{ formatCurrency(dealsStore.lostValue) }}</div>
        <div class="text-xs text-gray-400 mt-1">
          {{
            t('deals.dealsCount', {
              n: dealsStore.dealsInPeriod.filter((d) => d.stage === 'Closed Lost').length,
            })
          }}
        </div>
      </div>
    </div>

    <div class="card mb-6">
      <h3 class="text-sm font-semibold text-gray-800 mb-3">{{ t('deals.monthlyRevenue') }}</h3>
      <div class="flex items-end gap-3 h-40">
        <div
          v-for="month in dealsStore.monthlyWonRevenue"
          :key="month.key"
          class="flex-1 flex flex-col items-center gap-2 min-w-0"
        >
          <span class="text-xs font-medium text-gray-600">{{ formatCurrency(month.value) }}</span>
          <div class="w-full h-28 bg-gray-100 rounded-t-md flex items-end">
            <div
              class="w-full rounded-t-md transition-all duration-500"
              :class="month.isSelected ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-indigo-400 hover:bg-indigo-500'"
              :style="{ height: monthlyBarHeight(month.value) }"
            ></div>
          </div>
          <span class="text-[10px]" :class="month.isSelected ? 'text-indigo-700 font-semibold' : 'text-gray-500'">
            {{ month.label }}
          </span>
        </div>
      </div>
    </div>

    <DealsKanban v-if="viewMode === 'kanban'" />
    <DealsTable v-else />

    <DealForm v-if="showForm" @close="showForm = false" />
  </div>
</template>
