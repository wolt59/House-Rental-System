import request from '../utils/request'

export function login(username, password) {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)
  return request.post('/api/v1/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
}

export function register(data) {
  return request.post('/api/v1/auth/register', data)
}
