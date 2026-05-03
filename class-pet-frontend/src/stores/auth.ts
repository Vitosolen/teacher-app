import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type RegisterPayload } from '@/api/auth'
import type { Teacher } from '@/types/domain'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const teacher = ref<Teacher | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  function setToken(t: string | null) {
    token.value = t
    if (t) {
      localStorage.setItem('token', t)
    } else {
      localStorage.removeItem('token')
    }
  }

  async function login(username: string, password: string) {
    const r = await authApi.login(username, password)
    setToken(r.access_token)
    teacher.value = await authApi.me()
  }

  async function register(payload: RegisterPayload) {
    await authApi.register(payload)
    await login(payload.username, payload.password)
  }

  async function fetchMe() {
    if (!token.value) return null
    teacher.value = await authApi.me()
    return teacher.value
  }

  function logout() {
    setToken(null)
    teacher.value = null
  }

  return { token, teacher, isLoggedIn, login, register, fetchMe, logout }
})
