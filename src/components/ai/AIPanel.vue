<script setup lang="ts">
import { useAIStore } from '../../stores/ai'
import AIInsightCard from './AIInsightCard.vue'

const aiStore = useAIStore()
</script>

<template>
  <!-- Slide-out AI Panel -->
  <Teleport to="body">
    <div v-if="aiStore.panelOpen" class="fixed inset-0 z-50 flex justify-end">
      <div class="absolute inset-0 bg-black/20" @click="aiStore.closePanel()"></div>
      <div class="relative w-full max-w-md bg-white shadow-xl overflow-y-auto animate-slide-in">
        <div class="p-6">
          <!-- Header -->
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
              </div>
              <h2 class="text-lg font-semibold text-gray-900">AI Analysis</h2>
              <span class="badge badge-indigo text-[10px]">{{ aiStore.mode === 'demo' ? 'Demo' : 'Live' }}</span>
            </div>
            <button
              @click="aiStore.closePanel()"
              class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Loading State -->
          <div v-if="aiStore.panelLoading" class="space-y-4">
            <div class="flex items-center gap-3 text-sm text-gray-500">
              <div class="w-5 h-5 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
              Analyzing data...
            </div>
            <div class="space-y-3">
              <div class="h-4 bg-gray-100 rounded animate-pulse w-3/4"></div>
              <div class="h-4 bg-gray-100 rounded animate-pulse w-full"></div>
              <div class="h-4 bg-gray-100 rounded animate-pulse w-5/6"></div>
              <div class="h-4 bg-gray-100 rounded animate-pulse w-2/3"></div>
            </div>
          </div>

          <!-- Insight Content -->
          <div v-else-if="aiStore.panelInsight">
            <AIInsightCard :insight="aiStore.panelInsight" />
          </div>

          <!-- Empty State -->
          <div v-else class="text-center py-12 text-sm text-gray-400">
            No analysis available.
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.animate-slide-in {
  animation: slideIn 0.25s ease-out;
}
@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}
</style>
