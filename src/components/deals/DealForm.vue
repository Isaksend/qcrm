<script setup lang="ts">
import { reactive, onMounted, ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDealsStore } from '../../stores/deals'
import { useContactsStore } from '../../stores/contacts'
import { useAuthStore } from '../../stores/auth'
import type { Deal } from '../../types'
import { apiUrl } from '../../lib/api'
import { buildE164FromDialAndNational, normalizePhoneDigits } from '../../lib/phone'
import { dialForIso2 } from '../../lib/countries'
import CountryPhoneFields from '../contacts/CountryPhoneFields.vue'
import type { CountryPhoneModel } from '../contacts/CountryPhoneFields.vue'

const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()
const dealsStore = useDealsStore()
const contactsStore = useContactsStore()
const authStore = useAuthStore()

const teamMembers = ref<any[]>([])
const companies = ref<{ id: string; name: string }[]>([])
const contactFound = ref(false)
const submitError = ref('')

const contactGeo = reactive<CountryPhoneModel>({
  countryIso2: 'KZ',
  nationalNumber: '',
  city: '',
})

const form = reactive({
  title: '',
  value: 0,
  stage: 'New Request' as Deal['stage'],
  userId: '',
  contactId: '',
  notes: '',
  dealCompanyId: '',
  contactName: '',
  contactEmail: '',
  contactCompany: '',
})

const contactFullPhone = computed(() =>
  buildE164FromDialAndNational(dialForIso2(contactGeo.countryIso2), contactGeo.nationalNumber)
)

