import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiUrl } from '../lib/api'
import { useAuthStore } from './auth'

interface ChatMessage {
  id: string
  contactId: string
  dealId: string | null
  senderRole: 'manager' | 'client'
  senderId: string | null
  senderName: string
  content: string
  messageType: 'text' | 'image'
  timestamp: string
}

export const useChatStore = defineStore('chat', () => {
  const authStore = useAuthStore()
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const activeContactId = ref<string | null>(null)
  const activeDealIdForChat = ref<string | null>(null)
  let pollInterval: ReturnType<typeof setInterval> | null = null

  function getHeaders() {
    const token = authStore.token || localStorage.getItem('token')
    return {
      Authorization: `Bearer ${token || ''}`,
      'Content-Type': 'application/json',
    }
  }

  async function fetchMessages(contactId: string, dealId?: string | null) {
    isLoading.value = true
    activeContactId.value = contactId
    activeDealIdForChat.value = dealId || null
    try {
      const q =
        dealId && String(dealId).trim() !== ''
          ? `?dealId=${encodeURIComponent(String(dealId).trim())}`
          : ''
      const res = await fetch(apiUrl(`/api/chat/${contactId}${q}`), {
        headers: getHeaders(),
      })
      if (res.ok) {
        messages.value = await res.json()
      }
    } catch (e) {
      console.error('Failed to fetch chat history', e)
    } finally {
      isLoading.value = false
    }
  }

  async function sendMessage(contactId: string, content: string, dealId?: string) {
    try {
      const res = await fetch(apiUrl('/api/chat/send'), {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ contactId, content, dealId: dealId || null }),
      })
      if (res.ok) {
        const saved = await res.json()
        messages.value.push(saved)
        return saved
      } else {
        const err = await res.json()
        throw new Error(err.detail || 'Send failed')
      }
    } catch (e: any) {
      console.error('Failed to send message', e)
      throw e
    }
  }

  function startPolling(contactId: string, dealId?: string | null, intervalMs = 3000) {
    stopPolling()
    activeContactId.value = contactId
    activeDealIdForChat.value = dealId || null
    pollInterval = setInterval(async () => {
      if (activeContactId.value !== contactId) return
      try {
        const q =
          activeDealIdForChat.value && String(activeDealIdForChat.value).trim() !== ''
            ? `?dealId=${encodeURIComponent(String(activeDealIdForChat.value).trim())}`
            : ''
        const res = await fetch(apiUrl(`/api/chat/${contactId}${q}`), {
          headers: getHeaders(),
        })
        if (res.ok) {
          messages.value = await res.json()
        }
      } catch (e) {
        // silent retry
      }
    }, intervalMs)
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
    activeDealIdForChat.value = null
  }

  return {
    messages,
    isLoading,
    activeContactId,
    fetchMessages,
    sendMessage,
    startPolling,
    stopPolling,
  }
})
