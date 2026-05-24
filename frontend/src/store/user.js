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

    try {
      await fetchUser()
    } catch (error) {
      // fetchUser 失败时回滚 token，避免 isLoggedIn=true 但 user=null 的不一致状态
      token.value = ''
      user.value = null
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('user')
      throw error
    }
  }

  async function register(data) {
    await registerApi(data)
  }

  async function fetchUser() {
    const maxRetries = 2
    for (let i = 0; i <= maxRetries; i++) {
      try {
        const res = await getMe()
        user.value = res
        sessionStorage.setItem('user', JSON.stringify(res))
        return
      } catch (error) {
        if (i < maxRetries && error.response?.status === 401) {
          // 登录后后端 token 可能尚未就绪，短暂等待后重试
          await new Promise(resolve => setTimeout(resolve, 200))
          continue
        }
        console.error('获取用户信息失败:', error)
        throw error
      }
    }
  }

  function logout(router) {
    token.value = ''
    user.value = null
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('user')
    if (router) {
      router.push('/login')
    }
  }

  return { token, user, isLoggedIn, userRole, isAdmin, isLandlord, isTenant, login, register, fetchUser, logout }
})
