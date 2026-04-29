import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi } from '../api/auth'
import { getMe } from '../api/user'

export const useUserStore = defineStore('user', () => {
  const token = ref(sessionStorage.getItem('token') || '')
  const user = ref(JSON.parse(sessionStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || '')
  const isAdmin = computed(() => userRole.value === 'admin')
  const isLandlord = computed(() => userRole.value === 'landlord')
  const isTenant = computed(() => userRole.value === 'tenant')

  async function login(username, password) {
    const res = await loginApi(username, password)
    token.value = res.access_token
    sessionStorage.setItem('token', res.access_token)

    await new Promise(resolve => setTimeout(resolve, 50))

    await fetchUser()
  }

  async function register(data) {
    await registerApi(data)
  }

  async function fetchUser() {
    try {
      const res = await getMe()
      user.value = res
      sessionStorage.setItem('user', JSON.stringify(res))
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('user')
  }

  return { token, user, isLoggedIn, userRole, isAdmin, isLandlord, isTenant, login, register, fetchUser, logout }
})
