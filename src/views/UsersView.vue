<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const users = ref<any[]>([])
const showForm = ref(false)

const name = ref('')
const email = ref('')
const password = ref('')
const role = ref('user')

async function fetchUsers() {
  try {
    const res = await fetch('/api/users', {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (res.ok) users.value = await res.json()
  } catch (e) {
    console.error(e)
  }
}

async function createUser() {
  try {
    const res = await fetch('/api/users', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ 
        name: name.value, 
        email: email.value, 
        password: password.value, 
        role: role.value,
        company_id: authStore.user?.company_id || null
      })
    })
    if (res.ok) {
      showForm.value = false
      name.value = ''
      email.value = ''
      password.value = ''
      role.value = 'user'
      await fetchUsers()
    } else {
      const data = await res.json()
      alert('Error: ' + data.detail)
    }
  } catch (e) {
    console.error(e)
  }
}

async function deleteUser(id: string) {
  if (!confirm('Are you sure you want to delete this user?')) return
  try {
    const res = await fetch(`/api/users/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (res.ok) {
      await fetchUsers()
    } else {
      const data = await res.json()
      alert('Error: ' + data.detail)
    }
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  if (authStore.userRole === 'admin' || authStore.userRole === 'super_admin') {
    fetchUsers()
  }
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Team Management</h1>
        <p class="text-sm text-gray-500 mt-1">Manage users, managers and admins in your company.</p>
      </div>
      <button v-if="authStore.userRole !== 'user'" @click="showForm = true" class="btn-primary">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>
        New User
      </button>
    </div>

    <div v-if="authStore.userRole === 'user'" class="card text-center py-12 text-gray-500">
      <svg class="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
      You don't have permission to access team settings. <br/> Please contact your company's administrator.
    </div>

    <div v-else class="card overflow-hidden !p-0">
      <table class="w-full text-left">
        <thead class="bg-gray-50">
          <tr>
            <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Name</th>
            <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Email</th>
            <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Role</th>
            <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
            <th class="py-3 px-4 text-xs text-right font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
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
              <span class="px-2.5 py-1 rounded-md text-xs font-medium"
                :class="{
                  'bg-purple-100 text-purple-700': u.role === 'super_admin',
                  'bg-blue-100 text-blue-700': u.role === 'admin',
                  'bg-gray-100 text-gray-600': u.role === 'user'
                }">
                {{ u.role.replace('_', ' ').toUpperCase() }}
              </span>
            </td>
            <td class="py-3 px-4">
               <span class="flex items-center gap-1.5 text-xs text-green-700 font-medium bg-green-50 px-2 py-1 rounded w-fit">
                <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                Active
               </span>
            </td>
            <td class="py-3 px-4 text-right">
              <button 
                v-if="u.id !== authStore.user?.id && (authStore.userRole === 'super_admin' || u.role !== 'super_admin')"
                @click="deleteUser(u.id)" 
                class="text-red-500 hover:text-red-700 text-sm font-medium transition-colors"
               >
                Remove
              </button>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="5" class="py-8 text-center text-sm text-gray-500">No users found in your company.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Form -->
    <div v-if="showForm" class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md m-4 transform transition-all">
        <h3 class="text-xl font-bold text-gray-900 mb-2">Add New Team Member</h3>
        <p class="text-sm text-gray-500 mb-6">Create a new account within your company workspace.</p>
        
        <form @submit.prevent="createUser" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input v-model="name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" placeholder="Jane Doe" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
            <input v-model="email" type="email" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" placeholder="jane@example.com" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Temporary Password</label>
            <input v-model="password" type="password" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" placeholder="••••••••" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Role Permissions</label>
            <select v-model="role" class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all">
              <option value="user">User (View & Edit Deals)</option>
              <option value="admin">Admin (Manage Team & Settings)</option>
              <option v-if="authStore.userRole === 'super_admin'" value="super_admin">Super Admin (Global System Admin)</option>
            </select>
          </div>
          
          <div class="flex gap-3 justify-end pt-4 mt-2 border-t border-gray-100">
            <button type="button" @click="showForm = false" class="px-4 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">Cancel</button>
            <button type="submit" class="btn-primary px-6 py-2.5">Create Account</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
