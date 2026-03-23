<script setup lang="ts">
import { reactive } from 'vue'
import { useDealsStore } from '../../stores/deals'
import { useContactsStore } from '../../stores/contacts'
import { useSellersStore } from '../../stores/sellers'
import { useLeadsStore } from '../../stores/leads'
import type { Deal } from '../../types'

const emit = defineEmits<{ close: [] }>()
const dealsStore = useDealsStore()
const contactsStore = useContactsStore()
const sellersStore = useSellersStore()
const leadsStore = useLeadsStore()

const form = reactive({
  leadId: '',
  contactId: '',
  title: '',
  value: 0,
  stage: 'Discovery' as Deal['stage'],
  sellerId: '',
})

function submit() {
  if (!form.title || !form.contactId || !form.sellerId) return
  dealsStore.addDeal({
    leadId: form.leadId,
    contactId: form.contactId,
    title: form.title,
    value: Number(form.value) || 0,
    stage: form.stage,
    closedAt: form.stage === 'Closed Won' || form.stage === 'Closed Lost'
      ? new Date().toISOString().slice(0, 10)
      : null,
    sellerId: form.sellerId,
  })
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/30" @click="$emit('close')"></div>
      <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-semibold text-gray-900">New Deal</h2>
            <button @click="$emit('close')" class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>

          <form @submit.prevent="submit" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="col-span-2">
                <label class="block text-xs font-medium text-gray-600 mb-1">Deal Title *</label>
                <input v-model="form.title" type="text" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="Platform License" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Contact *</label>
                <select v-model="form.contactId" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white">
                  <option value="" disabled>Select contact</option>
                  <option v-for="c in contactsStore.contacts" :key="c.id" :value="c.id">{{ c.name }} — {{ c.company }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Seller *</label>
                <select v-model="form.sellerId" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white">
                  <option value="" disabled>Select seller</option>
                  <option v-for="s in sellersStore.sellers" :key="s.id" :value="s.id">{{ s.name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Related Lead</label>
                <select v-model="form.leadId" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white">
                  <option value="">None</option>
                  <option v-for="l in leadsStore.leads" :key="l.id" :value="l.id">{{ l.title }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Value ($)</label>
                <input v-model.number="form.value" type="number" min="0" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="100000" />
              </div>
              <div class="col-span-2">
                <label class="block text-xs font-medium text-gray-600 mb-1">Stage</label>
                <select v-model="form.stage" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white">
                  <option value="Discovery">Discovery</option>
                  <option value="Proposal">Proposal</option>
                  <option value="Negotiation">Negotiation</option>
                  <option value="Closed Won">Closed Won</option>
                  <option value="Closed Lost">Closed Lost</option>
                </select>
              </div>
            </div>

            <div class="flex justify-end gap-3 pt-2">
              <button type="button" @click="$emit('close')" class="btn-secondary">Cancel</button>
              <button type="submit" class="btn-primary">Create Deal</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>
</template>
