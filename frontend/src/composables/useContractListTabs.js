import { computed } from 'vue'

export const CONTRACT_STATUS_LABELS = {
  draft: '草稿',
  pending_sign: '待签约',
  pending_landlord_sign: '待房东签署',
  pending_tenant_sign: '待租客签署',
  part_signed: '部分签署',
  active: '生效中',
  change_negotiating: '变更协商中',
  terminate_negotiating: '解约协商中',
  terminated: '已终止',
  cancelled: '已取消',
  rejected: '已拒绝',
  expired: '已过期',
}

export const CONTRACT_STATUS_TYPES = {
  draft: 'info',
  pending_sign: 'warning',
  pending_landlord_sign: 'warning',
  pending_tenant_sign: 'warning',
  part_signed: 'warning',
  active: 'success',
  change_negotiating: 'warning',
  terminate_negotiating: 'warning',
  terminated: 'danger',
  cancelled: 'info',
  rejected: 'danger',
  expired: 'info',
}

export const APPLICATION_STATUS_LABELS = {
  apply_pending: '待房东确认',
  apply_approved: '已同意',
  apply_rejected: '已拒绝',
  apply_cancelled: '已取消',
}

export const APPLICATION_STATUS_TYPES = {
  apply_pending: 'warning',
  apply_approved: 'success',
  apply_rejected: 'danger',
  apply_cancelled: 'info',
}

export function appStatusLabel(s) {
  return APPLICATION_STATUS_LABELS[s] || s
}

export function appStatusType(s) {
  return APPLICATION_STATUS_TYPES[s] || 'info'
}

/** Tab 定义：name 为 el-tab-pane 的 name，filter 用于客户端筛选 */
export const CONTRACT_TABS = [
  { name: 'applications', label: '合约申请' },
  { name: 'all', label: '全部合同' },
  { name: 'draft', label: '草稿' },
  { name: 'pending_sign', label: '待签署' },
  { name: 'active', label: '生效中' },
  { name: 'expiring', label: '即将到期' },
  { name: 'ended', label: '已结束' },
  { name: 'change_negotiating', label: '变更协商中' },
  { name: 'terminate_negotiating', label: '解约协商中' },
]

function isActiveNotExpired(c) {
  if (c.status !== 'active') return false
  const endDate = new Date(c.end_date)
  return endDate >= new Date()
}

function isExpiringSoon(c) {
  if (c.status !== 'active') return false
  const now = new Date()
  const endDate = new Date(c.end_date)
  const thirtyDaysLater = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000)
  return endDate > now && endDate <= thirtyDaysLater
}

function isEnded(c) {
  if (['expired', 'terminated', 'cancelled', 'rejected'].includes(c.status)) return true
  if (c.status === 'active') {
    return new Date(c.end_date) < new Date()
  }
  return false
}

const TAB_FILTERS = {
  all: () => true,
  draft: (c) => c.status === 'draft',
  pending_sign: (c) => c.status === 'pending_sign' || c.status === 'pending_landlord_sign' || c.status === 'pending_tenant_sign' || c.status === 'part_signed',
  active: isActiveNotExpired,
  expiring: isExpiringSoon,
  ended: isEnded,
  change_negotiating: (c) => c.status === 'change_negotiating',
  terminate_negotiating: (c) => c.status === 'terminate_negotiating',
}

export function statusLabel(s) {
  return CONTRACT_STATUS_LABELS[s] || s
}

export function statusType(s) {
  return CONTRACT_STATUS_TYPES[s] || 'info'
}

export function getDaysRemaining(row) {
  if (!row.end_date) return 0
  const diffDays = Math.ceil((new Date(row.end_date) - new Date()) / (1000 * 60 * 60 * 24))
  return diffDays > 0 ? diffDays : 0
}

export function getDaysRemainingType(row) {
  const days = getDaysRemaining(row)
  if (days <= 7) return 'danger'
  if (days <= 15) return 'warning'
  return 'success'
}

export function useContractListTabs(contractsRef, applicationsRef) {
  const tabCounts = computed(() => {
    const list = contractsRef.value || []
    const apps = applicationsRef?.value || []
    const counts = {}
    for (const tab of CONTRACT_TABS) {
      if (tab.name === 'applications') {
        counts.applications = apps.length
      } else {
        const filter = TAB_FILTERS[tab.name]
        counts[tab.name] = filter ? list.filter(filter).length : 0
      }
    }
    return counts
  })

  function contractsForTab(tabName) {
    if (tabName === 'applications') {
      return applicationsRef?.value || []
    }
    const list = contractsRef.value || []
    const filter = TAB_FILTERS[tabName]
    return filter ? list.filter(filter) : list
  }

  return { tabCounts, contractsForTab }
}

/** 各 Tab 下表格列显示与宽度配置 */
export function useContractTableColumns(activeTabRef) {
  return computed(() => {
    const tab = activeTabRef.value
    const simpleActions = tab === 'expiring' || tab === 'ended'

    return {
      showLeasePeriod: ['all', 'active', 'ended', 'applications'].includes(tab),
      showExpiringEndDate: tab === 'expiring',
      showDaysRemaining: tab === 'expiring',
      showStatus: ['all', 'ended', 'applications'].includes(tab),
      showSignColumns: tab === 'pending_sign',
      isApplication: tab === 'applications',
      operationWidth: simpleActions ? 108 : undefined,
      operationMinWidth: simpleActions
        ? undefined
        : {
            applications: 200,
            draft: 280,
            pending_sign: 320,
            active: 200,
            terminate_negotiating: 280,
            change_negotiating: 160,
            all: 280,
          }[tab] ?? 240,
    }
  })
}
