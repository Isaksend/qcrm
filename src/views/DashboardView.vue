<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useContactsStore } from '../stores/contacts'
import { useDealsStore } from '../stores/deals'
import { usePeriodFilterStore } from '../stores/periodFilter'
import PeriodMonthFilter from '../components/deals/PeriodMonthFilter.vue'
import MetricCard from '../components/dashboard/MetricCard.vue'
import RevenueChart from '../components/dashboard/RevenueChart.vue'
import ActivityFeed from '../components/dashboard/ActivityFeed.vue'
import PipelineOverview from '../components/dashboard/PipelineOverview.vue'
import { dealStageLabel } from '../i18n/stages'
import { analyticsService } from '../services/analytics.service'

const { t, locale } = useI18n()
const contactsStore = useContactsStore()
const dealsStore = useDealsStore()
const periodFilter = usePeriodFilterStore()

const funnelEdges = ref<{ from_stage: string; to_stage: string; count: number; conversion_rate: number }[]>([])
const funnelEvents = ref(0)
const churnBuckets = ref<Record<string, number>>({ Low: 0, Medium: 0, High: 0 })
const churnTotal = ref(0)
const churnModelLoaded = ref(false)

function formatCurrency(val: number): string {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}

const conversionRate = computed(() => {
  const closed = dealsStore.dealsInPeriod.filter((d) => d.stage === 'Closed Won' || d.stage === 'Closed Lost')
  if (closed.length === 0) return 0
  const won = closed.filter((d) => d.stage === 'Closed Won').length
  return Math.round((won / closed.length) * 100)
})

onMounted(async () => {
  dealsStore.fetchDeals()
  contactsStore.fetchContacts()
  try {
    const [funnel, churn] = await Promise.all([
      analyticsService.getFunnelConversions(),
      analyticsService.getChurnRiskDistribution(80),
    ])
    funnelEdges.value = funnel.edges || []
    funnelEvents.value = funnel.events ?? 0
    churnBuckets.value = churn.buckets || { Low: 0, Medium: 0, High: 0 }
    churnTotal.value = churn.total_scored ?? 0
    churnModelLoaded.value = !!churn.model_loaded
  } catch {
    /* analytics optional */
  }
})

const metrics = computed(() => {
  locale.value
  return [
    {
      title: t('dashboard.metrics.totalRevenue'),
      value: formatCurrency(contactsStore.totalRevenue),
      trend: '+12.5%',
      trendUp: true,
      icon: 'revenue',
    },
    {
      title: t('dashboard.metrics.newRequests'),
      value: String(dealsStore.dealsInPeriod.filter((d) => d.stage === 'New Request').length),
      trend: t('dashboard.metrics.needsAction'),
      trendUp: true,
      icon: 'leads',
    },
    {
      title: t('dashboard.metrics.contacts'),
      value: String(contactsStore.contacts.length),
      trend: '+2',
      trendUp: true,
      icon: 'contacts',
    },
    {
      title: t('dashboard.metrics.conversionRate'),
      value: `${conversionRate.value}%`,
      trend: t('dashboard.metrics.winLoss'),
      trendUp: conversionRate.value > 50,
      icon: 'conversion',
    },
  ]
})

function stageTitle(stage: string) {
  return dealStageLabel(t, stage)
}

function stageBarWidth(count: number): string {
  const total = dealsStore.dealsInPeriod.length
  if (!total) return '0%'
  return `${(count / total) * 100}%`
}
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ t('dashboard.title') }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ t('dashboard.subtitle') }}</p>
      </div>
      <PeriodMonthFilter />
    </div>
    <p class="text-xs text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-lg px-3 py-2 mb-4">
      {{ t('dashboard.periodHint', { period: periodFilter.displayLabel }) }}
    </p>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <MetricCard v-for="metric in metrics" :key="metric.title" v-bind="metric" />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
      <div class="card">
        <h3 class="text-sm font-semibold text-gray-800 mb-3">{{ t('dashboard.funnelConversions') }}</h3>
        <p class="text-xs text-gray-500 mb-2">{{ t('dashboard.funnelHint', { n: funnelEvents }) }}</p>
        <div class="max-h-56 overflow-y-auto space-y-1 text-sm">
          <div
            v-for="(e, idx) in funnelEdges"
            :key="idx"
            class="flex justify-between gap-2 border-b border-gray-50 py-1"
          >
            <span class="text-gray-600 truncate"
              >{{ stageTitle(e.from_stage) }} → {{ stageTitle(e.to_stage) }}</span
            >
            <span class="text-gray-900 font-medium shrink-0">{{ Math.round(e.conversion_rate * 100) }}%</span>
          </div>
          <p v-if="!funnelEdges.length" class="text-gray-400 text-sm">{{ t('dashboard.funnelEmpty') }}</p>
        </div>
      </div>
      <div class="card">
        <h3 class="text-sm font-semibold text-gray-800 mb-3">{{ t('dashboard.churnDistribution') }}</h3>
        <p class="text-xs text-gray-500 mb-3">{{ t('dashboard.churnSample', { n: churnTotal }) }}</p>
        <div class="space-y-2">
          <div v-for="tier in ['High', 'Medium', 'Low']" :key="tier" class="flex items-center gap-3">
            <span class="w-16 text-xs font-medium text-gray-600">{{ tier }}</span>
            <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full"
                :class="tier === 'High' ? 'bg-red-400' : tier === 'Medium' ? 'bg-amber-400' : 'bg-emerald-400'"
                :style="{
                  width:
                    churnTotal > 0
                      ? `${((churnBuckets[tier] || 0) / churnTotal) * 100}%`
                      : '0%',
                }"
              ></div>
            </div>
            <span class="text-xs text-gray-600 w-8 text-right">{{ churnBuckets[tier] || 0 }}</span>
          </div>
        </div>
        <p v-if="!churnModelLoaded" class="text-xs text-amber-700 mt-2">{{ t('dashboard.churnHeuristic') }}</p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
      <RevenueChart />
      <PipelineOverview />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <ActivityFeed />
      <div class="card">
        <h3 class="text-sm font-semibold text-gray-800 mb-4">{{ t('dashboard.dealBreakdown') }}</h3>
        <div class="space-y-3">
          <div v-for="stage in dealsStore.byStage" :key="stage.stage" class="flex items-center justify-between">
            <div class="flex items-center gap-3 flex-1">
              <span class="text-sm text-gray-600 w-28 truncate" :title="stageTitle(stage.stage)">{{
                stageTitle(stage.stage)
              }}</span>
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
                  :style="{ width: stageBarWidth(stage.count) }"
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
