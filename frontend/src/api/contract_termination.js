import request from '../utils/request'

// 获取终止申请列表
export function getTerminationRequests(params) {
  return request.get('/api/v1/contract-terminations/', { params })
}

// 获取单个终止申请详情
export function getTerminationRequest(id) {
  return request.get(`/api/v1/contract-terminations/${id}`)
}

// 创建终止申请
export function createTerminationRequest(data) {
  return request.post('/api/v1/contract-terminations/', data)
}

// 同意终止申请
export function approveTerminationRequest(id, data) {
  return request.post(`/api/v1/contract-terminations/${id}/approve`, null, {
    params: { opinion: data.opinion || '' }
  })
}

// 拒绝终止申请
export function rejectTerminationRequest(id, reason) {
  return request.post(`/api/v1/contract-terminations/${id}/reject`, null, {
    params: { reason }
  })
}
