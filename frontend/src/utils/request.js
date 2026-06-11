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
    } else {
      const msg = extractErrorMessage(error) || '请求失败'
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

function extractErrorMessage(error) {
  const data = error.response?.data
  if (!data) {
    return error.message === 'Network Error' ? '网络连接失败，请检查服务器' : error.message
  }
  // FastAPI HTTPException: { detail: "string" }
  if (typeof data.detail === 'string' && data.detail) return data.detail
  // FastAPI RequestValidationError: { detail: [{ loc, msg, type }, ...] }
  if (Array.isArray(data.detail) && data.detail.length) {
    const first = data.detail[0]
    let msg = first?.msg || ''
    // 去掉 Pydantic 给 ValueError 自动加的 "Value error, " 前缀
    msg = msg.replace(/^Value error,\s*/i, '')
    const field = Array.isArray(first?.loc) ? first.loc.filter((p) => p !== 'body').join('.') : ''
    return field ? `${field}: ${msg}` : msg
  }
  return null
}

export default request
