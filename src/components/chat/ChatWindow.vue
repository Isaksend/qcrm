<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useChatStore } from '../../stores/chat'

const props = defineProps<{
  contactId: string
  contactName: string
  telegramLinked: boolean
  dealId?: string
}>()

const chatStore = useChatStore()
const newMessage = ref('')
const isSending = ref(false)
const sendError = ref('')
const chatContainer = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)

const API_URL = 'http://127.0.0.1:8000'

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

onMounted(async () => {
  await chatStore.fetchMessages(props.contactId)
  scrollToBottom()
  chatStore.startPolling(props.contactId)
})

onUnmounted(() => {
  chatStore.stopPolling()
})

watch(() => chatStore.messages.length, () => {
  scrollToBottom()
})

async function handleSend() {
  if (!newMessage.value.trim() || isSending.value) return
  isSending.value = true
  sendError.value = ''
  try {
    await chatStore.sendMessage(props.contactId, newMessage.value, props.dealId)
    newMessage.value = ''
    scrollToBottom()
  } catch (e: any) {
    sendError.value = e.message || 'Ошибка отправки'
  } finally {
    isSending.value = false
  }
}

function openFilePicker() {
  fileInput.value?.click()
}

async function handleFileUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  
  isUploading.value = true
  sendError.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('contactId', props.contactId)
    if (props.dealId) formData.append('dealId', props.dealId)

    const res = await fetch(`${API_URL}/api/chat/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
      body: formData,
    })
    if (res.ok) {
      const saved = await res.json()
      chatStore.messages.push(saved)
      scrollToBottom()
    } else {
      const err = await res.json()
      sendError.value = err.detail || 'Ошибка загрузки'
    }
  } catch (e: any) {
    sendError.value = e.message || 'Ошибка сети'
  } finally {
    isUploading.value = false
    input.value = '' // reset file input
  }
}

function getImageUrl(content: string) {
  if (content.startsWith('http')) return content
  return `${API_URL}${content}`
}

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

function formatDate(ts: string) {
  return new Date(ts).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

function shouldShowDate(idx: number) {
  if (idx === 0) return true
  const prev = new Date(chatStore.messages[idx - 1].timestamp).toDateString()
  const curr = new Date(chatStore.messages[idx].timestamp).toDateString()
  return prev !== curr
}

function openImage(url: string) {
  window.open(url, '_blank')
}
</script>

<template>
  <div class="flex flex-col h-full bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
    <!-- Header -->
    <div class="px-5 py-4 bg-gradient-to-r from-indigo-600 to-violet-600 text-white flex items-center gap-3 shrink-0">
      <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center font-bold text-lg backdrop-blur-sm">
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z"/></svg>
      </div>
      <div class="flex-1 min-w-0">
        <div class="font-bold text-sm truncate">{{ contactName }}</div>
        <div class="text-[11px] text-white/70 flex items-center gap-1">
          <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z"/></svg>
          <span v-if="telegramLinked">Telegram подключён</span>
          <span v-else class="text-yellow-300">Telegram не привязан</span>
        </div>
      </div>
    </div>

    <!-- Messages -->
    <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-1 bg-gray-50/50" style="min-height: 300px; max-height: 500px;">
      <div v-if="chatStore.isLoading" class="flex justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>

      <template v-else-if="chatStore.messages.length > 0">
        <template v-for="(msg, idx) in chatStore.messages" :key="msg.id">
          <!-- Date separator -->
          <div v-if="shouldShowDate(idx)" class="flex justify-center my-3">
            <span class="bg-gray-200 text-gray-500 text-[10px] px-3 py-0.5 rounded-full font-bold uppercase tracking-wider">
              {{ formatDate(msg.timestamp) }}
            </span>
          </div>

          <!-- Message bubble -->
          <div class="flex" :class="msg.senderRole === 'manager' ? 'justify-end' : 'justify-start'">
            <div 
              class="max-w-[75%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm"
              :class="msg.senderRole === 'manager' 
                ? 'bg-indigo-600 text-white rounded-br-md' 
                : 'bg-white text-gray-800 border border-gray-100 rounded-bl-md'"
            >
              <div class="text-[10px] font-bold mb-0.5" :class="msg.senderRole === 'manager' ? 'text-indigo-200' : 'text-indigo-600'">
                {{ msg.senderName }}
              </div>
              
              <!-- Image message -->
              <div v-if="msg.messageType === 'image'" class="my-1">
                <img 
                  :src="getImageUrl(msg.content)" 
                  alt="Photo" 
                  class="rounded-lg max-w-full max-h-60 cursor-pointer hover:opacity-90 transition-opacity"
                  @click="openImage(getImageUrl(msg.content))"
                />
              </div>
              <!-- Text message -->
              <div v-else class="break-words">{{ msg.content }}</div>
              
              <div class="text-[9px] mt-1 text-right" :class="msg.senderRole === 'manager' ? 'text-indigo-300' : 'text-gray-400'">
                {{ formatTime(msg.timestamp) }}
              </div>
            </div>
          </div>
        </template>
      </template>

      <div v-else class="flex flex-col items-center justify-center py-12 text-gray-400">
        <svg class="w-16 h-16 mb-3 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
        </svg>
        <p class="font-bold text-sm">Нет сообщений</p>
        <p class="text-xs">Напишите клиенту первым!</p>
      </div>
    </div>

    <!-- Error banner -->
    <div v-if="sendError" class="px-4 py-2 bg-red-50 border-t border-red-100 text-red-600 text-xs font-bold flex items-center gap-2">
      <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      {{ sendError }}
      <button @click="sendError = ''" class="ml-auto text-red-400 hover:text-red-600">&times;</button>
    </div>

    <!-- Input -->
    <div class="p-3 bg-white border-t border-gray-100 shrink-0">
      <div v-if="!telegramLinked" class="text-center py-3 text-xs text-gray-400 italic">
        Привяжите Telegram ID клиента, чтобы начать переписку.
      </div>
      <div v-else class="flex gap-2">
        <!-- Hidden file input -->
        <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="handleFileUpload" />
        
        <!-- Image upload button -->
        <button
          @click="openFilePicker"
          :disabled="isUploading"
          class="p-2.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-colors disabled:opacity-50 shrink-0"
          title="Отправить фото"
        >
          <svg v-if="!isUploading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <svg v-else class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
        </button>

        <input
          v-model="newMessage"
          @keydown.enter="handleSend"
          :disabled="isSending"
          type="text"
          placeholder="Написать сообщение..."
          class="flex-1 px-4 py-2.5 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all disabled:opacity-50"
        />
        <button
          @click="handleSend"
          :disabled="!newMessage.trim() || isSending"
          class="bg-indigo-600 text-white p-2.5 rounded-xl hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors shadow-lg shadow-indigo-100 shrink-0"
        >
          <svg v-if="!isSending" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
          </svg>
          <svg v-else class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