async function fetchCompanies() {
  if (authStore.userRole !== 'super_admin') return
  try {
    const res = await fetch(apiUrl('/api/companies'), {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (res.ok) {
      const data = await res.json()
      companies.value = data.map((c: { id: string; name: string }) => ({ id: c.id, name: c.name }))
      if (!form.dealCompanyId && companies.value.length) {
        form.dealCompanyId = companies.value[0].id
      }
    }
  } catch (e) {
    console.error(e)
  }
}

async function fetchTeamMembers() {
  if (authStore.userRole === 'admin' || authStore.userRole === 'super_admin') {
    try {
      const res = await fetch(apiUrl('/api/users'), {
        headers: { Authorization: `Bearer ${authStore.token}` },
      })
      if (res.ok) teamMembers.value = await res.json()
    } catch (e) {
      console.error(e)
    }
  } else {
    teamMembers.value = authStore.user ? [authStore.user] : []
  }
}

watch(contactFullPhone, async (full) => {
  const digits = normalizePhoneDigits(full)
  if (digits.length < 7) {
    contactFound.value = false
    form.contactId = ''
    return
  }
  const contact = await contactsStore.searchContactByPhone(full.trim())
  if (contact) {
    form.contactId = contact.id
    form.contactName = contact.name
    form.contactEmail = contact.email
    form.contactCompany = contact.company
    contactFound.value = true
    const iso = (contact as { country_iso2?: string | null }).country_iso2
    if (iso) contactGeo.countryIso2 = iso
    const city = (contact as { city?: string | null }).city
    if (city) contactGeo.city = city
  } else {
    contactFound.value = false
    form.contactId = ''
  }
})

async function submit() {
  submitError.value = ''
  if (!form.title.trim()) return

  const digits = normalizePhoneDigits(contactFullPhone.value)
  if (digits.length < 7) {
    submitError.value = t('dealForm.errors.phone')
    return
  }
  if (!form.contactName.trim()) {
    submitError.value = t('dealForm.errors.name')
    return
  }

  if (authStore.userRole === 'super_admin' && !form.dealCompanyId.trim()) {
    submitError.value = t('dealForm.errors.superCompany')
    return
  }

  const { contact, error } = await contactsStore.findOrCreateContactForDeal({
    phone: contactFullPhone.value,
    name: form.contactName,
    email: form.contactEmail,
    company: form.contactCompany,
    country_iso2: contactGeo.countryIso2,
    city: contactGeo.city.trim() || null,
  })

  if (!contact) {
    submitError.value = error || t('dealForm.errors.contactFailed')
    return
  }

  const dealResult = await dealsStore.addDeal({
    leadId: '',
    contactId: contact.id,
    title: form.title,
    value: Number(form.value) || 0,
    stage: form.stage,
    closedAt:
      form.stage === 'Closed Won' || form.stage === 'Closed Lost'
        ? new Date().toISOString().slice(0, 10)
        : null,
    userId: form.userId || authStore.user?.id || '',
    companyId: authStore.userRole === 'super_admin' ? form.dealCompanyId || null : authStore.user?.company_id || null,
    notes: form.notes,
  })
  if (!dealResult.ok) {
    submitError.value = dealResult.error || t('dealForm.errors.dealFailed')
    return
  }
  emit('close')
}

onMounted(() => {
  fetchTeamMembers()
  fetchCompanies()
})
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/30" @click="$emit('close')"></div>
      <div class="relative bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-semibold text-gray-900">{{ t('dealForm.title') }}</h2>
            <button type="button" @click="$emit('close')" class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form @submit.prevent="submit" class="space-y-4">
            <div class="bg-indigo-50/50 p-4 rounded-xl space-y-3 mb-4 border border-indigo-100">
              <h3 class="text-xs font-bold text-indigo-900 uppercase tracking-wider">{{ t('dealForm.dealInfo') }}</h3>
              <div class="grid grid-cols-2 gap-4">
                <div class="col-span-2">
                  <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('dealForm.dealTitle') }}</label>
                  <input
                    v-model="form.title"
                    type="text"
                    required
                    class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    placeholder="Platform License"
                  />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('dealForm.value') }}</label>
                  <input
                    v-model.number="form.value"
                    type="number"
                    min="0"
                    class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    placeholder="100000"
                  />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('dealForm.assignedTo') }}</label>
                  <select
                    v-model="form.userId"
                    class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white"
                  >
                    <option value="">{{ t('dealForm.meDefault') }}</option>
                    <option v-for="m in teamMembers" :key="m.id" :value="m.id">{{ m.name }}</option>
                  </select>
                </div>
                <div v-if="authStore.userRole === 'super_admin'" class="col-span-2">
                  <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('dealForm.superCompanyLabel') }}</label>
                  <select
                    v-model="form.dealCompanyId"
                    required
                    class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white"
                  >
                    <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </select>
                </div>
                <div class="col-span-2">
                  <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('dealForm.notes') }}</label>
                  <textarea
                    v-model="form.notes"
                    rows="3"
                    class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
                    :placeholder="t('dealForm.notesPlaceholder')"
                  ></textarea>
                </div>
              </div>
            </div>

            <div class="bg-gray-50 p-4 rounded-xl space-y-3 border border-gray-100">
              <h3 class="text-xs font-bold text-gray-900 uppercase tracking-wider">{{ t('dealForm.contactLink') }}</h3>
              <p class="text-xs text-gray-500">
                {{ t('dealForm.contactHelp') }}
              </p>

              <CountryPhoneFields v-model="contactGeo" />

              <div v-if="contactFound" class="bg-green-50 text-green-700 text-[10px] font-bold py-1 px-2 rounded">
                {{ t('dealForm.contactFound') }}
              </div>

              <div class="space-y-3">
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('dealForm.name') }}</label>
                  <input
                    v-model="form.contactName"
                    type="text"
                    required
                    class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    :class="contactFound ? 'bg-gray-100' : ''"
                    :readonly="contactFound"
                  />
                </div>
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('dealForm.email') }}</label>
                    <input
                      v-model="form.contactEmail"
                      type="email"
                      class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                      :class="contactFound ? 'bg-gray-100' : ''"
                      :readonly="contactFound"
                      :placeholder="t('common.optional')"
                    />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">{{ t('dealForm.company') }}</label>
                    <input
                      v-model="form.contactCompany"
                      type="text"
                      class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                      :class="contactFound ? 'bg-gray-100' : ''"
                      :readonly="contactFound"
                    />
                  </div>
                </div>
              </div>
            </div>

            <p v-if="submitError" class="text-sm text-red-600">{{ submitError }}</p>

            <div class="flex justify-end gap-3 pt-2">
              <button type="button" @click="$emit('close')" class="btn-secondary">{{ t('common.cancel') }}</button>
              <button type="submit" class="btn-primary">{{ t('dealForm.createDeal') }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>
</template>
