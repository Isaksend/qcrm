<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useChatStore } from '../../stores/chat'
import { useDealsStore } from '../../stores/deals'
import { apiUrl, getBackendOrigin } from '../../lib/api'
import type { Deal } from '../../types'

const props = defineProps<{
  contactId: string
  contactName: string
  telegramLinked: boolean
  dealId?: string
}>()

const chatStore = useChatStore()
const dealsStore = useDealsStore()

const newMessage = ref('')
const isSending = ref(false)
const sendError = ref('')
const chatContainer = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)

// New Deal Modal State
const showNewDealModal = ref(false)
const isCreatingDeal = ref(false)
const newDeal = ref<Deal>({
  title: '',
  value: 0,
  stage: 'New Request' as Deal['stage'],
  notes: ''
})

// AI Analysis State
const showAIModal = ref(false)
const isAnalyzing = ref(false)
const aiResult = ref<any>(null)

const origin = getBackendOrigin()

function mediaUrl(path: string) {
  if (path.startsWith('http')) return path
  return origin ? `${origin}${path}` : path
}

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

    const res = await fetch(apiUrl('/api/chat/upload'), {
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

async function handleCreateDeal() {
  if (!newDeal.value.title || isCreatingDeal.value) return
  isCreatingDeal.value = true
  try {
    await dealsStore.addDeal({
      leadId: '',
      closedAt: null,
      ...newDeal.value,
      contactId: props.contactId,
      userId: '', // handled by store/backend
      companyId: null as string | null, // handled by store/backend
    })
    showNewDealModal.value = false
    newDeal.value = {
      title: '',
      value: 0,
      stage: 'New Request',
      notes: '',
      id: '',
      leadId: '',
      contactId: '',
      closedAt: null,
      userId: '',
      companyId: null
    }
  } catch (e) {
    console.error(e)
  } finally {
    isCreatingDeal.value = false
  }
}

async function runAIAnalysis() {
  if (isAnalyzing.value) return
  isAnalyzing.value = true
  aiResult.value = null
  showAIModal.value = true
  try {
    const res = await fetch(apiUrl(`/api/chat/${props.contactId}/analyze`), {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
    })
    if (res.ok) {
      aiResult.value = await res.json()
    } else {
      const err = await res.json()
      alert(err.detail || 'AI Analysis failed')
    }
  } catch (e) {
    alert('Network error during AI analysis')
  } finally {
    isAnalyzing.value = false
  }
}

function getImageUrl(content: string) {
  if (content.startsWith('http')) return content
  return mediaUrl(content)
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
  <div class="flex flex-col h-full bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden relative">
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
      <!-- Actions -->
      <div class="flex items-center gap-2">
        <button 
          @click="runAIAnalysis"
          class="bg-indigo-500/30 hover:bg-indigo-500/50 p-1.5 rounded-lg transition-colors group flex items-center gap-1.5"
          title="AI Анализ вероятности"
        >
          <svg class="w-4 h-4 text-indigo-100 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71z"/>
          </svg>
          <span class="text-[9px] font-black uppercase tracking-tighter hidden sm:inline">AI Анализ</span>
        </button>
        <button 
          @click="showNewDealModal = true"
          class="bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-colors flex items-center gap-2"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 4v16m8-8H4"/></svg>
          Сделка
        </button>
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

    <!-- Input -->
    <div class="p-3 bg-white border-t border-gray-100 shrink-0">
      <div v-if="!telegramLinked" class="text-center py-3 text-xs text-gray-400 italic">
        Привяжите Telegram ID клиента, чтобы начать переписку.
      </div>
      <div v-else class="flex gap-2">
        <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="handleFileUpload" />
        <button
          @click="openFilePicker"
          :disabled="isUploading"
          class="p-2.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-colors disabled:opacity-50 shrink-0"
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
          class="bg-indigo-600 text-white p-2.5 rounded-xl hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-100 shrink-0"
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

    <!-- AI Analysis Modal -->
    <div v-if="showAIModal" class="absolute inset-0 bg-indigo-950/95 backdrop-blur-md z-[60] flex flex-col p-6 text-white animate-fade-in">
      <div class="flex items-center justify-between mb-8">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-indigo-500/30 flex items-center justify-center animate-pulse">
            <svg class="w-6 h-6 text-indigo-300" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71z"/></svg>
          </div>
          <div>
             <h3 class="text-lg font-black uppercase tracking-tighter">AI Анализ сделки</h3>
             <p class="text-[10px] text-indigo-300 uppercase font-bold">на базе Gemini 1.5 Flash</p>
          </div>
        </div>
        <button @click="showAIModal = false" class="text-indigo-300 hover:text-white transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>

      <div v-if="isAnalyzing" class="flex-1 flex flex-col items-center justify-center space-y-4">
        <div class="w-24 h-1 bg-white/10 rounded-full overflow-hidden">
          <div class="h-full bg-indigo-400 animate-loading-bar"></div>
        </div>
        <p class="text-sm font-bold text-indigo-200 animate-pulse">Анализируем историю переписки...</p>
      </div>

      <div v-else-if="aiResult" class="flex-1 overflow-y-auto space-y-6">
        <!-- Score -->
        <div class="flex flex-col items-center py-4">
          <div class="relative w-32 h-32 flex items-center justify-center">
            <svg class="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="8" class="text-white/5"/>
              <circle 
                cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="8" 
                class="text-indigo-400 transition-all duration-1000"
                :stroke-dasharray="283"
                :stroke-dashoffset="283 - (283 * aiResult.confidence) / 100"
              />
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <span class="text-3xl font-black">{{ aiResult.confidence }}%</span>
              <span class="text-[8px] uppercase font-black text-indigo-300">Вероятность</span>
            </div>
          </div>
        </div>

        <!-- Content -->
        <div class="bg-white/5 rounded-2xl p-5 border border-white/10">
          <h4 class="text-sm font-black uppercase text-indigo-200 mb-3">{{ aiResult.title }}</h4>
          <p class="text-sm text-indigo-100 leading-relaxed font-medium">{{ aiResult.content }}</p>
        </div>

        <!-- Suggestions -->
        <div class="space-y-3">
          <h4 class="text-[10px] font-black uppercase text-indigo-400 tracking-widest px-1">Рекомендованные шаги</h4>
          <div v-for="(step, i) in aiResult.suggestions" :key="i" class="flex gap-3 bg-white/5 p-3 rounded-xl border border-white/5 hover:border-white/20 transition-all">
            <span class="text-xs font-black text-indigo-400">{{ i + 1 }}.</span>
            <p class="text-sm font-medium text-white/90">{{ step }}</p>
          </div>
        </div>

        <button @click="showAIModal = false" class="w-full py-4 bg-indigo-600 hover:bg-indigo-500 rounded-xl font-black uppercase tracking-widest text-xs transition-all shadow-xl shadow-indigo-900/40">
          Понятно
        </button>
      </div>
    </div>

    <!-- Create Deal Modal -->
    <div v-if="showNewDealModal" class="absolute inset-0 bg-white/95 backdrop-blur-sm z-50 flex flex-col p-6 overflow-y-auto">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-black text-gray-900 uppercase tracking-tight">Новая сделка</h3>
        <button @click="showNewDealModal = false" class="text-gray-400 hover:text-gray-600">
           <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="space-y-4">
        <div>
          <label class="block text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1.5">Название сделки</label>
          <input v-model="newDeal.title" type="text" class="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-xl outline-none transition-all text-sm"/>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1.5">Сумма ($)</label>
            <input v-model="newDeal.value" type="number" class="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-xl outline-none transition-all text-sm"/>
          </div>
          <div>
            <label class="block text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1.5">Этап</label>
            <select v-model="newDeal.stage" class="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-xl outline-none transition-all text-sm">
              <option>New Request</option><option>Discovery</option><option>Proposal</option><option>Negotiation</option>
            </select>
          </div>
        </div>
        <button @click="handleCreateDeal" :disabled="!newDeal.title || isCreatingDeal" class="w-full py-4 bg-indigo-600 text-white rounded-xl font-black uppercase tracking-widest text-xs hover:bg-indigo-700 disabled:bg-gray-200 transition-all shadow-lg shadow-indigo-100">
          {{ isCreatingDeal ? 'Создание...' : 'Создать сделку' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes fade-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
.animate-fade-in { animation: fade-in 0.3s ease-out; }

@keyframes loading-bar {
  0% { transform: translateX(-100%); }
  50% { transform: translateX(0); }
  100% { transform: translateX(100%); }
}
.animate-loading-bar { animation: loading-bar 1.5s infinite linear; }
</style>
