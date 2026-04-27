import request from '../utils/request'

export function getRegionStats() {
  return request.get('/api/v1/stats/regions')
}

export function getFloorPlanStats() {
  return request.get('/api/v1/stats/floor-plans')
}

export function getDashboard() {
  return request.get('/api/v1/stats/dashboard')
}

export function getAuditLogs(params) {
  return request.get('/api/v1/admin/audit-logs/', { params })
}

export function getAuditLog(id) {
  return request.get(`/api/v1/admin/audit-logs/${id}`)
}
