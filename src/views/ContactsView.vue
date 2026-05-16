<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useContactsStore } from '../stores/contacts'
import ContactList from '../components/contacts/ContactList.vue'
import ContactDetail from '../components/contacts/ContactDetail.vue'
import ContactForm from '../components/contacts/ContactForm.vue'

const { t } = useI18n()
const route = useRoute()
const contactsStore = useContactsStore()
const showForm = ref(false)

function applyContactFromQuery() {
  const raw = route.query.contactId
  const id = typeof raw === 'string' ? raw : Array.isArray(raw) ? raw[0] : null
  if (!id) return
  contactsStore.selectedContactId = id
  contactsStore.statusFilter = 'All'
  contactsStore.searchQuery = ''
}

onMounted(async () => {
  await contactsStore.fetchContacts()
  applyContactFromQuery()
})

watch(() => route.query.contactId, applyContactFromQuery)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ t('contacts.title') }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ t('contacts.subtitle') }}</p>
      </div>
      <button @click="showForm = true" class="btn-primary">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        {{ t('contacts.newContact') }}
      </button>
    </div>

    <ContactList />
    <ContactDetail />
    <ContactForm v-if="showForm" @close="showForm = false" />
  </div>
</template>
