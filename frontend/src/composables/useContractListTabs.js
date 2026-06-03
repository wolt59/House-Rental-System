import { computed } from 'vue'

export const CONTRACT_STATUS_LABELS = {
  draft: '草稿',
  pending_sign: '待签约',
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
  part_signed: 'warning',
  active: 'success',
  change_negotiating: 'warning',
  terminate_negotiating: 'warning',
  terminated: 'danger',
  cancelled: 'info',
  rejected: 'danger',
  expired: 'info',
}

/** Tab 定义：name 为 el-tab-pane 的 name，filter 用于客户端筛选 */
export const CONTRACT_TABS = [
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
  pending_sign: (c) => c.status === 'pending_sign' || c.status === 'part_signed',
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

export function useContractListTabs(contractsRef) {
  const tabCounts = computed(() => {
    const list = contractsRef.value || []
    const counts = {}
    for (const tab of CONTRACT_TABS) {
      const filter = TAB_FILTERS[tab.name]
      counts[tab.name] = filter ? list.filter(filter).length : 0
    }
    return counts
  })

  function contractsForTab(tabName) {
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
      showLeasePeriod: ['all', 'active', 'ended'].includes(tab),
      showExpiringEndDate: tab === 'expiring',
      showDaysRemaining: tab === 'expiring',
      showStatus: ['all', 'ended'].includes(tab),
      showSignColumns: tab === 'pending_sign',
      operationWidth: simpleActions ? 108 : undefined,
      operationMinWidth: simpleActions
        ? undefined
        : {
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
