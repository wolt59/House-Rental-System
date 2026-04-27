import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi } from '../api/auth'
import { getMe } from '../api/user'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || '')
  const isAdmin = computed(() => userRole.value === 'admin')
  const isLandlord = computed(() => userRole.value === 'landlord')
  const isTenant = computed(() => userRole.value === 'tenant')

  async function login(username, password) {
    const res = await loginApi(username, password)
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
    await fetchUser()
  }

  async function register(data) {
    await registerApi(data)
  }

  async function fetchUser() {
    const res = await getMe()
    user.value = res
    localStorage.setItem('user', JSON.stringify(res))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isLoggedIn, userRole, isAdmin, isLandlord, isTenant, login, register, fetchUser, logout }
})
