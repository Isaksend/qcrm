import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Contact } from '../types'
import { contacts as mockContacts } from '../data/mock'

export const useContactsStore = defineStore('contacts', () => {
  const contacts = ref<Contact[]>(mockContacts)
  const searchQuery = ref('')
  const statusFilter = ref<string>('All')
  const selectedContactId = ref<string | null>(null)

  const filteredContacts = computed(() => {
    return contacts.value.filter((c) => {
      const matchesSearch =
        !searchQuery.value ||
        c.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        c.company.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        c.email.toLowerCase().includes(searchQuery.value.toLowerCase())
      const matchesStatus =
        statusFilter.value === 'All' || c.status === statusFilter.value
      return matchesSearch && matchesStatus
    })
  })

  const selectedContact = computed(() =>
    contacts.value.find((c) => c.id === selectedContactId.value) ?? null
  )

  const totalRevenue = computed(() =>
    contacts.value.reduce((sum, c) => sum + c.revenue, 0)
  )

  const activeCount = computed(() =>
    contacts.value.filter((c) => c.status === 'Active').length
  )

  function getContact(id: string) {
    return contacts.value.find((c) => c.id === id)
  }

  function addContact(data: Omit<Contact, 'id' | 'avatar'>) {
    const id = `c${Date.now()}`
    const avatar = data.name
      .split(' ')
      .map((w) => w[0])
      .join('')
      .slice(0, 2)
      .toUpperCase()
    contacts.value.push({ ...data, id, avatar })
  }

  return {
    contacts,
    searchQuery,
    statusFilter,
    selectedContactId,
    filteredContacts,
    selectedContact,
    totalRevenue,
    activeCount,
    getContact,
    addContact,
  }
})
