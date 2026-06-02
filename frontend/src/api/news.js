import request from '../utils/request'

export function getNewsList(params) {
  return request.get('/api/v1/news/', { params })
}

export function getMyNews(params) {
  return request.get('/api/v1/news/my', { params })
}

export function getNews(id) {
  return request.get(`/api/v1/news/${id}`)
}

export function createNews(data) {
  return request.post('/api/v1/news/', data)
}

export function updateNews(id, data) {
  return request.put(`/api/v1/news/${id}`, data)
}

export function deleteNews(id) {
  return request.delete(`/api/v1/news/${id}`)
}

// 管理员接口
export function getAllNewsAdmin(params) {
  return request.get('/api/v1/news/all', { params })
}

export function reviewNews(id, data) {
  return request.post(`/api/v1/news/${id}/review`, data)
}
