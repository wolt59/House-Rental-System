import request from '../utils/request'

export function getPayments(params) {
  return request.get('/api/v1/payments/', { params })
}

export function getPaymentStats() {
  return request.get('/api/v1/payments/stats')
}

export function getPayment(id) {
  return request.get(`/api/v1/payments/${id}`)
}

export function createPayment(data) {
  return request.post('/api/v1/payments/', data)
}

export function submitPayment(id, data) {
  return request.put(`/api/v1/payments/${id}/submit`, data)
}

export function confirmPayment(id) {
  return request.put(`/api/v1/payments/${id}/confirm`)
}

export function rejectPayment(id, data) {
  return request.put(`/api/v1/payments/${id}/reject`, data)
}

export function updatePayment(id, data) {
  return request.put(`/api/v1/payments/${id}`, data)
}

export function triggerOverdueCheck() {
  return request.post('/api/v1/payments/admin/generate-overdue')
}

export function triggerNextMonthBills() {
  return request.post('/api/v1/payments/admin/generate-next-month')
}
