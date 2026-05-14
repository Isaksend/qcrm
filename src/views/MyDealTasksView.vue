<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMyDealTasksStore } from '../stores/myDealTasks'

const { t, locale } = useI18n()
const myTasks = useMyDealTasksStore()

function intlLocaleTag(): string {
  const loc = locale.value
  if (loc === 'ru') return 'ru-RU'
  if (loc === 'kk') return 'kk-KZ'
  return 'en-US'
}

function formatDue(iso: string | null | undefined) {
  if (iso == null || String(iso).trim() === '') return '—'
  return new Date(iso).toLocaleString(intlLocaleTag(), {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  void myTasks.refresh(200)
})
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 pb-12">
    <h1 class="text-2xl font-bold text-gray-900 mb-1">{{ t('myDealTasks.title') }}</h1>
    <p class="text-sm text-gray-500 mb-2">{{ t('myDealTasks.subtitle') }}</p>
    <p class="text-sm text-indigo-700 font-semibold mb-6">
      {{ t('myDealTasks.openCountLine', { n: myTasks.openCount }) }}
    </p>

    <div v-if="myTasks.loading" class="text-sm text-gray-500">{{ t('common.loading') }}</div>
    <div v-else-if="!myTasks.items.length" class="text-sm text-gray-500 bg-gray-50 rounded-xl p-6 border border-gray-100">
      {{ t('myDealTasks.empty') }}
    </div>
    <div v-else class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-x-auto">
      <table class="w-full text-sm min-w-[640px]">
        <thead>
          <tr class="text-left text-[10px] uppercase text-gray-400 font-black tracking-widest border-b border-gray-100">
            <th class="px-4 py-3">{{ t('myDealTasks.colDue') }}</th>
            <th class="px-4 py-3">{{ t('myDealTasks.colDeal') }}</th>
            <th class="px-4 py-3">{{ t('myDealTasks.colTask') }}</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in myTasks.items" :key="row.id" class="border-b border-gray-50 last:border-0">
            <td class="px-4 py-3 text-gray-600 whitespace-nowrap">{{ formatDue(row.dueAt) }}</td>
            <td class="px-4 py-3 font-medium text-gray-900">{{ row.dealTitle }}</td>
            <td class="px-4 py-3 text-gray-700">{{ row.title }}</td>
            <td class="px-4 py-3 text-right">
              <router-link
                :to="`/deals/${encodeURIComponent(row.dealId)}`"
                class="text-indigo-600 font-semibold hover:text-indigo-800"
              >
                {{ t('myDealTasks.openDeal') }}
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
