<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useDealsStore } from '../stores/deals'
import { useContactsStore } from '../stores/contacts'
import { useAuthStore } from '../stores/auth'
import { useMyDealTasksStore } from '../stores/myDealTasks'
import ChatWindow from '../components/chat/ChatWindow.vue'
import AIPredictionCard from '../components/ai/AIPredictionCard.vue'
import type { Deal, Note, DealTask } from '../types'
import type { AIPredictionResponse } from '../types/ai'
import { apiUrl } from '../lib/api'

const route = useRoute()
const router = useRouter()
const { t, locale, te } = useI18n()

const STAGE_I18N: Record<string, string> = {
  'New Request': 'dealStages.newRequest',
  Qualified: 'dealStages.qualified',
  Discovery: 'dealStages.discovery',
  Proposal: 'dealStages.proposal',
  Negotiation: 'dealStages.negotiation',
  'Closed Won': 'dealStages.closedWon',
  'Closed Lost': 'dealStages.closedLost',
}

function dealStageLabel(stage: string): string {
  const path = STAGE_I18N[stage]
  return path ? t(path) : stage
}

const USER_ROLE_I18N: Record<string, string> = {
  sales_representative: 'users.roleUser',
  manager: 'users.roleManager',
  admin: 'users.roleAdmin',
  super_admin: 'users.roleSuper',
}

function userRoleLabel(role: string | null | undefined): string {
  if (!role || !String(role).trim()) return ''
  const path = USER_ROLE_I18N[String(role).trim()]
  return path ? t(path) : role
}
const dealsStore = useDealsStore()
const contactsStore = useContactsStore()
const authStore = useAuthStore()
const myDealTasksStore = useMyDealTasksStore()

const dealId = route.params.id as string
const deal = ref<Deal | null>(null)
const notes = ref<Note[]>([])
const newNoteContent = ref('')
const isLoading = ref(true)
const isSavingNote = ref(false)
const titleEdit = ref('')

const dealAiLoading = ref(false)
const dealAiError = ref('')
const dealAiLead = ref<AIPredictionResponse | null>(null)
const dealAiChurn = ref<AIPredictionResponse | null>(null)

type DealHistoryRow = {
  id: string
  deal_id: string
  field: string
  old_value: string | null
  new_value: string | null
  changed_at: string
  changed_by_id: string | null
  changed_by_name: string | null
}

const dealHistory = ref<DealHistoryRow[]>([])
const reassignUserId = ref('')
const isSavingReassign = ref(false)

const tasks = ref<DealTask[]>([])
const newTaskTitle = ref('')
const newTaskDue = ref('')
const newTaskAssigneeId = ref('')
const isSavingTask = ref(false)
const togglingTaskId = ref<string | null>(null)

const users = ref<any[]>([])

const canReassignDeal = computed(() => {
  const r = authStore.userRole
  if (r !== 'admin' && r !== 'super_admin') return false
  const cid = deal.value?.companyId
  return typeof cid === 'string' && cid.trim() !== ''
})

const assignableColleagues = computed(() => {
  const cid = deal.value?.companyId
  if (!cid || typeof cid !== 'string') return []
  return users.value.filter(
    (u) =>
      u.company_id === cid &&
      u.role !== 'super_admin' &&
      u.is_active !== 0,
  )
})

/** Исполнители для новой задачи (та же компания, что и сделка). */
const taskAssignOptions = computed(() => {
  const opts = assignableColleagues.value
  if (opts.length) return opts
  const u = authStore.user
  return u?.id ? [{ id: u.id, name: u.name || u.email, email: u.email }] : []
})

/** Список для селекта исполнителя: коллеги + уже назначенные на задачах (если их не было в списке). */
const taskAssignForSelect = computed(() => {
  const base = [...taskAssignOptions.value]
  const ids = new Set(base.map((u) => u.id))
  for (const t of tasks.value) {
    const aid = t.assignedUserId && String(t.assignedUserId).trim()
    if (!aid || ids.has(aid)) continue
    const u = userMap.value[aid]
    if (u) {
      base.push(u)
      ids.add(aid)
    }
  }
  return base.sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''), undefined, { sensitivity: 'base' }))
})

