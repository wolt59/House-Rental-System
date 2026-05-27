import request from '../utils/request'

export function getBookings(params) {
  return request.get('/api/v1/bookings/', { params })
}

export function getBooking(id) {
  return request.get(`/api/v1/bookings/${id}`)
}

export function createBooking(data) {
  return request.post('/api/v1/bookings/', data)
}

export function updateBooking(id, data) {
  return request.put(`/api/v1/bookings/${id}`, data)
}

export function deleteBooking(id) {
  return request.delete(`/api/v1/bookings/${id}`)
}

export function approveBooking(id) {
  return request.post(`/api/v1/bookings/${id}/approve`)
}

export function rejectBooking(id, reason) {
  return request.post(`/api/v1/bookings/${id}/reject`, null, { params: { reason } })
}

export function rescheduleBooking(id, data) {
  return request.post(`/api/v1/bookings/${id}/reschedule`, data)
}

export function respondReschedule(id, data) {
  return request.post(`/api/v1/bookings/${id}/reschedule-response`, data)
}

export function completeBooking(id) {
  return request.post(`/api/v1/bookings/${id}/complete`)
}

export function showContactInfo(id) {
  return request.post(`/api/v1/bookings/${id}/show-contact`)
}
