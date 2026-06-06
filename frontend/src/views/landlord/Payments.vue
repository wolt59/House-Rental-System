<template>
  <div class="page-container">
    <div class="page-header">
      <h2>收款管理</h2>
      <el-button type="primary" @click="loadData" :loading="loading">刷新</el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card submitted">
        <div class="stat-value">{{ pendingCount }}</div>
        <div class="stat-label">待确认收款</div>
      </div>
      <div class="stat-card overdue">
        <div class="stat-value">¥{{ stats.total_overdue }}</div>
        <div class="stat-label">逾期金额</div>
      </div>
      <div class="stat-card confirmed">
        <div class="stat-value">¥{{ stats.total_confirmed }}</div>
        <div class="stat-label">已确认收款</div>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-select
        v-model="filters.property_id"
        placeholder="按房源筛选"
        clearable
        filterable
        style="width: 200px"
        @change="loadData"
      >
        <el-option v-for="p in myProperties" :key="p.id" :label="p.title" :value="p.id" />
      </el-select>
      <el-input
        v-model="filters.property_title"
        placeholder="搜索房源标题关键词..."
        clearable
        style="width: 220px; margin-left: 10px"
        @input="onTitleSearch"
      />
      <el-select v-model="filters.status" placeholder="状态筛选" clearable style="width: 140px; margin-left: 10px" @change="loadData">
        <el-option v-for="(v, k) in statusMap" :key="k" :label="v" :value="k" />
      </el-select>
      <el-select v-model="filters.bill_type" placeholder="类型筛选" clearable style="width: 140px; margin-left: 10px" @change="loadData">
        <el-option v-for="(v, k) in billTypeMap" :key="k" :label="v" :value="k" />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="截止日期起"
        end-placeholder="截止日期止"
        format="YYYY/MM/DD"
        value-format="YYYY-MM-DD"
        style="margin-left: 10px; width: 260px"
        @change="onDateRangeChange"
        :clearable="true"
      />
    </div>

    <el-table :data="payments" stripe v-loading="loading">
      <el-table-column prop="bill_no" label="账单编号" min-width="180" show-overflow-tooltip />
      <el-table-column label="租客" min-width="90" show-overflow-tooltip>
        <template #default="{ row }">{{ row.tenant_name || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="房源" min-width="130" show-overflow-tooltip>
        <template #default="{ row }">{{ row.property_title || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="类型" width="80" align="center">
        <template #default="{ row }">{{ billTypeMap[row.bill_type] || row.bill_type }}</template>
      </el-table-column>
      <el-table-column label="周期" width="90" align="center">
        <template #default="{ row }">{{ row.period || '-' }}</template>
      </el-table-column>
      <el-table-column label="应收" width="100" align="right">
        <template #default="{ row }">¥{{ row.due_amount }}</template>
      </el-table-column>
      <el-table-column label="实付" width="100" align="right">
        <template #default="{ row }">{{ row.actual_amount ? '¥' + row.actual_amount : '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusMap[row.status] || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="截止日期" min-width="110">
        <template #default="{ row }">{{ formatDate(row.due_date) }}</template>
      </el-table-column>
      <el-table-column label="逾期" width="70" align="center">
        <template #default="{ row }">
          <span v-if="row.status === 'overdue'" style="color: red; font-weight: bold">{{ row.overdue_days }}天</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="200" align="center" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'submitted'" type="success" size="small" @click="handleConfirm(row)">
            确认收款
          </el-button>
          <el-button v-if="row.status === 'submitted'" type="danger" size="small" @click="openRejectDialog(row)">
            驳回
          </el-button>
          <el-button
            v-if="row.status === 'pending' || row.status === 'overdue'"
            type="warning"
            size="small"
            :loading="remindingId === row.id"
            @click="handleRemind(row)"
          >
            提醒付款
          </el-button>
          <el-button type="info" size="small" plain @click="openDetailDialog(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && payments.length === 0" description="暂无收款记录" />
    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <!-- 驳回对话框 -->
    <el-dialog v-model="showRejectDialog" title="驳回付款" width="460px">
      <el-form :model="rejectForm" label-width="80px">
        <el-form-item label="账单编号">
          <span>{{ currentBill?.bill_no || '-' }}</span>
        </el-form-item>
        <el-form-item label="驳回原因" required>
          <el-input v-model="rejectForm.reason" type="textarea" :rows="3" placeholder="请输入驳回原因，例如：付款金额不足" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="showRejectDialog = false">取消</el-button>
        <el-button type="danger" size="small" :loading="rejecting" @click="handleReject" :disabled="!rejectForm.reason.trim()">确认驳回</el-button>
      </template>
    </el-dialog>

    <!-- 账单详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="账单详情" width="560px">
      <el-descriptions :column="2" border v-if="currentBill">
        <el-descriptions-item label="账单编号">{{ currentBill.bill_no }}</el-descriptions-item>
        <el-descriptions-item label="合同编号">{{ currentBill.contract_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="租客">{{ currentBill.tenant_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房源">{{ currentBill.property_title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="账单类型">{{ billTypeMap[currentBill.bill_type] || currentBill.bill_type }}</el-descriptions-item>
        <el-descriptions-item label="所属周期">{{ currentBill.period || '-' }}</el-descriptions-item>
        <el-descriptions-item label="应收金额">
          <span style="color: #409eff; font-weight: bold">¥{{ currentBill.due_amount }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="实付金额">
          {{ currentBill.actual_amount ? '¥' + currentBill.actual_amount : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="支付方式">{{ methodMap[currentBill.payment_method] || currentBill.payment_method || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(currentBill.status)" size="small">{{ statusMap[currentBill.status] || currentBill.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="付款截止日">{{ formatDate(currentBill.due_date) }}</el-descriptions-item>
        <el-descriptions-item label="付款时间">{{ formatDateTime(currentBill.payment_time) }}</el-descriptions-item>
        <el-descriptions-item label="确认时间">{{ formatDateTime(currentBill.confirmed_at) }}</el-descriptions-item>
        <el-descriptions-item label="逾期天数">{{ currentBill.overdue_days || 0 }}天</el-descriptions-item>
        <el-descriptions-item label="转账备注" :span="2">{{ currentBill.transaction_note || '-' }}</el-descriptions-item>
        <el-descriptions-item label="驳回原因" :span="2" v-if="currentBill.rejected_reason">
          <span style="color: red">{{ currentBill.rejected_reason }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="付款凭证" :span="2" v-if="currentBill.payment_proof">
          <el-link :href="currentBill.payment_proof" target="_blank" type="primary">
            <el-button type="primary" size="small">查看付款凭证截图</el-button>
          </el-link>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(currentBill.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ currentBill.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getPayments, getPaymentStats, confirmPayment, rejectPayment, remindPayment } from '../../api/payment'
import { getMyProperties } from '../../api/property'
import { ElMessage, ElMessageBox } from 'element-plus'

const payments = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const myProperties = ref([])

const stats = reactive({ total_pending: 0, total_overdue: 0, total_confirmed: 0 })

// 默认日期范围：本月第一天 ～ 下月最后一天
function getDefaultDateRange() {
  const now = new Date()
  const from = new Date(now.getFullYear(), now.getMonth(), 1)
  const to = new Date(now.getFullYear(), now.getMonth() + 2, 0)
  const fmt = d => d.toISOString().split('T')[0]
  return { from: fmt(from), to: fmt(to) }
}

const defaultRange = getDefaultDateRange()
const dateRange = ref([defaultRange.from, defaultRange.to])

const filters = reactive({
  property_id: '',
  property_title: '',
  status: '',
  bill_type: '',
  due_date_from: defaultRange.from + 'T00:00:00',
  due_date_to: defaultRange.to + 'T23:59:59',
})

const pendingCount = computed(() => payments.value.filter(p => p.status === 'submitted').length)

const showRejectDialog = ref(false)
const showDetailDialog = ref(false)
const currentBill = ref(null)
const rejecting = ref(false)
const remindingId = ref(null)
const rejectForm = reactive({ reason: '' })

const statusMap = {
  pending: '待支付', submitted: '已提交付款', confirmed: '已确认收款',
  rejected: '已驳回', overdue: '已逾期', cancelled: '已取消',
}
const statusTypeMap = {
  pending: 'warning', submitted: 'info', confirmed: 'success',
  rejected: 'danger', overdue: 'danger', cancelled: 'info',
}
const billTypeMap = {
  rent: '租金', deposit: '押金', utility: '水电费', maintenance: '维修费', other: '其他',
}
const methodMap = { alipay: '支付宝', wechat: '微信', bank: '银行卡转账', cash: '现金' }

function statusType(s) { return statusTypeMap[s] || 'info' }
function formatDate(d) { return d ? new Date(d).toLocaleDateString('zh-CN') : '-' }
function formatDateTime(d) { return d ? new Date(d).toLocaleString('zh-CN') : '-' }

function onDateRangeChange(val) {
  if (val && val.length === 2) {
    filters.due_date_from = val[0] + 'T00:00:00'
    filters.due_date_to = val[1] + 'T23:59:59'
  } else {
    filters.due_date_from = ''
    filters.due_date_to = ''
  }
  loadData()
}

let titleTimer = null
function onTitleSearch() {
  if (titleTimer) clearTimeout(titleTimer)
  titleTimer = setTimeout(() => loadData(), 300)
}

async function loadData() {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    if (filters.property_id) params.property_id = filters.property_id
    if (filters.property_title) params.property_title = filters.property_title
    if (filters.status) params.status = filters.status
    if (filters.bill_type) params.bill_type = filters.bill_type
    if (filters.due_date_from) params.due_date_from = filters.due_date_from
    if (filters.due_date_to) params.due_date_to = filters.due_date_to

    const [res, statsRes] = await Promise.all([
      getPayments(params),
      getPaymentStats().catch(() => null),
    ])
    payments.value = res.items || []
    total.value = res.total || 0
    if (statsRes) {
      stats.total_pending = statsRes.total_pending || 0
      stats.total_overdue = statsRes.total_overdue || 0
      stats.total_confirmed = statsRes.total_confirmed || 0
    }
  } catch (e) {
    ElMessage.error('加载收款列表失败')
  } finally {
    loading.value = false
  }
}

async function loadProperties() {
  try {
    const res = await getMyProperties({ skip: 0, limit: 200 })
    myProperties.value = Array.isArray(res) ? res : []
  } catch (e) {
    console.error('加载房源列表失败', e)
  }
}

async function handleConfirm(row) {
  try {
    await ElMessageBox.confirm(
      `确认已经收到租客支付的 ¥${row.actual_amount || row.due_amount}？`,
      '确认收款',
      { confirmButtonText: '确认收款', cancelButtonText: '取消', type: 'success' }
    )
    await confirmPayment(row.id)
    ElMessage.success('已确认收款')
    loadData()
  } catch (e) {
    if (e !== 'cancel' && e?.response) {
      ElMessage.error(e.response.data?.detail || '操作失败')
    }
  }
}

async function handleRemind(row) {
  if (remindingId.value) return
  try {
    await ElMessageBox.confirm(
      `确认向租客发送付款提醒？\n\n账单：${row.bill_no}\n金额：¥${row.due_amount}\n房源：${row.property_title || '-'}`,
      '提醒付款',
      { confirmButtonText: '发送提醒', cancelButtonText: '取消', type: 'warning' }
    )
    remindingId.value = row.id
    await remindPayment(row.id)
    ElMessage.success('提醒已发送')
  } catch (e) {
    if (e === 'cancel') return
    ElMessage.error(e?.response?.data?.detail || '发送失败')
  } finally {
    remindingId.value = null
  }
}

function openRejectDialog(row) {
  currentBill.value = row
  rejectForm.reason = ''
  showRejectDialog.value = true
}

async function handleReject() {
  if (!rejectForm.reason.trim()) return
  rejecting.value = true
  try {
    await rejectPayment(currentBill.value.id, { rejected_reason: rejectForm.reason })
    ElMessage.success('已驳回付款')
    showRejectDialog.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '驳回失败')
  } finally {
    rejecting.value = false
  }
}

function openDetailDialog(row) {
  currentBill.value = row
  showDetailDialog.value = true
}

onMounted(() => {
  loadProperties()
  loadData()
})
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
.stats-row { display: flex; gap: 16px; margin-bottom: 16px; }
.stat-card {
  flex: 1; padding: 16px 20px; border-radius: 8px; color: #fff; text-align: center;
}
.stat-card.submitted { background: linear-gradient(135deg, #409eff, #66b1ff); }
.stat-card.overdue { background: linear-gradient(135deg, #f56c6c, #e74c3c); }
.stat-card.confirmed { background: linear-gradient(135deg, #67c23a, #27ae60); }
.stat-value { font-size: 24px; font-weight: bold; }
.stat-label { font-size: 13px; opacity: 0.9; margin-top: 4px; }
.filter-bar { margin-bottom: 12px; display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }

:deep(.el-table) { width: 100% !important; }
:deep(.el-table__inner-wrapper) { width: 100% !important; }
</style>