/** Админ / менеджер / super_admin могут ставить исполнителем другого пользователя компании. */
const canDelegateTasks = computed(() => {
  const r = authStore.userRole
  return r === 'admin' || r === 'super_admin' || r === 'manager'
})

watch(
  deal,
  (d) => {
    if (d) titleEdit.value = d.title
  },
  { immediate: true },
)

watch(
  () => deal.value?.userId,
  (uid) => {
    const s = typeof uid === 'string' ? uid.trim() : ''
    reassignUserId.value = s
  },
  { immediate: true },
)

watch(
  () => [deal.value?.id, deal.value?.userId, taskAssignOptions.value.map((u) => u.id).join(',')],
  () => {
    const uid = deal.value?.userId && String(deal.value.userId).trim()
    if (uid && taskAssignOptions.value.some((o) => o.id === uid)) {
      newTaskAssigneeId.value = uid
    } else if (authStore.user?.id) {
      newTaskAssigneeId.value = authStore.user.id
    } else {
      newTaskAssigneeId.value = ''
    }
  },
  { immediate: true },
)

const contact = computed(() => {
  if (!deal.value) return null
  return contactsStore.getContact(deal.value.contactId)
})

function openLinkedContact() {
  const id = contact.value?.id
  if (!id) return
  contactsStore.selectedContactId = id
  contactsStore.statusFilter = 'All'
  contactsStore.searchQuery = ''
  router.push({ path: '/contacts', query: { contactId: id } })
}

const userMap = computed(() => {
  const map: Record<string, any> = {}
  users.value.forEach((u) => (map[u.id] = u))
  return map
})

const manager = computed(() => {
  const id = typeof deal.value?.userId === 'string' ? deal.value.userId.trim() : ''
  if (!id) return null
  return userMap.value[id] ?? null
})

const creator = computed(() => {
  if (!deal.value) return null
  const raw = deal.value.createdById || deal.value.userId
  const id = typeof raw === 'string' ? raw.trim() : ''
  if (!id) return null
  return userMap.value[id] ?? null
})

function noteUserId(note: Note): string {
  const n = note as Note & { user_id?: string }
  const raw = n.userId ?? n.user_id
  return raw != null && String(raw).trim() !== '' ? String(raw).trim() : ''
}

function userDisplayName(userId: string | null | undefined): string {
  const id = typeof userId === 'string' ? userId.trim() : ''
  if (!id) return ''
  const u = userMap.value[id]
  if (u?.name) return u.name as string
  return t('dealDetail.userFallback', { id: id.slice(0, 8) })
}

function mergeAuthUserIntoList() {
  const u = authStore.user
  if (!u?.id) return
  if (users.value.some((x) => x.id === u.id)) return
  users.value = [...users.value, { ...u }]
}

async function hydrateMissingUsers(authHeaders: Record<string, string>) {
  mergeAuthUserIntoList()
  const ids = new Set<string>()
  const add = (raw: string | null | undefined) => {
    const s = typeof raw === 'string' ? raw.trim() : ''
    if (s) ids.add(s)
  }
  if (deal.value) {
    add(deal.value.userId ?? undefined)
    add(deal.value.createdById ?? undefined)
  }
  for (const n of notes.value) {
    add(noteUserId(n))
  }
  for (const t of tasks.value) {
    add(t.createdBy ?? undefined)
    add(t.assignedUserId ?? undefined)
  }
  add(newTaskAssigneeId.value || undefined)
  for (const id of ids) {
    if (users.value.some((u) => u.id === id)) continue
    try {
      const r = await fetch(apiUrl(`/api/users/${encodeURIComponent(id)}`), { headers: authHeaders })
      if (r.ok) users.value.push(await r.json())
    } catch {
      /* ignore */
    }
  }
}

