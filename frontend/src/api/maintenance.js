import request from '../utils/request'

export function getMaintenances(params) {
  return request.get('/api/v1/maintenance/', { params })
}

export function getMaintenance(id) {
  return request.get(`/api/v1/maintenance/${id}`)
}

export function createMaintenance(data) {
  return request.post('/api/v1/maintenance/', data)
}

export function updateMaintenance(id, data) {
  return request.put(`/api/v1/maintenance/${id}`, data)
}
