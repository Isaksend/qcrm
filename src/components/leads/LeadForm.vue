<script setup lang="ts">
import { reactive } from 'vue'
import { useLeadsStore } from '../../stores/leads'
import { useContactsStore } from '../../stores/contacts'
import { useSellersStore } from '../../stores/sellers'
import type { Lead } from '../../types'

const emit = defineEmits<{ close: [] }>()
const leadsStore = useLeadsStore()
const contactsStore = useContactsStore()
const sellersStore = useSellersStore()

const form = reactive({
  contactId: '',
  title: '',
  value: 0,
  stage: 'New' as Lead['stage'],
  probability: 20,
  source: '',
  assignedTo: '',
  notes: '',
})

function submit() {
  if (!form.title || !form.contactId || !form.assignedTo) return
  leadsStore.addLead({
    contactId: form.contactId,
    title: form.title,
    value: Number(form.value) || 0,
    stage: form.stage,
    probability: Number(form.probability) || 0,
    source: form.source,
    assignedTo: form.assignedTo,
    createdAt: new Date().toISOString().slice(0, 10),
    notes: form.notes,
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
            <h2 class="text-lg font-semibold text-gray-900">New Lead</h2>
            <button @click="$emit('close')" class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>

          <form @submit.prevent="submit" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="col-span-2">
                <label class="block text-xs font-medium text-gray-600 mb-1">Title *</label>
                <input v-model="form.title" type="text" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="Enterprise License Deal" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Contact *</label>
                <select v-model="form.contactId" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white">
                  <option value="" disabled>Select contact</option>
                  <option v-for="c in contactsStore.contacts" :key="c.id" :value="c.id">{{ c.name }} — {{ c.company }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Assigned Seller *</label>
                <select v-model="form.assignedTo" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white">
                  <option value="" disabled>Select seller</option>
                  <option v-for="s in sellersStore.sellers" :key="s.id" :value="s.id">{{ s.name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Value ($)</label>
                <input v-model.number="form.value" type="number" min="0" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="50000" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Stage</label>
                <select v-model="form.stage" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white">
                  <option value="New">New</option>
                  <option value="Qualified">Qualified</option>
                  <option value="Proposal">Proposal</option>
                  <option value="Negotiation">Negotiation</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Probability (%)</label>
                <input v-model.number="form.probability" type="number" min="0" max="100" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Source</label>
                <input v-model="form.source" type="text" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="Referral, Website, etc." />
              </div>
              <div class="col-span-2">
                <label class="block text-xs font-medium text-gray-600 mb-1">Notes</label>
                <textarea v-model="form.notes" rows="3" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none" placeholder="Any additional notes..."></textarea>
              </div>
            </div>

            <div class="flex justify-end gap-3 pt-2">
              <button type="button" @click="$emit('close')" class="btn-secondary">Cancel</button>
              <button type="submit" class="btn-primary">Create Lead</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>
</template>
