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
