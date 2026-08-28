import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '../api/client'

export interface StaffUser {
  id: number
  username: string
  display_name: string
  role: 'admin' | 'doctor'
  department_name?: string
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

  function logout() {
    localStorage.removeItem('staff_token')
    localStorage.removeItem('staff_user')
    user.value = null
  }

  return { user, loggedIn, login, logout }
})

