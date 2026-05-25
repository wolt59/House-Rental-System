import request from '../utils/request'

export function getContracts(params) {
  return request.get('/api/v1/contracts/', { params })
}

export function getContract(id) {
  return request.get(`/api/v1/contracts/${id}`)
}

export function createContract(data) {
  return request.post('/api/v1/contracts/', data)
}

export function autoCreateContract(data) {
  return request.post('/api/v1/contracts/auto-create', data)
}

export function updateContract(id, data) {
  return request.put(`/api/v1/contracts/${id}`, data)
}

export function signContractLandlord(id) {
  return request.put(`/api/v1/contracts/${id}/sign/landlord`)
}

export function signContractTenant(id) {
  return request.put(`/api/v1/contracts/${id}/sign/tenant`)
}

export function withdrawSignatureLandlord(id) {
  return request.put(`/api/v1/contracts/${id}/withdraw/landlord`)
}

export function withdrawSignatureTenant(id) {
  return request.put(`/api/v1/contracts/${id}/withdraw/tenant`)
}

export function cancelContract(id) {
  return request.put(`/api/v1/contracts/${id}/cancel`)
}

export function rejectContract(id, data) {
  return request.put(`/api/v1/contracts/${id}/reject`, data)
}

export function terminateContract(id, data) {
  return request.put(`/api/v1/contracts/${id}/terminate`, data)
}
