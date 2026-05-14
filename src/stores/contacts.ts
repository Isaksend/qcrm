import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Contact } from '../types'
import { apiUrl } from '../lib/api'
import { useAuthStore } from './auth'
import { canonicalPhoneForStorage, normalizePhoneDigits } from '../lib/phone'

export const useContactsStore = defineStore('contacts', () => {
  const authStore = useAuthStore()
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
      const response = await fetch(apiUrl('/api/contacts'), {
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

  function contactsAuthHeader(): Record<string, string> {
    const t = authStore.token || localStorage.getItem('token')
    return t ? { Authorization: `Bearer ${t}` } : {}
  }

  async function searchContactByPhone(phone: string) {
    try {
      const response = await fetch(apiUrl(`/api/contacts/search?phone=${encodeURIComponent(phone)}`), {
        headers: contactsAuthHeader(),
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
      const response = await fetch(apiUrl('/api/contacts'), {
        headers: contactsAuthHeader(),
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

  /**
   * Для формы сделки: найти контакт по телефону (любой формат) или создать без дублей по телефону/email.
   */
  async function findOrCreateContactForDeal(payload: {
    phone: string
    name: string
    email?: string
    company?: string
    country_iso2?: string | null
    city?: string | null
  }): Promise<{ contact: Contact | null; error?: string }> {
    const authStore = useAuthStore()
    const token = authStore.token
    if (!token) return { contact: null, error: 'Нет авторизации' }

    const name = payload.name.trim()
    if (!name) return { contact: null, error: 'Укажите имя контакта' }

    const digits = normalizePhoneDigits(payload.phone)
    if (digits.length < 7) {
      return { contact: null, error: 'Введите телефон (не меньше 7 цифр)' }
    }

    const variants = [payload.phone.trim(), `+${digits}`, digits]
    const seen = new Set<string>()
    for (const p of variants) {
      if (seen.has(p)) continue
      seen.add(p)
      const found = await searchContactByPhone(p)
      if (found) {
        if (!contacts.value.some((c) => c.id === found.id)) contacts.value.push(found)
        return { contact: found }
      }
    }

    await fetchContacts()
    const localByDigits = contacts.value.find((c) => normalizePhoneDigits(c.phone) === digits)
    if (localByDigits) return { contact: localByDigits }

    let email = (payload.email ?? '').trim()
    const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    if (!emailValid) {
      email = `tinycrm.${digits}.${crypto.randomUUID().slice(0, 8)}@noreply.invalid`
    } else {
      const dupEmail = contacts.value.find((c) => c.email.toLowerCase() === email.toLowerCase())
      // Только тот же контакт (email + те же цифры телефона). Иначе — создаём новую запись с уникальным email.
      if (dupEmail && normalizePhoneDigits(dupEmail.phone) === digits) {
        return { contact: dupEmail }
      }
      if (dupEmail) {
        email = `tinycrm.${digits}.${crypto.randomUUID().slice(0, 8)}@noreply.invalid`
      }
    }

    const phoneStored = canonicalPhoneForStorage(payload.phone)
    const avatar = name
      .split(' ')
      .map((w) => w[0])
      .join('')
      .slice(0, 2)
      .toUpperCase()

    const body = {
      name,
      email,
      phone: phoneStored,
      company: (payload.company ?? '').trim(),
      role: 'Lead',
      status: 'Prospect' as Contact['status'],
      revenue: 0,
      lastContact: new Date().toISOString().split('T')[0],
      tags: [] as string[],
      avatar,
      country_iso2: payload.country_iso2 || null,
      city: payload.city || null,
    }

    try {
      const response = await fetch(apiUrl('/api/contacts'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      })
      if (response.ok) {
        const newContact = (await response.json()) as Contact
        contacts.value.push(newContact)
        return { contact: newContact }
      }

      await fetchContacts()
      const byPhone = contacts.value.find((c) => normalizePhoneDigits(c.phone) === digits)
      if (byPhone) return { contact: byPhone }
      const byEmail = contacts.value.find((c) => c.email.toLowerCase() === email.toLowerCase())
      if (byEmail && normalizePhoneDigits(byEmail.phone) === digits) return { contact: byEmail }

      let detail = 'Не удалось создать контакт'
      try {
        const err = await response.json()
        if (err.detail) detail = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail)
      } catch {
        /* ignore */
      }
      return { contact: null, error: detail }
    } catch (e) {
      console.error(e)
      return { contact: null, error: 'Ошибка сети при создании контакта' }
    }
  }

  async function updateContact(id: string, patch: Partial<Contact>) {
    const token = authStore.token
    if (!token) return null
    try {
      const response = await fetch(apiUrl(`/api/contacts/${id}`), {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(patch),
      })
      if (!response.ok) return null
      const updated = (await response.json()) as Contact
      const i = contacts.value.findIndex((c) => c.id === id)
      if (i >= 0) contacts.value[i] = updated
      return updated
    } catch (e) {
      console.error(e)
      return null
    }
  }

  async function deleteContact(id: string) {
    const token = authStore.token
    if (!token) return false
    try {
      const response = await fetch(apiUrl(`/api/contacts/${id}`), {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) return false
      contacts.value = contacts.value.filter((c) => c.id !== id)
      if (selectedContactId.value === id) selectedContactId.value = null
      return true
    } catch (e) {
      console.error(e)
      return false
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
    findOrCreateContactForDeal,
    updateContact,
    deleteContact,
  }
})
