import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Contact } from '../types'
const API_URL = '/api'

export const useContactsStore = defineStore('contacts', () => {
  const contacts = ref<Contact[]>([])
  const isLoading = ref(false)
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

  async function addContact(data: Omit<Contact, 'id' | 'avatar'>) {
    const avatar = data.name
      .split(' ')
      .map((w) => w[0])
      .join('')
      .slice(0, 2)
      .toUpperCase()
    
    const payload = { ...data, avatar }

    try {
      const response = await fetch(`${API_URL}/contacts`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload)
      })
      if (response.ok) {
        const newContact = await response.json()
        contacts.value.push(newContact)
        return newContact
      } else {
        console.error('Failed to save contact via API')
        return null
      }
    } catch (e) {
      console.error(e)
      return null
    }
  }

  async function searchContactByPhone(phone: string) {
    try {
      const response = await fetch(`${API_URL}/contacts/search?phone=${encodeURIComponent(phone)}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      })
      if (response.ok) {
        return await response.json()
      }
      return null
    } catch (e) {
      console.error(e)
      return null
    }
  }

  async function fetchContacts() {
    isLoading.value = true
    try {
      const response = await fetch(`${API_URL}/contacts`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      })
      if (response.ok) {
        contacts.value = await response.json()
      }
    } catch (e) {
      console.error(e)
    } finally {
      isLoading.value = false
    }
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
    isLoading,
    getContact,
    addContact,
    searchContactByPhone,
    fetchContacts,
  }
})
