import { useAIStore } from '../stores/ai'
import { getDemoInsight, getLiveInsight } from '../services/ai'

export function useAI() {
  const aiStore = useAIStore()

  async function analyze(
    entityType: string,
    entityId: string,
    entityData?: Record<string, unknown>
  ) {
    aiStore.openPanel(entityType, entityId)

    try {
      let insight
      if (aiStore.mode === 'demo') {
        insight = await getDemoInsight(entityType, entityId)
      } else {
        if (!aiStore.apiKey) {
          aiStore.showSettingsModal = true
          aiStore.closePanel()
          return
        }
        insight = await getLiveInsight(
          entityType,
          entityData ?? { id: entityId },
          aiStore.apiKey
        )
      }
      aiStore.setPanelInsight(insight)
    } catch (error) {
      aiStore.setPanelInsight({
        id: `ai-error-${Date.now()}`,
        entityType: entityType as any,
        entityId,
        category: 'analysis',
        title: 'Analysis Error',
        content: `Failed to generate insight: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again or switch to demo mode.`,
        confidence: 0,
        suggestions: ['Check your API key', 'Try demo mode', 'Retry analysis'],
      })
    }
  }

  return { analyze }
}
