<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { aiService } from '../services/ai.service'
import type { AIPredictionResponse, AIInputData } from '../types/ai'
import AIPredictionCard from '../components/ai/AIPredictionCard.vue'

const { t } = useI18n()

const formData = ref<AIInputData>({
  activity_count_30d: 10,
  days_since_last_contact: 5,
  total_deal_value: 1000,
  interaction_score: 0.5,
})

const leadResult = ref<AIPredictionResponse | null>(null)
const churnResult = ref<AIPredictionResponse | null>(null)
const loading = ref(false)
const error = ref('')
const contactIdInput = ref('')

const runAnalysis = async () => {
  loading.value = true
  error.value = ''
  try {
    const [lead, churn] = await Promise.all([aiService.scoreLead(formData.value), aiService.predictChurn(formData.value)])
    leadResult.value = lead
    churnResult.value = churn
  } catch (e: unknown) {
    const detail =
      e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : undefined
    error.value = detail || t('aiLab.errors.aiService')
  } finally {
    loading.value = false
  }
}

const runAutomatedAnalysis = async () => {
  if (!contactIdInput.value) {
    error.value = t('aiLab.contactIdRequired')
    return
  }
  loading.value = true
  error.value = ''
  try {
    const result = await aiService.analyzeContact(contactIdInput.value)
    leadResult.value = result.analysis.lead_conversion
    churnResult.value = result.analysis.churn_risk
    formData.value = { ...result.features }
  } catch (e: unknown) {
    const detail =
      e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : undefined
    error.value = detail || t('aiLab.errors.contactAi')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 p-8">
    <div class="max-w-6xl mx-auto">
      <header class="mb-12">
        <h1 class="text-3xl font-extrabold text-gray-900 mb-2">{{ t('aiLab.title') }}</h1>
        <p class="text-gray-500">{{ t('aiLab.subtitle') }}</p>
      </header>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-1 space-y-6">
          <div class="bg-indigo-900 p-8 rounded-2xl shadow-lg text-white">
            <h2 class="text-xl font-bold mb-4">{{ t('aiLab.automatedTitle') }}</h2>
            <p class="text-indigo-200 text-sm mb-6">{{ t('aiLab.automatedHint') }}</p>
            <div class="space-y-4">
              <input
                v-model="contactIdInput"
                type="text"
                placeholder="e.g. contact_1"
                class="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/20 text-white placeholder-indigo-300 outline-none focus:ring-2 focus:ring-white/50"
              />
              <button
                @click="runAutomatedAnalysis"
                :disabled="loading"
                class="w-full py-3 bg-white text-indigo-900 rounded-xl font-bold hover:bg-indigo-50 transition-colors disabled:opacity-50"
              >
                {{ t('aiLab.fetchAnalyze') }}
              </button>
            </div>
          </div>

          <div class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
            <h2 class="text-xl font-bold mb-6 text-gray-800">{{ t('aiLab.manualTitle') }}</h2>
            <div class="space-y-6">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('aiLab.activities') }}</label>
                <input
                  v-model="formData.activity_count_30d"
                  type="number"
                  class="w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('aiLab.daysSince') }}</label>
                <input
                  v-model="formData.days_since_last_contact"
                  type="number"
                  class="w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('aiLab.dealValue') }}</label>
                <input
                  v-model="formData.total_deal_value"
                  type="number"
                  class="w-full px-4 py-2 rounded-lg border focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('aiLab.interactionScore') }}</label>
                <input
                  v-model="formData.interaction_score"
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div class="text-right text-xs font-mono mt-1 text-gray-500">{{ formData.interaction_score }}</div>
              </div>

              <button
                @click="runAnalysis"
                :disabled="loading"
                class="w-full py-3 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-colors disabled:opacity-50"
              >
                {{ loading ? t('aiLab.analyzing') : t('aiLab.runAnalysis') }}
              </button>

              <p v-if="error" class="text-red-500 text-sm mt-4 text-center">{{ error }}</p>
            </div>
          </div>
        </div>

        <div class="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-8">
          <AIPredictionCard :title="t('aiLab.leadCard')" :prediction="leadResult" :loading="loading" />
          <AIPredictionCard :title="t('aiLab.churnCard')" :prediction="churnResult" :loading="loading" />
        </div>
      </div>
    </div>
  </div>
</template>
