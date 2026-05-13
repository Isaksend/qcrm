<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useContactsStore } from '../stores/contacts'
import { useDealsStore } from '../stores/deals'
import DealsTable from '../components/deals/DealsTable.vue'
import DealsKanban from '../components/deals/DealsKanban.vue'
import DealForm from '../components/deals/DealForm.vue'
import { monthlyRevenue } from '../data/mock'

const { t } = useI18n()
const dealsStore = useDealsStore()
const contactsStore = useContactsStore()
const showForm = ref(false)
const viewMode = ref<'kanban' | 'table'>('kanban')

function formatCurrency(val: number): string {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}

const maxMonthly = computed(() => Math.max(1, ...monthlyRevenue.map((m) => m.value)))

onMounted(() => {
  dealsStore.fetchDeals()
  contactsStore.fetchContacts()
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ t('deals.title') }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ t('deals.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-3">
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

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <div class="card">
        <div class="text-xs text-gray-500 mb-1">{{ t('deals.totalPipeline') }}</div>
        <div class="text-xl font-bold text-gray-900">{{ formatCurrency(dealsStore.totalValue) }}</div>
        <div class="text-xs text-gray-400 mt-1">{{ t('deals.dealsCount', { n: dealsStore.deals.length }) }}</div>
      </div>
      <div class="card">
        <div class="text-xs text-gray-500 mb-1">{{ t('deals.wonRevenue') }}</div>
        <div class="text-xl font-bold text-green-600">{{ formatCurrency(dealsStore.wonValue) }}</div>
        <div class="text-xs text-gray-400 mt-1">
          {{ t('deals.dealsCount', { n: dealsStore.deals.filter((d) => d.stage === 'Closed Won').length }) }}
        </div>
      </div>
      <div class="card">
        <div class="text-xs text-gray-500 mb-1">{{ t('deals.lostRevenue') }}</div>
        <div class="text-xl font-bold text-red-500">{{ formatCurrency(dealsStore.lostValue) }}</div>
        <div class="text-xs text-gray-400 mt-1">
          {{ t('deals.dealsCount', { n: dealsStore.deals.filter((d) => d.stage === 'Closed Lost').length }) }}
        </div>
      </div>
    </div>

    <div class="card mb-6">
      <h3 class="text-sm font-semibold text-gray-800 mb-3">{{ t('deals.monthlyRevenue') }}</h3>
      <div class="flex items-end gap-2 h-20">
        <div v-for="month in monthlyRevenue" :key="month.month" class="flex-1 flex flex-col items-center gap-1">
          <div class="w-full bg-gray-100 rounded-t flex-1 flex items-end">
            <div
              class="w-full bg-indigo-400 rounded-t transition-all hover:bg-indigo-500"
              :style="{ height: `${(month.value / maxMonthly) * 100}%` }"
            ></div>
          </div>
          <span class="text-[10px] text-gray-400">{{ month.month }}</span>
        </div>
      </div>
    </div>

    <DealsKanban v-if="viewMode === 'kanban'" />
    <DealsTable v-else />

    <DealForm v-if="showForm" @close="showForm = false" />
  </div>
</template>