async function loadDealContactAi(contactId: string, forDealId: string) {
  dealAiLoading.value = true
  dealAiError.value = ''
  dealAiLead.value = null
  dealAiChurn.value = null
  const token = authStore.token || localStorage.getItem('token')
  const authHeaders: Record<string, string> = {}
  if (token) authHeaders.Authorization = `Bearer ${token}`
  try {
    const qs = new URLSearchParams({ deal_id: forDealId })
    const r = await fetch(
      apiUrl(`/api/ai/analyze-contact/${encodeURIComponent(contactId)}?${qs.toString()}`),
      { headers: authHeaders },
    )
    if (!r.ok) {
      let msg = `HTTP ${r.status}`
      try {
        const err = await r.json()
        if (err.detail) msg = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail)
      } catch {
        /* ignore */
      }
      dealAiError.value = msg
      return
    }
    const data = await r.json()
    dealAiLead.value = data.analysis?.lead_conversion ?? null
    dealAiChurn.value = data.analysis?.churn_risk ?? null
  } catch {
    dealAiError.value = t('dealDetail.networkError')
  } finally {
    dealAiLoading.value = false
  }
}

async function loadDealTasks(authHeaders: Record<string, string>) {
  const tasksRes = await fetch(apiUrl(`/api/deals/${encodeURIComponent(dealId)}/tasks`), { headers: authHeaders })
  if (tasksRes.ok) {
    tasks.value = await tasksRes.json()
  } else {
    tasks.value = []
  }
}

