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

export function getMonthlyIncome() {
  return request.get('/api/v1/stats/monthly-income')
}

export function getUserActivity() {
  return request.get('/api/v1/stats/user-activity')
}

export function getPropertyStatus() {
  return request.get('/api/v1/stats/property-status')
}

export function getLandlordDashboard() {
  return request.get('/api/v1/stats/landlord-dashboard')
}

export function getLandlordMonthlyIncome() {
  return request.get('/api/v1/stats/landlord-monthly-income')
}

export function getAuditLogs(params) {
  return request.get('/api/v1/admin/audit-logs/', { params })
}

export function getAuditLog(id) {
  return request.get(`/api/v1/admin/audit-logs/${id}`)
}
