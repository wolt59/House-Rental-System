import request from '../utils/request'

export function getUsers(params) {
  return request.get('/api/v1/users/', { params })
}

export function getUser(userId) {
  return request.get(`/api/v1/users/${userId}`)
}

export function getMe() {
  return request.get('/api/v1/users/me')
}

export function updateMe(data) {
  return request.put('/api/v1/users/me', data)
}

export function changePassword(data) {
  return request.put('/api/v1/users/me/password', data)
}

export function updateUser(userId, data) {
  return request.put(`/api/v1/users/${userId}`, data)
}

export function toggleUserStatus(userId) {
  return request.put(`/api/v1/users/${userId}/status`)
}

export function getLandlordStats(params) {
  return request.get('/api/v1/users/landlord-stats', { params })
}
