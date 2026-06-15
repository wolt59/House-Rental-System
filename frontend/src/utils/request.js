import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'
import { useUserStore } from '../store/user'

const request = axios.create({
  baseURL: '',
  timeout: 15000,
})

request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    const token = userStore.token || sessionStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.config?.url?.includes('/api/v1/auth/login')) {
      return Promise.reject(error)
    }
    if (error.response?.status === 401) {
      if (error.config?.url?.includes('/api/v1/auth/login')) {
        // login endpoint returns 401 for wrong credentials — let the caller handle it
      } else {
        const userStore = useUserStore()
        userStore.logout(router)
        ElMessage.error('登录已过期，请重新登录')
      }
    }
    // 不在此处统一弹错误提示——业务层已包含各自的 ElMessage.error 处理，
    // 全局拦截重复弹窗在业务有 fallback 时会产生误导。
    return Promise.reject(error)
  }
)

export default request
