import request from '../utils/request'

export function getComplaints(params) {
  return request.get('/api/v1/complaints/', { params })
}

export function getComplaint(id) {
  return request.get(`/api/v1/complaints/${id}`)
}

export function createComplaint(data) {
  return request.post('/api/v1/complaints/', data)
}

export function updateComplaint(id, data) {
  return request.put(`/api/v1/complaints/${id}`, data)
}
