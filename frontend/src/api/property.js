import request from '../utils/request'

export function getProperties(params) {
  return request.get('/api/v1/properties/', { params })
}

export function getMyProperties(params) {
  return request.get('/api/v1/properties/my', { params })
}

export function getOwnerProperties(ownerId, params) {
  return request.get(`/api/v1/properties/owner/${ownerId}`, { params })
}

export function getProperty(id) {
  return request.get(`/api/v1/properties/${id}`)
}

export function createProperty(data) {
  return request.post('/api/v1/properties/', data)
}

export function updateProperty(id, data) {
  return request.put(`/api/v1/properties/${id}`, data)
}

export function deleteProperty(id) {
  return request.delete(`/api/v1/properties/${id}`)
}

export function reviewProperty(id, data) {
  return request.put(`/api/v1/properties/${id}/review`, data)
}

export function changePropertyStatus(id, data) {
  return request.put(`/api/v1/properties/${id}/status`, data)
}

export function getPropertyImages(propertyId) {
  return request.get(`/api/v1/property-images/${propertyId}/images`)
}

export function addPropertyImage(propertyId, data) {
  return request.post(`/api/v1/property-images/${propertyId}/images`, data)
}

export function updatePropertyImage(imageId, data) {
  return request.put(`/api/v1/property-images/images/${imageId}`, data)
}

export function deletePropertyImage(imageId) {
  return request.delete(`/api/v1/property-images/images/${imageId}`)
}

export function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/api/v1/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