async function fetchData() {
  isLoading.value = true
  const token = authStore.token || localStorage.getItem('token')
  const authHeaders: Record<string, string> = {}
  if (token) authHeaders.Authorization = `Bearer ${token}`
  try {
    if (token && !authStore.user) {
      await authStore.fetchCurrentUser()
    }

    // 1. Список коллег компании
    const userRes = await fetch(apiUrl('/api/users'), {
      headers: authHeaders,
    })
    if (userRes.ok) users.value = await userRes.json()
    mergeAuthUserIntoList()

    // 2. Сделка
    const res = await fetch(apiUrl(`/api/deals/${dealId}`), {
      headers: authHeaders,
    })
    if (res.ok) {
      deal.value = await res.json()
    }

    // 3. Заметки
    const notesRes = await fetch(apiUrl(`/api/deals/${dealId}/notes`), {
      headers: authHeaders,
    })
    if (notesRes.ok) notes.value = await notesRes.json()

    const histRes = await fetch(apiUrl(`/api/deals/${encodeURIComponent(dealId)}/history`), { headers: authHeaders })
    if (histRes.ok) {
      dealHistory.value = await histRes.json()
    } else {
      dealHistory.value = []
    }

    await loadDealTasks(authHeaders)

    await hydrateMissingUsers(authHeaders)

    // 4. Контакты для сайдбара
    if (contactsStore.contacts.length === 0) await contactsStore.fetchContacts()

    const cid = deal.value?.contactId
    if (cid && String(cid).trim()) {
      await loadDealContactAi(String(cid).trim(), dealId)
    } else {
      dealAiLoading.value = false
      dealAiLead.value = null
      dealAiChurn.value = null
      dealAiError.value = ''
    }
  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

async function addNote() {
  if (!newNoteContent.value.trim()) return
  isSavingNote.value = true
  const token = authStore.token || localStorage.getItem('token')
  const authHeaders: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) authHeaders.Authorization = `Bearer ${token}`
  try {
    const res = await fetch(apiUrl(`/api/deals/${dealId}/notes`), {
      method: 'POST',
      headers: authHeaders,
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

async function addTask() {
  if (!newTaskTitle.value.trim()) return
  isSavingTask.value = true
  const token = authStore.token || localStorage.getItem('token')
  const authHeaders: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) authHeaders.Authorization = `Bearer ${token}`
  try {
    const body: Record<string, unknown> = { title: newTaskTitle.value.trim() }
    if (canDelegateTasks.value && newTaskAssigneeId.value.trim()) {
      body.assignedUserId = newTaskAssigneeId.value.trim()
    }
    if (newTaskDue.value.trim()) {
      body.dueAt = new Date(newTaskDue.value).toISOString()
    }
    const res = await fetch(apiUrl(`/api/deals/${encodeURIComponent(dealId)}/tasks`), {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify(body),
    })
    if (res.ok) {
      newTaskTitle.value = ''
      newTaskDue.value = ''
      await loadDealTasks(authHeaders)
      await hydrateMissingUsers(authHeaders)
      void myDealTasksStore.refresh(80)
    }
  } catch (e) {
    console.error(e)
  } finally {
    isSavingTask.value = false
  }
}

async function updateTaskAssignee(task: DealTask, ev: Event) {
  const el = ev.target as HTMLSelectElement
  const newId = el?.value?.trim() || ''
  if (!newId || newId === (task.assignedUserId && String(task.assignedUserId).trim())) return
  const token = authStore.token || localStorage.getItem('token')
  const authHeaders: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) authHeaders.Authorization = `Bearer ${token}`
  try {
    const res = await fetch(
      apiUrl(`/api/deals/${encodeURIComponent(dealId)}/tasks/${encodeURIComponent(task.id)}`),
      {
        method: 'PATCH',
        headers: authHeaders,
        body: JSON.stringify({ assignedUserId: newId }),
      },
    )
    if (res.ok) {
      await loadDealTasks(authHeaders)
      await hydrateMissingUsers(authHeaders)
      void myDealTasksStore.refresh(80)
    } else {
      el.value = (task.assignedUserId && String(task.assignedUserId).trim()) || ''
    }
  } catch (e) {
    console.error(e)
    el.value = (task.assignedUserId && String(task.assignedUserId).trim()) || ''
  }
}

async function toggleTaskDone(task: DealTask) {
  togglingTaskId.value = task.id
  const token = authStore.token || localStorage.getItem('token')
  const authHeaders: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) authHeaders.Authorization = `Bearer ${token}`
  const next = task.isDone ? 0 : 1
  try {
    const res = await fetch(
      apiUrl(`/api/deals/${encodeURIComponent(dealId)}/tasks/${encodeURIComponent(task.id)}`),
      {
        method: 'PATCH',
        headers: authHeaders,
        body: JSON.stringify({ isDone: next }),
      },
    )
    if (res.ok) {
      await loadDealTasks(authHeaders)
      void myDealTasksStore.refresh(80)
    }
  } catch (e) {
    console.error(e)
  } finally {
    togglingTaskId.value = null
  }
}

async function deleteTask(task: DealTask) {
  if (!confirm(t('dealDetail.tasksConfirmDelete'))) return
  const token = authStore.token || localStorage.getItem('token')
  const authHeaders: Record<string, string> = {}
  if (token) authHeaders.Authorization = `Bearer ${token}`
  try {
    const res = await fetch(
      apiUrl(`/api/deals/${encodeURIComponent(dealId)}/tasks/${encodeURIComponent(task.id)}`),
      { method: 'DELETE', headers: authHeaders },
    )
    if (res.ok) {
      await loadDealTasks(authHeaders)
      void myDealTasksStore.refresh(80)
    }
  } catch (e) {
    console.error(e)
  }
}

function isTaskOverdue(task: DealTask): boolean {
  if (task.isDone) return false
  const raw = task.dueAt
  if (raw == null || String(raw).trim() === '') return false
  const t = new Date(raw).getTime()
  if (Number.isNaN(t)) return false
  return t < Date.now()
}

async function saveDealTitle() {
  if (!deal.value) return
  await dealsStore.updateDeal(dealId, { title: titleEdit.value })
  await fetchData()
}

async function saveReassignOwner() {
  if (!deal.value || !reassignUserId.value.trim()) return
  if (reassignUserId.value.trim() === (deal.value.userId || '').trim()) return
  isSavingReassign.value = true
  try {
    const updated = await dealsStore.updateDeal(dealId, { userId: reassignUserId.value.trim() })
    if (updated) deal.value = updated
    await fetchData()
  } finally {
    isSavingReassign.value = false
  }
}

async function deleteThisDeal() {
  if (!confirm(t('dealDetail.confirmDeleteDeal'))) return
  const ok = await dealsStore.deleteDeal(dealId)
  if (ok) router.push('/deals')
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

function intlLocaleTag(): string {
  const loc = locale.value
  if (loc === 'ru') return 'ru-RU'
  if (loc === 'kk') return 'kk-KZ'
  return 'en-US'
}

function formatCurrency(val: number): string {
  return new Intl.NumberFormat(intlLocaleTag(), { style: 'currency', currency: 'USD' }).format(val)
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString(intlLocaleTag(), {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function historyFieldLabel(field: string): string {
  const p = `dealDetail.historyField.${field}`
  return te(p) ? t(p) : field
}

function historyCellText(field: string, val: string | null): string {
  if (val == null || val === '') return '—'
  if (field === 'userId') return userDisplayName(val)
  if (val.length > 96) return `${val.slice(0, 96)}…`
  return val
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
        <div class="flex flex-col gap-2 flex-1 min-w-0">
          <div class="flex items-center gap-4">
            <button @click="router.back()" class="p-2 hover:bg-gray-100 rounded-full text-gray-400 transition-colors shrink-0">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
            </button>
            <div class="min-w-0 flex-1">
              <input
                v-model="titleEdit"
                class="text-2xl font-bold text-gray-900 w-full border border-transparent hover:border-gray-200 focus:border-indigo-300 rounded-lg px-2 py-1 -ml-2"
              />
              <div class="flex items-center gap-2 mt-1 flex-wrap">
                <span class="px-2.5 py-0.5 rounded-full text-xs font-bold" :class="stageClass[deal.stage]">
                  {{ dealStageLabel(deal.stage) }}
                </span>
                <span class="text-xs text-gray-400 font-mono">ID: {{ deal.id.slice(0, 8) }}</span>
                <button type="button" class="text-xs font-semibold text-indigo-600" @click="saveDealTitle">{{ t('dealDetail.saveTitle') }}</button>
                <button type="button" class="text-xs font-semibold text-red-600" @click="deleteThisDeal">{{ t('dealDetail.deleteDeal') }}</button>
              </div>
            </div>
          </div>
        </div>
        <div class="bg-emerald-50 px-6 py-3 rounded-2xl border border-emerald-100 text-right">
          <div class="text-2xl font-black text-emerald-600">{{ formatCurrency(deal.value) }}</div>
          <div class="text-[10px] text-emerald-600/70 font-bold uppercase tracking-widest">{{ t('dealDetail.dealValue') }}</div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main Info -->
        <div class="lg:col-span-2 space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h3 class="text-sm font-black text-gray-900 uppercase tracking-widest mb-6 border-b border-gray-50 pb-2">{{ t('dealDetail.dealContext') }}</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <label class="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-1">{{ t('dealDetail.statusLabel') }}</label>
                <p class="font-bold text-gray-900 flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full" :class="deal.closedAt ? 'bg-gray-400' : 'bg-green-500 animate-pulse'"></span>
                  {{ deal.closedAt ? t('dealDetail.archive') : t('dealDetail.inPipeline') }}
                </p>
              </div>
              <div>
                <label class="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-1">{{ t('dealDetail.responsible') }}</label>
                <div v-if="manager" class="flex flex-col">
                  <span class="font-bold text-gray-900">{{ manager.name }}</span>
                  <span class="text-[10px] text-indigo-600 font-bold uppercase">{{ userRoleLabel(manager.role) }}</span>
                </div>
                <div v-else-if="deal.userId && String(deal.userId).trim()" class="flex flex-col">
                  <span class="font-bold text-gray-900">{{ userDisplayName(deal.userId) }}</span>
                  <span class="text-[10px] text-gray-500 font-bold uppercase">id: {{ String(deal.userId).slice(0, 8) }}…</span>
                </div>
                <p v-else class="text-gray-400 italic">{{ t('dealDetail.notAssigned') }}</p>
              </div>
              <div>
                <label class="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-1">{{ t('dealDetail.createdBy') }}</label>
                <div v-if="creator" class="flex flex-col">
                  <span class="font-bold text-gray-900">{{ creator.name }}</span>
                  <span class="text-[10px] text-gray-500 font-bold uppercase">{{ creator.email }}</span>
                </div>
                <div
                  v-else-if="(deal.createdById && String(deal.createdById).trim()) || (deal.userId && String(deal.userId).trim())"
                  class="flex flex-col"
                >
                  <span class="font-bold text-gray-900">{{ userDisplayName(deal.createdById || deal.userId) }}</span>
                </div>
                <p v-else class="text-gray-400 italic">{{ t('dealDetail.notSpecifiedCreator') }}</p>
              </div>
              <div>
                <label class="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-1">{{ t('dealDetail.closingDate') }}</label>
                <p class="font-bold text-gray-900">{{ deal.closedAt ? formatDate(deal.closedAt) : t('dealDetail.pendingClose') }}</p>
              </div>
            </div>

            <div
              v-if="canReassignDeal && assignableColleagues.length"
              class="mt-6 pt-6 border-t border-gray-50"
            >
              <label class="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-2">{{
                t('dealDetail.reassignOwner')
              }}</label>
              <div class="flex flex-wrap gap-3 items-center">
                <select
                  v-model="reassignUserId"
                  class="flex-1 min-w-[200px] max-w-md border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white"
                >
                  <option v-for="u in assignableColleagues" :key="u.id" :value="u.id">
                    {{ u.name }} — {{ u.email }}
                  </option>
                </select>
                <button
                  type="button"
                  class="btn-primary text-sm py-2 px-4 shrink-0"
                  :disabled="
                    isSavingReassign ||
                    !reassignUserId.trim() ||
                    reassignUserId.trim() === (deal.userId && String(deal.userId).trim())
                  "
                  @click="saveReassignOwner"
                >
                  {{ t('dealDetail.reassignSave') }}
                </button>
              </div>
            </div>
            
            <div v-if="deal.notes" class="mt-8 pt-6 border-t border-gray-50">
               <label class="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-2">{{ t('dealDetail.originalDescription') }}</label>
               <p class="text-sm text-gray-600 bg-gray-50 p-4 rounded-xl italic">{{ deal.notes }}</p>
            </div>
          </div>

          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 overflow-x-auto">
            <h3 class="text-sm font-black text-gray-900 uppercase tracking-widest mb-4 border-b border-gray-50 pb-2">
              {{ t('dealDetail.historyTitle') }}
            </h3>
            <p v-if="dealHistory.length === 0" class="text-sm text-gray-400">{{ t('dealDetail.historyEmpty') }}</p>
            <table v-else class="w-full text-sm min-w-[640px]">
              <thead>
                <tr class="text-left text-[10px] uppercase text-gray-400 font-black tracking-widest border-b border-gray-100">
                  <th class="pb-2 pr-3">{{ t('dealDetail.historyColTime') }}</th>
                  <th class="pb-2 pr-3">{{ t('dealDetail.historyColField') }}</th>
                  <th class="pb-2 pr-3">{{ t('dealDetail.historyColOld') }}</th>
                  <th class="pb-2 pr-3">{{ t('dealDetail.historyColNew') }}</th>
                  <th class="pb-2">{{ t('dealDetail.historyColUser') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in dealHistory"
                  :key="row.id"
                  class="border-b border-gray-50 last:border-0 align-top"
                >
                  <td class="py-2 pr-3 text-gray-500 whitespace-nowrap">{{ formatDate(row.changed_at) }}</td>
                  <td class="py-2 pr-3 font-medium text-gray-800">{{ historyFieldLabel(row.field) }}</td>
                  <td class="py-2 pr-3 text-gray-600 break-all max-w-[200px]">{{ historyCellText(row.field, row.old_value) }}</td>
                  <td class="py-2 pr-3 text-gray-600 break-all max-w-[200px]">{{ historyCellText(row.field, row.new_value) }}</td>
                  <td class="py-2 text-gray-700">{{ row.changed_by_name || row.changed_by_id || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h3 class="text-sm font-black text-gray-900 uppercase tracking-widest mb-4 border-b border-gray-50 pb-2">
              {{ t('dealDetail.tasksTitle') }}
            </h3>
            <div class="flex flex-col sm:flex-row gap-3 mb-4">
              <input
                v-model="newTaskTitle"
                type="text"
                class="flex-1 min-w-0 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                :placeholder="t('dealDetail.tasksPlaceholder')"
              />
              <input
                v-model="newTaskDue"
                type="datetime-local"
                class="sm:w-56 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                :title="t('dealDetail.tasksDueHint')"
              />
            </div>
            <div v-if="canDelegateTasks" class="mb-4">
              <label class="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-1.5">{{
                t('dealDetail.tasksAssignLabel')
              }}</label>
              <select
                v-model="newTaskAssigneeId"
                class="w-full max-w-md border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white"
              >
                <option v-for="u in taskAssignForSelect" :key="u.id" :value="u.id">
                  {{ u.name }} — {{ u.email }}
                </option>
              </select>
              <p class="text-[11px] text-gray-500 mt-1">{{ t('dealDetail.tasksAssignHint') }}</p>
            </div>
            <p v-else class="mb-4 text-[11px] text-gray-500 bg-gray-50 rounded-lg px-3 py-2 border border-gray-100 max-w-2xl">
              {{ t('dealDetail.tasksAssignSalesNote') }}
            </p>
            <div class="mb-6">
              <button
                type="button"
                class="btn-primary text-sm py-2 px-4 shrink-0 disabled:opacity-50"
                :disabled="!newTaskTitle.trim() || isSavingTask"
                @click="addTask"
              >
                {{ t('dealDetail.tasksAdd') }}
              </button>
            </div>
            <p v-if="tasks.length === 0" class="text-sm text-gray-400">{{ t('dealDetail.tasksEmpty') }}</p>
            <ul v-else class="space-y-3">
              <li
                v-for="task in tasks"
                :key="task.id"
                class="flex flex-wrap items-start gap-3 p-4 rounded-xl border transition-colors"
                :class="
                  isTaskOverdue(task)
                    ? 'border-amber-300 bg-amber-50/70'
                    : task.isDone
                      ? 'border-gray-100 bg-gray-50/50 opacity-80'
                      : 'border-gray-100 bg-white'
                "
              >
                <label class="flex items-start gap-2 cursor-pointer shrink-0 pt-0.5">
                  <input
                    type="checkbox"
                    class="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4 mt-0.5"
                    :aria-label="t('dealDetail.tasksDoneToggle')"
                    :checked="!!task.isDone"
                    :disabled="togglingTaskId === task.id"
                    @change="toggleTaskDone(task)"
                  />
                </label>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-semibold text-gray-900 break-words" :class="{ 'line-through text-gray-500': !!task.isDone }">
                    {{ task.title }}
                  </p>
                  <p class="text-[11px] text-gray-500 mt-1">
                    <span v-if="task.dueAt">{{ t('dealDetail.tasksDueLabel') }}: {{ formatDate(task.dueAt) }}</span>
                    <span v-else>{{ t('dealDetail.tasksNoDue') }}</span>
                    <span v-if="task.assignedUserId" class="ml-2">
                      · {{ t('dealDetail.tasksAssigneeShort') }}: {{ userDisplayName(task.assignedUserId) }}
                    </span>
                    <span v-if="task.createdBy" class="ml-2">
                      · {{ t('dealDetail.tasksAuthorShort') }}: {{ userDisplayName(task.createdBy) }}
                    </span>
                  </p>
                  <p v-if="isTaskOverdue(task)" class="text-[11px] font-bold text-amber-700 mt-1">
                    {{ t('dealDetail.tasksOverdue') }}
                  </p>
                  <div v-if="canDelegateTasks && !task.isDone && taskAssignForSelect.length" class="mt-2 max-w-md">
                    <label class="text-[10px] text-gray-400 uppercase font-black block mb-1">{{
                      t('dealDetail.tasksReassignLabel')
                    }}</label>
                    <select
                      class="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-xs bg-white"
                      :value="task.assignedUserId || ''"
                      @change="updateTaskAssignee(task, $event)"
                    >
                      <option v-for="u in taskAssignForSelect" :key="u.id" :value="u.id">
                        {{ u.name }} — {{ u.email }}
                      </option>
                    </select>
                  </div>
                </div>
                <button
                  type="button"
                  class="text-xs font-bold text-red-600 hover:text-red-800 shrink-0"
                  @click="deleteTask(task)"
                >
                  {{ t('dealDetail.tasksDelete') }}
                </button>
              </li>
            </ul>
          </div>

          <template v-if="deal.contactId && String(deal.contactId).trim()">
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4">
              <div>
                <h3 class="text-sm font-black text-gray-900 uppercase tracking-widest">{{ t('dealDetail.aiSectionTitle') }}</h3>
                <p class="text-xs text-gray-500 mt-1">{{ t('dealDetail.aiSubtitle') }}</p>
              </div>
              <p v-if="dealAiError" class="text-sm text-red-600">{{ dealAiError }}</p>
              <div v-else class="grid md:grid-cols-2 gap-4">
                <AIPredictionCard
                  kind="lead"
                  :title="t('dealDetail.aiLeadTitle')"
                  :prediction="dealAiLead"
                  :loading="dealAiLoading"
                />
                <AIPredictionCard
                  kind="churn"
                  :title="t('dealDetail.aiChurnTitle')"
                  :prediction="dealAiChurn"
                  :loading="dealAiLoading"
                />
              </div>
            </div>
          </template>
          <div v-else class="text-sm text-gray-500 bg-gray-50 rounded-xl p-4 border border-gray-100">
            {{ t('dealDetail.aiNoContact') }}
          </div>

          <!-- Notes / Timeline -->
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div class="p-6 border-b border-gray-50 flex items-center justify-between">
              <h3 class="text-sm font-black text-gray-900 uppercase tracking-widest">{{ t('dealDetail.timelineTitle') }}</h3>
              <span class="bg-gray-100 text-gray-600 text-[10px] px-2 py-0.5 rounded-full font-bold">{{ t('dealDetail.notesCount', { n: notes.length }) }}</span>
            </div>
            
            <!-- Add Note Input -->
            <div class="p-4 bg-gray-50/50">
              <div class="relative">
                <textarea 
                  v-model="newNoteContent"
                  rows="2" 
                  class="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none transition-all shadow-inner" 
                  :placeholder="t('dealDetail.notePlaceholder')"
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
                  <span class="text-xs font-black text-gray-900">{{
                    note.authorName || userDisplayName(noteUserId(note)) || t('dealDetail.unknownAuthor')
                  }}</span>
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
                <p class="text-gray-400 text-sm italic">{{ t('dealDetail.notesEmpty') }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Sidebar Info -->
        <div class="space-y-6">
          <div
            v-if="contact"
            class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 cursor-pointer hover:border-indigo-200 transition-colors"
            role="button"
            tabindex="0"
            @click="openLinkedContact"
            @keydown.enter="openLinkedContact"
          >
            <h3 class="text-sm font-black text-gray-900 uppercase tracking-widest mb-6">{{ t('dealDetail.linkedContact') }}</h3>
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
                <label class="text-[9px] text-gray-400 font-black uppercase tracking-widest mb-1">{{ t('dealDetail.email') }}</label>
                <div class="flex items-center gap-2">
                   <svg class="w-3 h-3 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                   <span class="text-sm text-gray-600 truncate font-medium">{{ contact.email }}</span>
                </div>
              </div>
              <div class="flex flex-col">
                <label class="text-[9px] text-gray-400 font-black uppercase tracking-widest mb-1">{{ t('dealDetail.phone') }}</label>
                <div class="flex items-center gap-2">
                   <svg class="w-3 h-3 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
                   <span class="text-sm text-gray-600 font-medium">{{ contact.phone }}</span>
                </div>
              </div>
            </div>
            <button
              type="button"
              class="w-full mt-8 py-3 text-xs font-black text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 uppercase tracking-widest"
              @click.stop="openLinkedContact"
            >
              {{ t('dealDetail.contactDossier') }}
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
