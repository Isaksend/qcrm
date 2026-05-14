<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { apiUrl } from '../lib/api'

const { t } = useI18n()
const authStore = useAuthStore()
const users = ref<any[]>([])
const companies = ref<{ id: string; name: string }[]>([])
const showForm = ref(false)
const showEdit = ref(false)

const name = ref('')
const email = ref('')
const password = ref('')
const role = ref('sales_representative')
const newUserCompanyId = ref('')

const editId = ref('')
const editName = ref('')
const editRole = ref('sales_representative')
const editCompanyId = ref('')
const editActive = ref(true)

async function fetchCompanies() {
  if (authStore.userRole !== 'super_admin') return
  try {
    const res = await fetch(apiUrl('/api/companies'), {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (res.ok) {
      const data = await res.json()
      companies.value = data.map((c: any) => ({ id: c.id, name: c.name }))
      if (!newUserCompanyId.value && companies.value.length) {
        newUserCompanyId.value = companies.value[0].id
      }
    }
  } catch (e) {
    console.error(e)
  }
}

async function fetchUsers() {
  try {
    const res = await fetch(apiUrl('/api/users'), {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (res.ok) users.value = await res.json()
  } catch (e) {
    console.error(e)
  }
}

async function createUser() {
  try {
    let company_id: string | null = authStore.user?.company_id || null
    if (authStore.userRole === 'super_admin') {
      company_id = role.value === 'super_admin' ? null : newUserCompanyId.value || null
    }
    const res = await fetch(apiUrl('/api/users'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({
        name: name.value,
        email: email.value,
        password: password.value,
        role: role.value,
        company_id,
      }),
    })
    if (res.ok) {
      showForm.value = false
      name.value = ''
      email.value = ''
      password.value = ''
      role.value = 'sales_representative'
      newUserCompanyId.value = companies.value[0]?.id || ''
      await fetchUsers()
    } else {
      const data = await res.json()
      alert(`${t('users.errorPrefix')} ${data.detail}`)
    }
  } catch (e) {
    console.error(e)
  }
}

async function deleteUser(id: string) {
  if (!confirm(t('users.confirmDelete'))) return
  try {
    const res = await fetch(apiUrl(`/api/users/${id}`), {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (res.ok) {
      await fetchUsers()
    } else {
      const data = await res.json()
      alert(`${t('users.errorPrefix')} ${data.detail}`)
    }
  } catch (e) {
    console.error(e)
  }
}

function openEditUser(u: any) {
  editId.value = u.id
  editName.value = u.name
  editRole.value = u.role
  editCompanyId.value = u.company_id || ''
  editActive.value = u.is_active === 1
  showEdit.value = true
}

function closeEdit() {
  showEdit.value = false
}

async function saveEditUser() {
  try {
    const body: Record<string, unknown> = {
      name: editName.value,
      role: editRole.value,
      is_active: editActive.value ? 1 : 0,
    }
    if (editRole.value !== 'super_admin') {
      body.company_id = editCompanyId.value || null
    } else {
      body.company_id = null
    }
    const res = await fetch(apiUrl(`/api/users/${editId.value}`), {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify(body),
    })
    if (res.ok) {
      closeEdit()
      await fetchUsers()
    } else {
      const data = await res.json()
      alert(`${t('users.errorPrefix')} ${data.detail}`)
    }
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  if (['admin', 'super_admin', 'manager'].includes(authStore.userRole)) {
    fetchUsers()
    fetchCompanies()
  }
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ t('users.title') }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ t('users.subtitle') }}</p>
      </div>
      <button v-if="['admin', 'super_admin', 'manager'].includes(authStore.userRole)" @click="showForm = true" class="btn-primary">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        {{ t('users.newUser') }}
      </button>
    </div>

    <div v-if="!['admin', 'super_admin', 'manager'].includes(authStore.userRole)" class="card text-center py-12 text-gray-500">
      <svg class="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
      </svg>
      {{ t('users.noAccess') }}
      <br />
      {{ t('users.contactAdmin') }}
    </div>

    <div v-else class="card overflow-hidden !p-0">
      <table class="w-full text-left">
        <thead class="bg-gray-50">
          <tr>
            <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ t('users.table.name') }}</th>
            <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ t('users.table.email') }}</th>
            <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ t('users.table.role') }}</th>
            <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ t('users.table.status') }}</th>
            <th class="py-3 px-4 text-xs text-right font-semibold text-gray-500 uppercase tracking-wider">{{ t('users.table.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors">
            <td class="py-3 px-4">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-xs">
                  {{ u.name.charAt(0).toUpperCase() }}
                </div>
                <span class="font-medium text-gray-900">{{ u.name }}</span>
              </div>
            </td>
            <td class="py-3 px-4 text-gray-500 text-sm">{{ u.email }}</td>
            <td class="py-3 px-4">
              <span
                class="px-2.5 py-1 rounded-md text-xs font-medium"
                :class="{
                  'bg-purple-100 text-purple-700': u.role === 'super_admin',
                  'bg-blue-100 text-blue-700': u.role === 'admin',
                  'bg-amber-100 text-amber-800': u.role === 'manager',
                  'bg-emerald-100 text-emerald-800': u.role === 'sales_representative',
                  'bg-gray-100 text-gray-600': u.role === 'user',
                }"
              >
                {{ u.role.replace('_', ' ').toUpperCase() }}
              </span>
            </td>
            <td class="py-3 px-4">
              <span
                v-if="u.is_active === 1"
                class="flex items-center gap-1.5 text-xs text-green-700 font-medium bg-green-50 px-2 py-1 rounded w-fit"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                {{ t('users.active') }}
              </span>
              <span
                v-else
                class="flex items-center gap-1.5 text-xs text-gray-600 font-medium bg-gray-100 px-2 py-1 rounded w-fit"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-gray-400"></span>
                {{ t('users.inactive') }}
              </span>
            </td>
            <td class="py-3 px-4 text-right space-x-3">
              <button
                v-if="authStore.userRole === 'super_admin' && u.id !== authStore.user?.id"
                type="button"
                class="text-indigo-600 hover:text-indigo-800 text-sm font-medium transition-colors"
                @click="openEditUser(u)"
              >
                {{ t('users.edit') }}
              </button>
              <button
                v-if="
                  u.id !== authStore.user?.id &&
                  (authStore.userRole === 'super_admin' ||
                    (authStore.userRole === 'admin' && u.role !== 'super_admin' && u.role !== 'admin') ||
                    (authStore.userRole === 'manager' && u.role === 'sales_representative'))
                "
                @click="deleteUser(u.id)"
                class="text-red-500 hover:text-red-700 text-sm font-medium transition-colors"
              >
                {{ t('users.remove') }}
              </button>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="5" class="py-8 text-center text-sm text-gray-500">{{ t('users.empty') }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showForm" class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md m-4 transform transition-all">
        <h3 class="text-xl font-bold text-gray-900 mb-2">{{ t('users.modalTitle') }}</h3>
        <p class="text-sm text-gray-500 mb-6">{{ t('users.modalHint') }}</p>

        <form @submit.prevent="createUser" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('auth.fullName') }}</label>
            <input
              v-model="name"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              placeholder="Jane Doe"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('users.emailAddress') }}</label>
            <input
              v-model="email"
              type="email"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              placeholder="jane@example.com"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('users.tempPassword') }}</label>
            <input
              v-model="password"
              type="password"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              placeholder="••••••••"
            />
          </div>
          <div v-if="authStore.userRole === 'super_admin' && role !== 'super_admin'">
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('users.companyLabel') }}</label>
            <select
              v-model="newUserCompanyId"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
            >
              <option value="">{{ t('users.companyPlaceholder') }}</option>
              <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('users.rolePermissions') }}</label>
            <select
              v-model="role"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
            >
              <option value="sales_representative">{{ t('users.roleUser') }}</option>
              <option v-if="authStore.userRole !== 'manager'" value="manager">{{ t('users.roleManager') }}</option>
              <option v-if="authStore.userRole === 'super_admin'" value="admin">{{ t('users.roleAdmin') }}</option>
              <option v-if="authStore.userRole === 'super_admin'" value="super_admin">{{ t('users.roleSuper') }}</option>
            </select>
          </div>

          <div class="flex gap-3 justify-end pt-4 mt-2 border-t border-gray-100">
            <button type="button" @click="showForm = false" class="px-4 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
              {{ t('common.cancel') }}
            </button>
            <button type="submit" class="btn-primary px-6 py-2.5">{{ t('users.createAccount') }}</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showEdit" class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md m-4 transform transition-all max-h-[90vh] overflow-y-auto">
        <h3 class="text-xl font-bold text-gray-900 mb-2">{{ t('users.editTitle') }}</h3>
        <p class="text-sm text-gray-500 mb-6">{{ t('users.editHint') }}</p>
        <form @submit.prevent="saveEditUser" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('auth.fullName') }}</label>
            <input
              v-model="editName"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('users.rolePermissions') }}</label>
            <select
              v-model="editRole"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
            >
              <option value="sales_representative">{{ t('users.roleUser') }}</option>
              <option value="manager">{{ t('users.roleManager') }}</option>
              <option value="admin">{{ t('users.roleAdmin') }}</option>
              <option value="super_admin">{{ t('users.roleSuper') }}</option>
            </select>
          </div>
          <div v-if="editRole !== 'super_admin'">
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('users.companyLabel') }}</label>
            <select
              v-model="editCompanyId"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
            >
              <option value="">{{ t('users.companyPlaceholder') }}</option>
              <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <input id="edit-active" v-model="editActive" type="checkbox" class="rounded border-gray-300 text-indigo-600" />
            <label for="edit-active" class="text-sm text-gray-700">{{ t('users.active') }}</label>
          </div>
          <div class="flex gap-3 justify-end pt-4 mt-2 border-t border-gray-100">
            <button type="button" class="px-4 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg" @click="closeEdit">
              {{ t('common.cancel') }}
            </button>
            <button type="submit" class="btn-primary px-6 py-2.5">{{ t('users.saveChanges') }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
