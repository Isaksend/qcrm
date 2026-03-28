<script setup lang="ts">
import { useContactsStore } from '../../stores/contacts'
import { useDealsStore } from '../../stores/deals'
import { useAI } from '../../composables/useAI'
import { computed } from 'vue'

const contactsStore = useContactsStore()
const dealsStore = useDealsStore()
const { analyze } = useAI()

const contact = computed(() => contactsStore.selectedContact)

const contactDeals = computed(() => {
  if (!contact.value) return []
  return dealsStore.deals.filter((d) => d.contactId === contact.value!.id)
})

const statusClass: Record<string, string> = {
  Active: 'badge-green',
  Inactive: 'badge-red',
  Prospect: 'badge-yellow',
}

const stageClass: Record<string, string> = {
  'New Request': 'badge-blue',
  'Qualified': 'badge-indigo',
  'Discovery': 'badge-blue',
  'Proposal': 'badge-yellow',
  'Negotiation': 'badge-yellow',
  'Closed Won': 'badge-green',
  'Closed Lost': 'badge-red',
}

function formatCurrency(val: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val)
}

function handleAnalyze() {
  if (contact.value) {
    analyze('contact', contact.value.id, { ...contact.value })
  }
}
</script>

<template>
  <div
    v-if="contact"
    class="fixed inset-0 z-30 flex justify-end"
  >
    <div class="absolute inset-0 bg-black/20" @click="contactsStore.selectedContactId = null"></div>
    <div class="relative w-full max-w-lg bg-white shadow-xl overflow-y-auto animate-slide-in">
      <div class="p-6">
        <!-- Header -->
        <div class="flex items-start justify-between mb-6">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 rounded-full bg-indigo-100 flex items-center justify-center">
              <span class="text-indigo-600 text-lg font-semibold">{{ contact.avatar }}</span>
            </div>
            <div>
              <h2 class="text-lg font-semibold text-gray-900">{{ contact.name }}</h2>
              <p class="text-sm text-gray-500">{{ contact.role }} at {{ contact.company }}</p>
              <span class="badge mt-1" :class="statusClass[contact.status]">{{ contact.status }}</span>
            </div>
          </div>
          <button
            @click="contactsStore.selectedContactId = null"
            class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Contact Info -->
        <div class="space-y-3 mb-6">
          <div class="flex items-center gap-3 text-sm">
            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span class="text-gray-600">{{ contact.email }}</span>
          </div>
          <div class="flex items-center gap-3 text-sm">
            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <span class="text-gray-600">{{ contact.phone }}</span>
          </div>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-2 gap-4 mb-6">
          <div class="bg-gray-50 rounded-lg p-3">
            <div class="text-xs text-gray-500 mb-1">Total Revenue</div>
            <div class="text-lg font-semibold text-gray-900">{{ formatCurrency(contact.revenue) }}</div>
          </div>
          <div class="bg-gray-50 rounded-lg p-3">
            <div class="text-xs text-gray-500 mb-1">Last Contact</div>
            <div class="text-lg font-semibold text-gray-900">{{ contact.lastContact }}</div>
          </div>
        </div>

        <!-- Tags -->
        <div class="mb-6">
          <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Tags</h3>
          <div class="flex flex-wrap gap-2">
            <span v-for="tag in contact.tags" :key="tag" class="badge badge-indigo">{{ tag }}</span>
          </div>
        </div>

        <!-- Related Deals -->
        <div class="mb-6">
          <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Related Deals</h3>
          <div v-if="contactDeals.length" class="space-y-2">
            <div
              v-for="deal in contactDeals"
              :key="deal.id"
              class="flex items-center justify-between bg-gray-50 rounded-lg p-3"
            >
              <div>
                <div class="text-sm font-medium text-gray-800">{{ deal.title }}</div>
                <span class="badge mt-1" :class="stageClass[deal.stage]">{{ deal.stage }}</span>
              </div>
              <div class="text-sm font-semibold text-gray-700">{{ formatCurrency(deal.value) }}</div>
            </div>
          </div>
          <p v-else class="text-sm text-gray-400">No related deals.</p>
        </div>

        <!-- AI Button -->
        <button @click="handleAnalyze" class="btn-primary w-full justify-center">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
          </svg>
          Analyze with AI
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-slide-in {
  animation: slideIn 0.25s ease-out;
}
@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}
</style>
