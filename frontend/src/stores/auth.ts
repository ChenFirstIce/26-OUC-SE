import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '../api/client'

export interface StaffUser {
  id: number
  username: string
  display_name: string
  role: 'admin' | 'doctor'
  department_name?: string
  permissions?: {
    can_create_patients: boolean
    can_assign_questionnaires: boolean
    can_review_results: boolean
    can_manage_templates: boolean
  }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<StaffUser | null>(JSON.parse(localStorage.getItem('staff_user') || 'null'))
  const loggedIn = computed(() => Boolean(localStorage.getItem('staff_token') && user.value))

  async function login(username: string, password: string) {
    const { data } = await api.post('/auth/login', { username, password })
    localStorage.setItem('staff_token', data.access_token)
    localStorage.setItem('staff_user', JSON.stringify(data.user))
    user.value = data.user
  }

  async function refresh() {
    if (!localStorage.getItem('staff_token')) return
    const { data } = await api.get('/auth/me')
    localStorage.setItem('staff_user', JSON.stringify(data))
    user.value = data
  }

  function logout() {
    localStorage.removeItem('staff_token')
    localStorage.removeItem('staff_user')
    user.value = null
  }

  return { user, loggedIn, login, refresh, logout }
})
