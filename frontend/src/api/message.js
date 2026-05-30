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

export function getConversations() {
  return request.get('/api/v1/messages/conversations')
}

export function getUnreadCount(type) {
  const params = type ? { type } : {}
  return request.get('/api/v1/messages/unread-count', { params })
}

export function getConversationMessages(peerUserId, params) {
  return request.get(`/api/v1/messages/conversations/${peerUserId}`, { params })
}

export function markConversationRead(peerUserId) {
  return request.put(`/api/v1/messages/conversations/${peerUserId}/read`)
}

export function searchUsers(keyword, limit = 20) {
  return request.get('/api/v1/messages/users/search', { params: { keyword, limit } })
}

export function createWebSocket(token) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/ws?token=${encodeURIComponent(token)}`
  return new WebSocket(wsUrl)
}