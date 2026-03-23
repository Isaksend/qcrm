import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AIInsight, AIMode } from '../types'
import { aiInsights } from '../data/mock'

export const useAIStore = defineStore('ai', () => {
  const mode = ref<AIMode>('demo')
  const apiKey = ref('')
  const panelOpen = ref(false)
  const panelEntityType = ref<string>('')
  const panelEntityId = ref<string>('')
  const panelLoading = ref(false)
  const panelInsight = ref<AIInsight | null>(null)
  const insights = ref<AIInsight[]>(aiInsights)
  const filterType = ref<string>('all')
  const showSettingsModal = ref(false)

  const filteredInsights = computed(() => {
    if (filterType.value === 'all') return insights.value
    return insights.value.filter((i) => i.entityType === filterType.value)
  })

  function openPanel(entityType: string, entityId: string) {
    panelEntityType.value = entityType
    panelEntityId.value = entityId
    panelOpen.value = true
    panelInsight.value = null
    panelLoading.value = true
  }

  function closePanel() {
    panelOpen.value = false
    panelLoading.value = false
    panelInsight.value = null
  }

  function setPanelInsight(insight: AIInsight) {
    panelInsight.value = insight
    panelLoading.value = false
  }

  function toggleMode() {
    mode.value = mode.value === 'demo' ? 'live' : 'demo'
  }

  return {
    mode,
    apiKey,
    panelOpen,
    panelEntityType,
    panelEntityId,
    panelLoading,
    panelInsight,
    insights,
    filterType,
    showSettingsModal,
    filteredInsights,
    openPanel,
    closePanel,
    setPanelInsight,
    toggleMode,
  }
})
