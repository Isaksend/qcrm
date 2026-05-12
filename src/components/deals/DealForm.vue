<script setup lang="ts">
import { reactive, onMounted, ref, watch } from 'vue'
import { useDealsStore } from '../../stores/deals'
import { useContactsStore } from '../../stores/contacts'
import { useAuthStore } from '../../stores/auth'
import type { Deal } from '../../types'

const emit = defineEmits<{ close: [] }>()
const dealsStore = useDealsStore()
const contactsStore = useContactsStore()
const authStore = useAuthStore()

const teamMembers = ref<any[]>([])
const showNewContactFields = ref(false)
const contactFound = ref(false)

const form = reactive({
  title: '',
  value: 0,
  stage: 'New Request' as Deal['stage'],
  userId: '',
  contactId: '',
  notes: '',
  // Fields for new contact
  contactPhone: '',
  contactName: '',
  contactEmail: '',
  contactCompany: '',
})

async function fetchTeamMembers() {
  if (authStore.userRole === 'admin' || authStore.userRole === 'super_admin') {
    try {
      const res = await fetch('/api/users', {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      if (res.ok) teamMembers.value = await res.json()
    } catch (e) { console.error(e) }
  } else {
    teamMembers.value = authStore.user ? [authStore.user] : []
  }
}

watch(() => form.contactPhone, async (newPhone) => {
  if (newPhone.length >= 10) {
    const contact = await contactsStore.searchContactByPhone(newPhone)
    if (contact) {
      form.contactId = contact.id
      form.contactName = contact.name
      form.contactEmail = contact.email
      form.contactCompany = contact.company
      contactFound.value = true
      showNewContactFields.value = true
    } else {
      contactFound.value = false
      if (!form.contactId) showNewContactFields.value = true
    }
  }
})

async function submit() {
  if (!form.title) return

  let finalContactId = form.contactId

  // Create contact if it's a new one
  if (!finalContactId && form.contactPhone && form.contactName) {
    const newContact = await contactsStore.addContact({
      name: form.contactName,
      email: form.contactEmail,
      phone: form.contactPhone,
      company: form.contactCompany,
      role: 'Lead',
      status: 'Prospect',
      revenue: 0,
      lastContact: new Date().toISOString().split('T')[0],
      tags: []
    })
    if (newContact) finalContactId = newContact.id
  }

  if (!finalContactId) {
    alert('Please select or create a contact')
    return
  }

  await dealsStore.addDeal({
    leadId: '',
    contactId: finalContactId,
    title: form.title,
    value: Number(form.value) || 0,
    stage: form.stage,
    closedAt: form.stage === 'Closed Won' || form.stage === 'Closed Lost'
      ? new Date().toISOString().slice(0, 10)
      : null,
    userId: form.userId || authStore.user?.id || '',
    companyId: authStore.user?.company_id || null,
    notes: form.notes,
  })
  emit('close')
}

onMounted(() => {
  fetchTeamMembers()
})
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/30" @click="$emit('close')"></div>
      <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-semibold text-gray-900">New Deal & Contact</h2>
            <button @click="$emit('close')" class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>

          <form @submit.prevent="submit" class="space-y-4">
            <!-- Deal Details -->
            <div class="bg-indigo-50/50 p-4 rounded-xl space-y-3 mb-4 border border-indigo-100">
              <h3 class="text-xs font-bold text-indigo-900 uppercase tracking-wider">Deal Information</h3>
              <div class="grid grid-cols-2 gap-4">
                <div class="col-span-2">
                  <label class="block text-xs font-medium text-gray-600 mb-1">Deal Title *</label>
                  <input v-model="form.title" type="text" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="Platform License" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Value ($)</label>
                  <input v-model.number="form.value" type="number" min="0" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="100000" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Assigned To</label>
                  <select v-model="form.userId" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white">
                    <option value="">Me (default)</option>
                    <option v-for="m in teamMembers" :key="m.id" :value="m.id">{{ m.name }}</option>
                  </select>
                </div>
                <div class="col-span-2">
                  <label class="block text-xs font-medium text-gray-600 mb-1">Notes / Description</label>
                  <textarea v-model="form.notes" rows="3" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none" placeholder="Details about this deal..."></textarea>
                </div>
              </div>
            </div>

            <!-- Contact Search/Create -->
            <div class="bg-gray-50 p-4 rounded-xl space-y-3 border border-gray-100">
              <h3 class="text-xs font-bold text-gray-900 uppercase tracking-wider">Contact Link</h3>
              
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Search or New Phone*</label>
                <input v-model="form.contactPhone" type="tel" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" placeholder="+7 (___) ___ - __ - __" />
              </div>

              <div v-if="showNewContactFields" class="space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                <div v-if="contactFound" class="bg-green-50 text-green-700 text-[10px] font-bold py-1 px-2 rounded mb-2">
                  MATCHING CONTACT FOUND
                </div>
                
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Name *</label>
                  <input v-model="form.contactName" type="text" :disabled="contactFound" required class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none disabled:bg-gray-100" />
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">Email</label>
                    <input v-model="form.contactEmail" type="email" :disabled="contactFound" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none disabled:bg-gray-100" />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">Company</label>
                    <input v-model="form.contactCompany" type="text" :disabled="contactFound" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none disabled:bg-gray-100" />
                  </div>
                </div>
              </div>
              
              <div v-else class="text-xs text-gray-400 italic">
                Enter phone number to find or create contact...
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
