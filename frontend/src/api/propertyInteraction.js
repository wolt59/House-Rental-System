import request from '../utils/request'

// 房源交互摘要（收藏数、评论数、当前用户是否收藏）
export function getPropertySummary(propertyId) {
  return request.get(`/api/v1/property-interactions/properties/${propertyId}/summary`)
}

// 切换收藏
export function toggleFavorite(propertyId) {
  return request.post(`/api/v1/property-interactions/favorites/toggle`, null, {
    params: { property_id: propertyId },
  })
}

// 我的收藏列表
export function getMyFavorites(params) {
  return request.get(`/api/v1/property-interactions/favorites/me`, { params })
}

// 评论列表
export function getPropertyComments(propertyId, params) {
  return request.get(`/api/v1/property-interactions/properties/${propertyId}/comments`, { params })
}

// 发布评论
export function createPropertyComment(data) {
  return request.post(`/api/v1/property-interactions/comments`, data)
}

// 修改评论（仅作者本人或管理员）
export function updatePropertyComment(commentId, data) {
  return request.put(`/api/v1/property-interactions/comments/${commentId}`, data)
}

// 删除评论（仅作者本人或管理员）
export function deletePropertyComment(commentId) {
  return request.delete(`/api/v1/property-interactions/comments/${commentId}`)
}
