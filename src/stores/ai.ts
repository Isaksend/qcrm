import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AIInsight, AIMode } from '../types'
import { apiUrl } from '../lib/api'
import { useAuthStore } from './auth'

export const useAIStore = defineStore('ai', () => {
  const authStore = useAuthStore()
  const mode = ref<AIMode>('demo')
  const apiKey = ref('')
  const panelOpen = ref(false)
  const panelEntityType = ref<string>('')
  const panelEntityId = ref<string>('')
  const panelLoading = ref(false)
  const panelInsight = ref<AIInsight | null>(null)
  const insights = ref<AIInsight[]>([])
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

  async function fetchInsights() {
    const token = authStore.token || localStorage.getItem('token')
    if (!token) return
    try {
      const response = await fetch(apiUrl('/api/insights'), {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        insights.value = await response.json()
      }
    } catch (e) {
      console.error('Failed to fetch AI insights:', e)
    }
  }

  async function saveInsight(insight: AIInsight) {
    const token = authStore.token || localStorage.getItem('token')
    if (!token) return insight
    try {
      // Remove temporary ID to let backend generate one, though backend might ignore it if it doesn't match UUID
      const payload = {
        entityType: insight.entityType,
        entityId: insight.entityId,
        category: insight.category,
        title: insight.title,
        content: insight.content,
        confidence: insight.confidence,
        suggestions: insight.suggestions
      }
      const response = await fetch(apiUrl('/api/insights'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload)
      })
      if (response.ok) {
        const saved = await response.json()
        insights.value.unshift(saved)
        return saved
      }
    } catch (e) {
      console.error('Failed to save AI insight:', e)
    }
    return insight
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
    fetchInsights,
    saveInsight,
  }
})
