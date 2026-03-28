<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useContactsStore } from '../stores/contacts'
import { useDealsStore } from '../stores/deals'
import { useSellersStore } from '../stores/sellers'
import MetricCard from '../components/dashboard/MetricCard.vue'
import RevenueChart from '../components/dashboard/RevenueChart.vue'
import ActivityFeed from '../components/dashboard/ActivityFeed.vue'
import PipelineOverview from '../components/dashboard/PipelineOverview.vue'

const contactsStore = useContactsStore()
const dealsStore = useDealsStore()
const sellersStore = useSellersStore()

function formatCurrency(val: number): string {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}

onMounted(() => {
  dealsStore.fetchDeals()
  contactsStore.fetchContacts()
  sellersStore.fetchSellers()
})

const metrics = computed(() => [
  {
    title: 'Total Revenue',
    value: formatCurrency(contactsStore.totalRevenue),
    trend: '+12.5%',
    trendUp: true,
    icon: 'revenue',
  },
  {
    title: 'New Requests',
    value: String(dealsStore.deals.filter(d => d.stage === 'New Request').length),
    trend: 'Needs Action',
    trendUp: true,
    icon: 'leads',
  },
  {
    title: 'Contacts',
    value: String(contactsStore.contacts.length),
    trend: '+2',
    trendUp: true,
    icon: 'contacts',
  },
  {
    title: 'Conversion Rate',
    value: `${sellersStore.avgConversionRate}%`,
    trend: '+5%',
    trendUp: true,
    icon: 'conversion',
  },
])
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
      <p class="text-sm text-gray-500 mt-1">Welcome back. Here's what's happening with your CRM.</p>
    </div>

    <!-- Metric Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <MetricCard
        v-for="metric in metrics"
        :key="metric.title"
        v-bind="metric"
      />
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
      <RevenueChart />
      <PipelineOverview />
    </div>

    <!-- Activity Feed -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <ActivityFeed />
      <div class="card">
        <h3 class="text-sm font-semibold text-gray-800 mb-4">Deal Stage Breakdown</h3>
        <div class="space-y-3">
          <div v-for="stage in dealsStore.byStage" :key="stage.stage" class="flex items-center justify-between">
            <div class="flex items-center gap-3 flex-1">
              <span class="text-sm text-gray-600 w-28">{{ stage.stage }}</span>
              <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full"
                  :class="{
                    'bg-cyan-400': stage.stage === 'New Request',
                    'bg-teal-400': stage.stage === 'Qualified',
                    'bg-blue-400': stage.stage === 'Discovery',
                    'bg-purple-400': stage.stage === 'Proposal',
                    'bg-orange-400': stage.stage === 'Negotiation',
                    'bg-green-400': stage.stage === 'Closed Won',
                    'bg-red-400': stage.stage === 'Closed Lost',
                  }"
                  :style="{ width: `${(stage.count / dealsStore.deals.length) * 100}%` }"
                ></div>
              </div>
            </div>
            <div class="text-right ml-3">
              <span class="text-sm font-medium text-gray-700">{{ formatCurrency(stage.value) }}</span>
              <span class="text-xs text-gray-400 ml-1">({{ stage.count }})</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
