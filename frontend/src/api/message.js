import request from '../utils/request'

export function getReceivedMessages(params) {
  return request.get('/api/v1/messages/received', { params })
}

export function getSentMessages(params) {
  return request.get('/api/v1/messages/sent', { params })
}

export function sendMessage(data) {
  return request.post('/api/v1/messages/', data)
}

export function markMessageRead(id) {
  return request.put(`/api/v1/messages/${id}/read`)
}
