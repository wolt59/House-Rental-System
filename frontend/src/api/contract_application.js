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

export function rejectApplication(id, reason) {
  return request.post(`/api/v1/contract-applications/${id}/reject`, null, { params: { reason } })
}

export function cancelApplication(id) {
  return request.put(`/api/v1/contract-applications/${id}/cancel`)
}
