<script setup lang="ts">
import { computed } from 'vue';
import type { AIPredictionResponse } from '../../types/ai';

const props = defineProps<{
  title: string;
  prediction: AIPredictionResponse | null;
  loading: boolean;
}>();

const riskColor = computed(() => {
  if (!props.prediction) return 'bg-gray-400';
  switch (props.prediction.risk_category) {
    case 'High': return 'bg-red-500';
    case 'Medium': return 'bg-yellow-500';
    case 'Low': return 'bg-green-500';
    default: return 'bg-blue-500';
  }
});

const formatFeatureName = (name: string) => {
  return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
};
</script>

<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 transition-all hover:shadow-md">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-lg font-semibold text-gray-800">{{ title }}</h3>
      <div v-if="prediction" :class="[riskColor, 'px-3 py-1 rounded-full text-white text-xs font-bold uppercase tracking-wider']">
        {{ prediction.risk_category }} RISK
      </div>
    </div>

    <div v-if="loading" class="animate-pulse space-y-4">
      <div class="h-4 bg-gray-200 rounded w-3/4"></div>
      <div class="h-20 bg-gray-100 rounded"></div>
    </div>

    <div v-else-if="prediction" class="space-y-6">
      <!-- Probability Gauge -->
      <div>
        <div class="flex justify-between mb-2">
          <span class="text-sm font-medium text-gray-600">Confidence Score</span>
          <span class="text-sm font-bold text-gray-900">{{ prediction.probability }}%</span>
        </div>
        <div class="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
          <div 
            class="h-full transition-all duration-1000 ease-out"
            :class="riskColor"
            :style="{ width: `${prediction.probability}%` }"
          ></div>
        </div>
      </div>

      <!-- SHAP Factors (Explainable AI) -->
      <div>
        <h4 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">Key Influence Factors</h4>
        <div class="space-y-3">
          <div 
            v-for="factor in prediction.top_factors" 
            :key="factor.feature"
            class="flex items-center p-3 rounded-xl border border-gray-50 bg-gray-50/50"
          >
            <div 
              class="w-1.5 h-8 rounded-full mr-4"
              :class="factor.impact > 0 ? 'bg-indigo-400' : 'bg-orange-400'"
            ></div>
            <div class="flex-1">
              <div class="text-sm font-medium text-gray-700">
                {{ formatFeatureName(factor.feature) }}
              </div>
              <div class="text-xs text-gray-500">
                {{ factor.impact > 0 ? 'Positive' : 'Negative' }} impact on score
              </div>
            </div>
            <div class="text-xs font-mono font-bold" :class="factor.impact > 0 ? 'text-indigo-600' : 'text-orange-600'">
              {{ factor.impact > 0 ? '+' : '' }}{{ factor.impact.toFixed(2) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-8">
      <div class="text-gray-300 mb-2">
        <svg class="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </div>
      <p class="text-sm text-gray-400 font-medium">Ready for AI Analysis</p>
    </div>
  </div>
</template>

<style scoped>
.transition-all {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
