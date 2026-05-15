<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useContactsStore } from '../../stores/contacts'
import { useDealsStore } from '../../stores/deals'

const entityType = defineModel<'contact' | 'deal'>('entityType', { default: 'contact' })
const modelValue = defineModel<string>({ default: '' })

const { t, locale } = useI18n()
const contactsStore = useContactsStore()
const dealsStore = useDealsStore()
const query = ref('')
const open = ref(false)

const selectedLabel = computed(() => {
  locale.value
  if (!modelValue.value) return ''
  if (entityType.value === 'contact') {
    const c = contactsStore.contacts.find((x) => x.id === modelValue.value)
    return c ? `${c.name} (${c.email})` : modelValue.value.slice(0, 8)
  }
  const d = dealsStore.deals.find((x) => x.id === modelValue.value)
  return d ? `${d.title} — ${d.stage}` : modelValue.value.slice(0, 8)
})

const results = computed(() => {
  locale.value
  const q = query.value.toLowerCase().trim()
  if (entityType.value === 'contact') {
    return contactsStore.contacts
      .filter(
        (c) =>
          !q ||
          c.name.toLowerCase().includes(q) ||
          c.email.toLowerCase().includes(q) ||
          (c.company || '').toLowerCase().includes(q),
      )
      .slice(0, 8)
      .map((c) => ({ id: c.id, title: c.name, subtitle: c.email }))
  }
  return dealsStore.deals
    .filter((d) => !q || d.title.toLowerCase().includes(q) || d.stage.toLowerCase().includes(q))
    .slice(0, 8)
    .map((d) => ({ id: d.id, title: d.title, subtitle: `${d.stage} · $${d.value}` }))
})

function pick(id: string) {
  modelValue.value = id
  open.value = false
  query.value = ''
}

</script>

<template>
  <div class="space-y-2">
    <select
      v-model="entityType"
      class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
      @change="modelValue = ''; query = ''"
    >
      <option value="contact">{{ t('globalSearch.types.contact') }}</option>
      <option value="deal">{{ t('globalSearch.types.deal') }}</option>
    </select>

    <div class="relative">
      <input
        v-model="query"
        type="text"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
        :placeholder="t('activities.searchEntity')"
        @focus="open = true"
      />
      <p v-if="modelValue && !open" class="text-xs text-gray-500 mt-1 truncate">
        {{ t('activities.selected') }}: {{ selectedLabel }}
      </p>
      <ul
        v-if="open && results.length"
        class="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
      >
        <li v-for="r in results" :key="r.id">
          <button
            type="button"
            class="w-full text-left px-3 py-2 hover:bg-gray-50 text-sm"
            @mousedown.prevent="pick(r.id)"
          >
            <span class="font-medium text-gray-900">{{ r.title }}</span>
            <span class="block text-xs text-gray-500">{{ r.subtitle }}</span>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>
