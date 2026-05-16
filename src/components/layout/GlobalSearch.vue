<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useContactsStore } from '../../stores/contacts'
import { useDealsStore } from '../../stores/deals'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const { t, locale } = useI18n()
const router = useRouter()
const contactsStore = useContactsStore()
const dealsStore = useDealsStore()

const query = ref('')
const searchInput = ref<HTMLInputElement | null>(null)

function close() {
  emit('update:modelValue', false)
  setTimeout(() => {
    query.value = ''
  }, 200)
}

const results = computed(() => {
  locale.value
  const q = query.value.toLowerCase().trim()
  if (!q) return []

  const list: { id: string; typeKey: 'contact' | 'deal'; title: string; subtitle: string; route: string }[] = []

  contactsStore.contacts.forEach((c) => {
    if (
      c.name.toLowerCase().includes(q) ||
      c.company.toLowerCase().includes(q) ||
      c.email.toLowerCase().includes(q)
    ) {
      list.push({
        id: c.id,
        typeKey: 'contact',
        title: c.name,
        subtitle: `${c.company} • ${c.email}`,
        route: '/contacts',
      })
    }
  })

  dealsStore.deals.forEach((d) => {
    if (d.title.toLowerCase().includes(q)) {
      list.push({
        id: d.id,
        typeKey: 'deal',
        title: d.title,
        subtitle: `${d.stage} • $${d.value}`,
        route: `/deals/${d.id}`,
      })
    }
  })

  return list.slice(0, 8)
})

function typeLabel(typeKey: 'contact' | 'deal') {
  return t(`globalSearch.types.${typeKey}`)
}

function selectResult(route: string) {
  router.push(route)
  close()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.modelValue) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  if (props.modelValue && searchInput.value) {
    searchInput.value.focus()
  }
})

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      nextTick(() => {
        searchInput.value?.focus()
      })
    }
  }
)

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div v-if="modelValue" class="fixed inset-0 z-[100] flex items-start justify-center pt-16 sm:pt-24 backdrop-blur-sm bg-gray-900/40 transition-opacity">
    <div class="fixed inset-0" @click="close"></div>

    <div class="relative w-full max-w-xl bg-white rounded-xl shadow-2xl ring-1 ring-black/5 overflow-hidden transform transition-all mx-4">
      <div class="flex items-center px-4 py-3 border-b border-gray-100 gap-2">
        <svg class="w-5 h-5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          ref="searchInput"
          v-model="query"
          type="text"
          class="flex-1 min-w-0 border-0 focus:ring-0 text-sm text-gray-900 placeholder-gray-400 outline-none bg-transparent"
          :placeholder="t('globalSearch.placeholder')"
        />
        <div class="text-[10px] font-medium tracking-wide text-gray-400 uppercase bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200 shrink-0">
          ESC
        </div>
      </div>

      <div class="max-h-96 overflow-y-auto py-2">
        <div v-if="!query" class="px-6 py-8 text-center text-sm text-gray-500">
          {{ t('globalSearch.empty') }}
        </div>

        <div v-else-if="results.length === 0" class="px-6 py-8 text-center text-sm text-gray-500">
          {{ t('globalSearch.noResults') }} <strong class="text-gray-900">{{ query }}</strong>
        </div>

        <ul v-else class="divide-y divide-gray-50">
          <li
            v-for="result in results"
            :key="result.id"
            class="px-4 py-3 hover:bg-gray-50 cursor-pointer flex items-center gap-3 transition-colors"
            @click="selectResult(result.route)"
          >
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-inner"
              :class="{
                'bg-blue-100 text-blue-600 border border-blue-200': result.typeKey === 'contact',
                'bg-green-100 text-emerald-600 border border-green-200': result.typeKey === 'deal',
              }"
            >
              <svg v-if="result.typeKey === 'contact'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
              <svg v-if="result.typeKey === 'deal'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>

            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-gray-900 truncate">{{ result.title }}</div>
              <div class="text-[11px] text-gray-500 truncate mt-0.5">{{ result.subtitle }}</div>
            </div>

            <div class="text-[10px] font-bold text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full border border-gray-200 shadow-sm uppercase shrink-0">
              {{ typeLabel(result.typeKey) }}
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
