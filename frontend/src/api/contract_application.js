import request from '../utils/request'

export function getApplications(params) {
  return request.get('/api/v1/contract-applications/', { params })
}

export function getApplication(id) {
  return request.get(`/api/v1/contract-applications/${id}`)
}

export function approveApplication(id, data) {
  return request.post(`/api/v1/contract-applications/${id}/approve`, data)
}

export function rejectApplication(id, data) {
  return request.post(`/api/v1/contract-applications/${id}/reject`, data)
}

export function cancelApplication(id) {
  return request.put(`/api/v1/contract-applications/${id}/cancel`)
}
