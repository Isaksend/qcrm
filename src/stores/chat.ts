import { defineStore } from 'pinia'
import { ref } from 'vue'

const API_URL = 'http://127.0.0.1:8000/api'

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
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const activeContactId = ref<string | null>(null)
  let pollInterval: ReturnType<typeof setInterval> | null = null

  function getHeaders() {
    return {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    }
  }

  async function fetchMessages(contactId: string) {
    isLoading.value = true
    activeContactId.value = contactId
    try {
      const res = await fetch(`${API_URL}/chat/${contactId}`, {
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
      const res = await fetch(`${API_URL}/chat/send`, {
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

  function startPolling(contactId: string, intervalMs = 3000) {
    stopPolling()
    activeContactId.value = contactId
    pollInterval = setInterval(async () => {
      if (activeContactId.value !== contactId) return
      try {
        const res = await fetch(`${API_URL}/chat/${contactId}`, {
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
