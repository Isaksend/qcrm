<script setup lang="ts">
import { useContactsStore } from '../../stores/contacts'
import { useAI } from '../../composables/useAI'
import ContactCard from './ContactCard.vue'

const store = useContactsStore()
const { analyze } = useAI()

const statuses = ['All', 'Active', 'Inactive', 'Prospect']

function handleAnalyze(contactId: string) {
  const contact = store.getContact(contactId)
  if (contact) {
    analyze('contact', contactId, { ...contact })
  }
}
</script>

<template>
  <div>
    <!-- Filters -->
    <div class="flex items-center gap-4 mb-4">
      <div class="relative flex-1 max-w-sm">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="store.searchQuery"
          type="text"
          placeholder="Search contacts..."
          class="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
        />
      </div>
      <div class="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
        <button
          v-for="status in statuses"
          :key="status"
          @click="store.statusFilter = status"
          class="px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
          :class="store.statusFilter === status ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
        >
          {{ status }}
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100">
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Contact</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Company</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Role</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Revenue</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Last Contact</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-12">AI</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <ContactCard
            v-for="contact in store.filteredContacts"
            :key="contact.id"
            :contact="contact"
            @select="store.selectedContactId = $event"
            @analyze="handleAnalyze"
          />
        </tbody>
      </table>
      <div v-if="store.filteredContacts.length === 0" class="px-4 py-12 text-center text-sm text-gray-400">
        No contacts found matching your criteria.
      </div>
    </div>
  </div>
</template>
