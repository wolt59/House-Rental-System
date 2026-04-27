import request from '../utils/request'

export function getPayments(params) {
  return request.get('/api/v1/payments/', { params })
}

export function getPayment(id) {
  return request.get(`/api/v1/payments/${id}`)
}

export function createPayment(data) {
  return request.post('/api/v1/payments/', data)
}

export function updatePayment(id, data) {
  return request.put(`/api/v1/payments/${id}`, data)
}
