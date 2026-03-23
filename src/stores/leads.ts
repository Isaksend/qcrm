import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Lead } from '../types'
import { leads as mockLeads } from '../data/mock'

export const useLeadsStore = defineStore('leads', () => {
  const leads = ref<Lead[]>(mockLeads)

  const stages = ['New', 'Qualified', 'Proposal', 'Negotiation', 'Won', 'Lost'] as const

  const leadsByStage = computed(() => {
    const grouped: Record<string, Lead[]> = {}
    for (const stage of stages) {
      grouped[stage] = leads.value.filter((l) => l.stage === stage)
    }
    return grouped
  })

  const activeLeads = computed(() =>
    leads.value.filter((l) => l.stage !== 'Won' && l.stage !== 'Lost')
  )

  const totalPipelineValue = computed(() =>
    activeLeads.value.reduce((sum, l) => sum + l.value, 0)
  )

  const weightedPipelineValue = computed(() =>
    activeLeads.value.reduce((sum, l) => sum + l.value * (l.probability / 100), 0)
  )

  const wonDealsValue = computed(() =>
    leads.value
      .filter((l) => l.stage === 'Won')
      .reduce((sum, l) => sum + l.value, 0)
  )

  function getLead(id: string) {
    return leads.value.find((l) => l.id === id)
  }

  function addLead(data: Omit<Lead, 'id'>) {
    const id = `l${Date.now()}`
    leads.value.push({ ...data, id })
  }

  return {
    leads,
    stages,
    leadsByStage,
    activeLeads,
    totalPipelineValue,
    weightedPipelineValue,
    wonDealsValue,
    getLead,
    addLead,
  }
})
