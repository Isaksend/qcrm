<script setup lang="ts">
import { reactive } from 'vue'
import { useSellersStore } from '../../stores/sellers'

const emit = defineEmits<{ close: [] }>()
const store = useSellersStore()

const form = reactive({
  name: '',
  email: '',
  role: 'Account Executive',
  dealsWon: 0,
  dealsClosed: 0,
  revenue: 0,
  conversionRate: 0,
  activeLeads: 0,
})

function submit() {
  if (!form.name || !form.email) return
  store.addSeller({
    name: form.name,
    email: form.email,
    role: form.role,
    dealsWon: Number(form.dealsWon) || 0,
    dealsClosed: Number(form.dealsClosed) || 0,
    revenue: Number(form.revenue) || 0,
    conversionRate: Number(form.conversionRate) || 0,
    activeLeads: Number(form.activeLeads) || 0,
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
            <h2 class="text-lg font-semibold text-gray-900">New Seller</h2>
            <button @click="$emit('close')" class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>

          <form @submit.prevent="submit" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="col-span-2">
                <label class="block text-xs font-medium text-gray-600 mb-1">Full Name *</label>
                <input v-model="form.name" type="text" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="Alex Rivera" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Email *</label>
                <input v-model="form.email" type="email" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="alex@tinycrm.com" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Role</label>
                <select v-model="form.role" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white">
                  <option>Account Executive</option>
                  <option>Senior Account Executive</option>
                  <option>Sales Development Rep</option>
                  <option>Sales Manager</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Deals Won</label>
                <input v-model.number="form.dealsWon" type="number" min="0" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Deals Closed</label>
                <input v-model.number="form.dealsClosed" type="number" min="0" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Revenue ($)</label>
                <input v-model.number="form.revenue" type="number" min="0" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="0" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Conversion Rate (%)</label>
                <input v-model.number="form.conversionRate" type="number" min="0" max="100" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Active Leads</label>
                <input v-model.number="form.activeLeads" type="number" min="0" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" />
              </div>
            </div>

            <div class="flex justify-end gap-3 pt-2">
              <button type="button" @click="$emit('close')" class="btn-secondary">Cancel</button>
              <button type="submit" class="btn-primary">Create Seller</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>
</template>
