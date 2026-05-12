<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useContactsStore } from '../stores/contacts'
import ChatWindow from '../components/chat/ChatWindow.vue'

const API_URL = '/api'
const contactsStore = useContactsStore()
const selectedContactId = ref<string | null>(null)
const showNewChatModal = ref(false)
const newTelegramId = ref('')
const newChatMessage = ref('')
const isStartingChat = ref(false)
const startChatError = ref('')
let contactsPollInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  contactsStore.fetchContacts()
  // Auto-refresh contacts every 5s to pick up bot-registered clients
  contactsPollInterval = setInterval(() => {
    contactsStore.fetchContacts()
  }, 5000)
})

onUnmounted(() => {
  if (contactsPollInterval) clearInterval(contactsPollInterval)
})

const selectedContact = computed(() => {
  if (!selectedContactId.value) return null
  return contactsStore.contacts.find(c => c.id === selectedContactId.value)
})

const linkedContacts = computed(() => {
  return contactsStore.contacts.filter(c => c.telegram_id)
})

const unlinkedContacts = computed(() => {
  return contactsStore.contacts.filter(c => !c.telegram_id)
})

async function startNewChat() {
  if (!newTelegramId.value.trim()) return
  isStartingChat.value = true
  startChatError.value = ''
  try {
    const res = await fetch(`${API_URL}/chat/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        telegram_id: newTelegramId.value.trim(),
        message: newChatMessage.value.trim() || null,
      })
    })
    if (res.ok) {
      const data = await res.json()
      // Close modal first
      showNewChatModal.value = false
      newTelegramId.value = ''
      newChatMessage.value = ''
      // Refresh contacts to pick up the new one
      await contactsStore.fetchContacts()
      // Auto-select the new contact after contacts are loaded
      selectedContactId.value = data.contactId
      
      if (data.delivered === false && data.contactName) {
        alert(`Контакт "${data.contactName}" создан, но клиент ещё не запустил бота (/start). Сообщение сохранено в CRM.`)
      }
    } else {
      const err = await res.json()
      startChatError.value = err.detail || 'Ошибка'
    }
  } catch (e: any) {
    startChatError.value = e.message || 'Ошибка сети'
  } finally {
    isStartingChat.value = false
  }
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Messages</h1>
        <p class="text-sm text-gray-500 mt-1">Telegram-интеграция: Переписка с клиентами прямо из CRM.</p>
      </div>
      <button @click="showNewChatModal = true" class="btn-primary">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>
        Начать чат
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6" style="height: 650px;">
      <!-- Contact List (Left Panel) -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
        <div class="p-4 border-b border-gray-100 bg-gray-50/50 shrink-0">
          <h3 class="text-xs font-black text-gray-900 uppercase tracking-widest">Контакты</h3>
        </div>
        <div class="flex-1 overflow-y-auto">
          <!-- Telegram-linked contacts -->
          <div v-if="linkedContacts.length > 0" class="p-2">
            <div class="text-[9px] text-green-600 font-black uppercase tracking-widest px-3 py-2 flex items-center gap-1">
              <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z"/></svg>
              Telegram подключён ({{ linkedContacts.length }})
            </div>
            <button
              v-for="contact in linkedContacts"
              :key="contact.id"
              @click="selectedContactId = contact.id"
              class="w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all text-left"
              :class="selectedContactId === contact.id ? 'bg-indigo-50 border border-indigo-200' : 'hover:bg-gray-50'"
            >
              <div class="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-sm shrink-0">
                {{ contact.avatar || contact.name.charAt(0) }}
              </div>
              <div class="min-w-0 flex-1">
                <div class="font-bold text-sm text-gray-900 truncate">{{ contact.name }}</div>
                <div class="text-[10px] text-gray-400 truncate">{{ contact.company || contact.email }}</div>
              </div>
              <div class="w-2 h-2 rounded-full bg-green-500 shrink-0"></div>
            </button>
          </div>
          
          <!-- Unlinked contacts -->
          <div v-if="unlinkedContacts.length > 0" class="p-2 border-t border-gray-50">
            <div class="text-[9px] text-gray-400 font-black uppercase tracking-widest px-3 py-2">
              Без Telegram ({{ unlinkedContacts.length }})
            </div>
            <div
              v-for="contact in unlinkedContacts"
              :key="contact.id"
              class="flex items-center gap-3 px-3 py-2.5 rounded-xl opacity-50"
            >
              <div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 font-bold text-xs shrink-0">
                {{ contact.avatar || contact.name.charAt(0) }}
              </div>
              <div class="min-w-0 flex-1">
                <div class="text-xs text-gray-600 truncate">{{ contact.name }}</div>
              </div>
            </div>
          </div>

          <div v-if="contactsStore.contacts.length === 0" class="flex flex-col items-center justify-center py-12 text-gray-400">
            <p class="text-sm">Нет контактов</p>
          </div>
        </div>
      </div>

      <!-- Chat Window (Right Panel) -->
      <div class="lg:col-span-2">
        <ChatWindow
          v-if="selectedContact"
          :key="selectedContact.id"
          :contact-id="selectedContact.id"
          :contact-name="selectedContact.name"
          :telegram-linked="!!selectedContact.telegram_id"
        />
        <div v-else class="h-full bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center justify-center text-gray-400">
          <svg class="w-20 h-20 mb-4 text-gray-200" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z"/>
          </svg>
          <p class="font-bold text-lg text-gray-500">Telegram Messenger</p>
          <p class="text-sm mt-1">Выберите контакт или нажмите «Начать чат»</p>
          <button @click="showNewChatModal = true" class="mt-4 px-4 py-2 bg-indigo-600 text-white text-sm font-bold rounded-xl hover:bg-indigo-700 transition-colors">
            + Начать новый чат
          </button>
        </div>
      </div>
    </div>

    <!-- New Chat Modal -->
    <div v-if="showNewChatModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showNewChatModal = false">
      <div class="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <h3 class="text-lg font-black text-gray-900 mb-1">Начать чат</h3>
        <p class="text-sm text-gray-500 mb-6">Введите Telegram ID клиента. Если контакт не существует — он будет создан автоматически.</p>
        
        <div class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-gray-600 mb-1">Telegram ID *</label>
            <input
              v-model="newTelegramId"
              type="text"
              placeholder="Например: 123456789"
              class="w-full px-4 py-2.5 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            />
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-600 mb-1">Первое сообщение (необязательно)</label>
            <input
              v-model="newChatMessage"
              type="text"
              placeholder="Здравствуйте! Чем могу помочь?"
              class="w-full px-4 py-2.5 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            />
          </div>

          <div v-if="startChatError" class="bg-red-50 text-red-600 text-xs p-3 rounded-lg font-bold">
            {{ startChatError }}
          </div>

          <div class="flex gap-3 pt-2">
            <button @click="showNewChatModal = false" class="flex-1 py-2.5 text-sm font-bold text-gray-600 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors">
              Отмена
            </button>
            <button
              @click="startNewChat"
              :disabled="!newTelegramId.trim() || isStartingChat"
              class="flex-1 py-2.5 text-sm font-bold text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {{ isStartingChat ? 'Подключение...' : 'Начать чат' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
