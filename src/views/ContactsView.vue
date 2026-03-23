<script setup lang="ts">
import { ref } from 'vue'
import ContactList from '../components/contacts/ContactList.vue'
import ContactDetail from '../components/contacts/ContactDetail.vue'
import ContactForm from '../components/contacts/ContactForm.vue'

const showForm = ref(false)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Contacts</h1>
        <p class="text-sm text-gray-500 mt-1">Manage your contacts and customer relationships.</p>
      </div>
      <button @click="showForm = true" class="btn-primary">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>
        New Contact
      </button>
    </div>

    <ContactList />
    <ContactDetail />
    <ContactForm v-if="showForm" @close="showForm = false" />
  </div>
</template>
