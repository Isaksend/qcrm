<script setup lang="ts">
import { reactive } from 'vue'
import { useContactsStore } from '../../stores/contacts'

const emit = defineEmits<{ close: [] }>()
const store = useContactsStore()

const form = reactive({
  name: '',
  email: '',
  phone: '',
  company: '',
  role: '',
  status: 'Prospect' as 'Active' | 'Inactive' | 'Prospect',
  revenue: 0,
  lastContact: new Date().toISOString().slice(0, 10),
  tags: '',
})

function submit() {
  if (!form.name || !form.email || !form.company) return
  store.addContact({
    name: form.name,
    email: form.email,
    phone: form.phone,
    company: form.company,
    role: form.role,
    status: form.status,
    revenue: Number(form.revenue) || 0,
    lastContact: form.lastContact,
    tags: form.tags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean),
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
            <h2 class="text-lg font-semibold text-gray-900">New Contact</h2>
            <button @click="$emit('close')" class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>

          <form @submit.prevent="submit" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="col-span-2">
                <label class="block text-xs font-medium text-gray-600 mb-1">Full Name *</label>
                <input v-model="form.name" type="text" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="Jane Smith" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Email *</label>
                <input v-model="form.email" type="email" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="jane@company.com" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Phone</label>
                <input v-model="form.phone" type="text" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="+1 (555) 000-0000" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Company *</label>
                <input v-model="form.company" type="text" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="Acme Inc." />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Role</label>
                <input v-model="form.role" type="text" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="VP of Sales" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Status</label>
                <select v-model="form.status" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white">
                  <option value="Prospect">Prospect</option>
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Revenue ($)</label>
                <input v-model.number="form.revenue" type="number" min="0" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="0" />
              </div>
              <div class="col-span-2">
                <label class="block text-xs font-medium text-gray-600 mb-1">Tags</label>
                <input v-model="form.tags" type="text" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="Enterprise, Tech, Decision Maker" />
                <p class="text-xs text-gray-400 mt-1">Comma-separated</p>
              </div>
            </div>

            <div class="flex justify-end gap-3 pt-2">
              <button type="button" @click="$emit('close')" class="btn-secondary">Cancel</button>
              <button type="submit" class="btn-primary">Create Contact</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>
</template>
