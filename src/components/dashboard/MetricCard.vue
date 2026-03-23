<script setup lang="ts">
defineProps<{
  title: string
  value: string
  trend: string
  trendUp: boolean
  icon: string
}>()
</script>

<template>
  <div class="card">
    <div class="flex items-center justify-between mb-4">
      <span class="text-sm font-medium text-gray-500">{{ title }}</span>
      <div class="w-10 h-10 rounded-lg flex items-center justify-center"
        :class="icon === 'revenue' ? 'bg-green-100' : icon === 'leads' ? 'bg-blue-100' : icon === 'contacts' ? 'bg-purple-100' : 'bg-orange-100'"
      >
        <!-- Revenue -->
        <svg v-if="icon === 'revenue'" class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <!-- Leads -->
        <svg v-if="icon === 'leads'" class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
        </svg>
        <!-- Contacts -->
        <svg v-if="icon === 'contacts'" class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
        </svg>
        <!-- Conversion -->
        <svg v-if="icon === 'conversion'" class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      </div>
    </div>
    <div class="text-2xl font-bold text-gray-900">{{ value }}</div>
    <div class="flex items-center gap-1 mt-1">
      <svg
        class="w-4 h-4"
        :class="trendUp ? 'text-green-500' : 'text-red-500'"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          v-if="trendUp"
          stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M5 10l7-7m0 0l7 7m-7-7v18"
        />
        <path
          v-else
          stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M19 14l-7 7m0 0l-7-7m7 7V3"
        />
      </svg>
      <span class="text-sm" :class="trendUp ? 'text-green-600' : 'text-red-600'">{{ trend }}</span>
      <span class="text-sm text-gray-400 ml-1">vs last month</span>
    </div>
  </div>
</template>
