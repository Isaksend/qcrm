<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDealsStore } from '../stores/deals'
import { useContactsStore } from '../stores/contacts'
import ChatWindow from '../components/chat/ChatWindow.vue'
import type { Deal, Note } from '../types'

const route = useRoute()
const router = useRouter()
const dealsStore = useDealsStore()
const contactsStore = useContactsStore()

const dealId = route.params.id as string
const deal = ref<Deal | null>(null)
const manager = ref<any>(null)
const notes = ref<Note[]>([])
const newNoteContent = ref('')
const isLoading = ref(true)
const isSavingNote = ref(false)

const contact = computed(() => {
  if (!deal.value) return null
  return contactsStore.getContact(deal.value.contactId)
})

const users = ref<any[]>([])
const userMap = computed(() => {
  const map: Record<string, any> = {}
  users.value.forEach(u => map[u.id] = u)
  return map
})

async function fetchData() {
  isLoading.value = true
  try {
    // 1. Fetch Users (for manager and note authors)
    const userRes = await fetch(`/api/users`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    if (userRes.ok) users.value = await userRes.json()

    // 2. Fetch Deal
    const res = await fetch(`/api/deals/${dealId}`, {
       headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    if (res.ok) {
      deal.value = await res.json()
      if (deal.value?.userId) {
        manager.value = userMap.value[deal.value.userId]
      }
    }

    // 3. Fetch Notes
    const notesRes = await fetch(`/api/deals/${dealId}/notes`, {
       headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    if (notesRes.ok) notes.value = await notesRes.json()

    // 4. Ensure contacts pre-loaded
    if (contactsStore.contacts.length === 0) await contactsStore.fetchContacts()
    
  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

async function addNote() {
  if (!newNoteContent.value.trim()) return
  isSavingNote.value = true
  try {
    const res = await fetch(`/api/deals/${dealId}/notes`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        dealId: dealId,
        content: newNoteContent.value
      })
    })
    if (res.ok) {
      const savedNote = await res.json()
      notes.value.unshift(savedNote)
      newNoteContent.value = ''
    }
  } catch (e) {
    console.error(e)
  } finally {
    isSavingNote.value = false
  }
}

onMounted(() => {
  fetchData()
})

const stageClass: Record<string, string> = {
  'New Request': 'bg-cyan-100 text-cyan-700',
  'Qualified': 'bg-teal-100 text-teal-700',
  'Discovery': 'bg-blue-100 text-blue-700',
  'Proposal': 'bg-purple-100 text-purple-700',
  'Negotiation': 'bg-orange-100 text-orange-700',
  'Closed Won': 'bg-green-100 text-green-700',
  'Closed Lost': 'bg-red-100 text-red-700',
}

function formatCurrency(val: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val)
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 pb-12">
    <div v-if="isLoading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
    </div>

    <div v-else-if="deal" class="space-y-6">
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <button @click="router.back()" class="p-2 hover:bg-gray-100 rounded-full text-gray-400 transition-colors">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
          </button>
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ deal.title }}</h1>
            <div class="flex items-center gap-2 mt-1">
              <span class="px-2.5 py-0.5 rounded-full text-xs font-bold" :class="stageClass[deal.stage]">
                {{ deal.stage }}
              </span>
              <span class="text-xs text-gray-400 font-mono">ID: {{ deal.id.slice(0, 8) }}</span>
            </div>
          </div>
        </div>
        <div class="bg-emerald-50 px-6 py-3 rounded-2xl border border-emerald-100 text-right">
          <div class="text-2xl font-black text-emerald-600">{{ formatCurrency(deal.value) }}</div>
          <div class="text-[10px] text-emerald-600/70 font-bold uppercase tracking-widest">Deal Value</div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main Info -->
        <div class="lg:col-span-2 space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h3 class="text-sm font-black text-gray-900 uppercase tracking-widest mb-6 border-b border-gray-50 pb-2">Deal Context</h3>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-6">
              <div>
                <label class="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-1">Status</label>
                <p class="font-bold text-gray-900 flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full" :class="deal.closedAt ? 'bg-gray-400' : 'bg-green-500 animate-pulse'"></span>
                  {{ deal.closedAt ? 'Archive' : 'In Pipeline' }}
                </p>
              </div>
              <div>
                <label class="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-1">Assigned Manager</label>
                <div v-if="manager" class="flex flex-col">
                  <span class="font-bold text-gray-900">{{ manager.name }}</span>
                  <span class="text-[10px] text-indigo-600 font-bold uppercase">{{ manager.role }}</span>
                </div>
                <p v-else class="text-gray-400 italic">Unassigned</p>
              </div>
              <div>
                <label class="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-1">Closed Date</label>
                <p class="font-bold text-gray-900">{{ deal.closedAt ? formatDate(deal.closedAt) : 'Pending' }}</p>
              </div>
            </div>
            
            <div v-if="deal.notes" class="mt-8 pt-6 border-t border-gray-50">
               <label class="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-2">Original Description</label>
               <p class="text-sm text-gray-600 bg-gray-50 p-4 rounded-xl italic">{{ deal.notes }}</p>
            </div>
          </div>

          <!-- Notes / Timeline -->
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div class="p-6 border-b border-gray-50 flex items-center justify-between">
              <h3 class="text-sm font-black text-gray-900 uppercase tracking-widest">Collaborative Timeline</h3>
              <span class="bg-gray-100 text-gray-600 text-[10px] px-2 py-0.5 rounded-full font-bold">{{ notes.length }} NOTES</span>
            </div>
            
            <!-- Add Note Input -->
            <div class="p-4 bg-gray-50/50">
              <div class="relative">
                <textarea 
                  v-model="newNoteContent"
                  rows="2" 
                  class="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none transition-all shadow-inner" 
                  placeholder="Shared a note with the team..."
                ></textarea>
                <button 
                  @click="addNote" 
                  :disabled="!newNoteContent.trim() || isSavingNote"
                  class="absolute bottom-3 right-3 bg-indigo-600 text-white p-2 rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors shadow-lg shadow-indigo-200"
                >
                  <svg v-if="!isSavingNote" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>
                  <svg v-else class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                </button>
              </div>
            </div>

            <div class="p-6 space-y-8 max-h-[500px] overflow-y-auto">
              <div v-for="note in notes" :key="note.id" class="relative pl-8 border-l-2 border-gray-100">
                <div class="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-white border-2 border-indigo-400"></div>
                
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-xs font-black text-gray-900">{{ userMap[note.userId]?.name || 'Unknown User' }}</span>
                  <span class="text-[9px] text-gray-400 font-bold uppercase tracking-tighter">{{ formatDate(note.createdAt) }}</span>
                </div>
                <div class="text-sm text-gray-600 bg-white p-3 rounded-lg border border-gray-100 shadow-sm inline-block max-w-full break-words">
                  {{ note.content }}
                </div>
              </div>
              
              <div v-if="notes.length === 0" class="text-center py-10">
                <div class="text-gray-300 mb-2">
                   <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                </div>
                <p class="text-gray-400 text-sm italic">No discussion yet. Every note helps the team win!</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Sidebar Info -->
        <div class="space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6" v-if="contact">
            <h3 class="text-sm font-black text-gray-900 uppercase tracking-widest mb-6">Linked Contact</h3>
            <div class="flex items-center gap-4 mb-6 pb-6 border-b border-gray-50">
              <div class="w-14 h-14 rounded-2xl bg-indigo-600 flex items-center justify-center font-black text-white text-xl shadow-lg shadow-indigo-100">
                {{ contact.avatar }}
              </div>
              <div>
                <p class="font-black text-gray-900 text-lg leading-tight">{{ contact.name }}</p>
                <p class="text-xs text-indigo-600 font-bold mt-1">{{ contact.company }}</p>
              </div>
            </div>
            <div class="space-y-4">
              <div class="flex flex-col">
                <label class="text-[9px] text-gray-400 font-black uppercase tracking-widest mb-1">Email</label>
                <div class="flex items-center gap-2">
                   <svg class="w-3 h-3 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                   <span class="text-sm text-gray-600 truncate font-medium">{{ contact.email }}</span>
                </div>
              </div>
              <div class="flex flex-col">
                <label class="text-[9px] text-gray-400 font-black uppercase tracking-widest mb-1">Phone</label>
                <div class="flex items-center gap-2">
                   <svg class="w-3 h-3 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
                   <span class="text-sm text-gray-600 font-medium">{{ contact.phone }}</span>
                </div>
              </div>
            </div>
            <button @click="router.push('/contacts')" class="w-full mt-8 py-3 text-xs font-black text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 uppercase tracking-widest">
              CONTACT DOSSIER
            </button>
          </div>

          <!-- Telegram Chat Widget -->
          <div v-if="contact" class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <ChatWindow
              :contact-id="contact.id"
              :contact-name="contact.name"
              :telegram-linked="!!contact.telegram_id"
              :deal-id="dealId"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
