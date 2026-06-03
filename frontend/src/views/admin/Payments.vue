<template>
  <div class="page-container">
    <div class="page-header">
      <h2>账单管理</h2>
      <div class="header-actions">
        <el-button type="warning" @click="handleCheckOverdue" :loading="checkingOverdue">检查逾期</el-button>
        <el-button type="primary" @click="handleGenerateBills" :loading="generatingBills">生成下月账单</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-input v-model="filters.search" placeholder="搜索账单编号/合同编号" clearable style="width: 200px" @change="loadData" />
      <el-select v-model="filters.status" placeholder="状态筛选" clearable style="width: 140px; margin-left: 10px" @change="loadData">
        <el-option v-for="(v, k) in statusMap" :key="k" :label="v" :value="k" />
      </el-select>
      <el-select v-model="filters.bill_type" placeholder="类型筛选" clearable style="width: 140px; margin-left: 10px" @change="loadData">
        <el-option v-for="(v, k) in billTypeMap" :key="k" :label="v" :value="k" />
      </el-select>
      <el-button @click="loadData" style="margin-left: 10px">查询</el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card total">
        <div class="stat-value">{{ totalBills }}</div>
        <div class="stat-label">总账单数</div>
      </div>
      <div class="stat-card pending">
        <div class="stat-value">¥{{ stats.total_pending }}</div>
        <div class="stat-label">待支付金额</div>
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

    <el-table :data="payments" stripe v-loading="loading">
      <el-table-column prop="bill_no" label="账单编号" min-width="180" show-overflow-tooltip />
      <el-table-column label="租客" min-width="90" show-overflow-tooltip>
        <template #default="{ row }">{{ row.tenant_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="房东" min-width="90" show-overflow-tooltip>
        <template #default="{ row }">{{ row.landlord_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="房源" min-width="130" show-overflow-tooltip>
        <template #default="{ row }">{{ row.property_title || '-' }}</template>
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
          <span v-if="row.status === 'overdue'" style="color: red">{{ row.overdue_days }}天</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" align="center" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDetailDialog(row)">详情</el-button>
          <el-button v-if="row.status === 'pending'" size="small" type="danger" @click="handleCancelBill(row)">取消</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && payments.length === 0" description="暂无账单" />
    <div class="pagination-wrap" v-if="totalBills >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="totalBills" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <!-- 账单详情 -->
    <el-dialog v-model="showDetailDialog" title="账单详情" width="560px">
      <el-descriptions :column="2" border v-if="currentBill">
        <el-descriptions-item label="账单编号">{{ currentBill.bill_no }}</el-descriptions-item>
        <el-descriptions-item label="合同编号">{{ currentBill.contract_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="租客">{{ currentBill.tenant_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房东">{{ currentBill.landlord_name || '-' }}</el-descriptions-item>
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
          <el-link :href="currentBill.payment_proof" target="_blank" type="primary">查看凭证</el-link>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(currentBill.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDateTime(currentBill.updated_at) }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ currentBill.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getPayments, getPaymentStats, updatePayment, triggerOverdueCheck, triggerNextMonthBills } from '../../api/payment'
import { ElMessage, ElMessageBox } from 'element-plus'

const payments = ref([])
const loading = ref(false)
const totalBills = ref(0)
const pageSize = ref(15)
const currentPage = ref(1)

const stats = reactive({ total_pending: 0, total_overdue: 0, total_confirmed: 0 })
const filters = reactive({ search: '', status: '', bill_type: '' })

const checkingOverdue = ref(false)
const generatingBills = ref(false)

const showDetailDialog = ref(false)
const currentBill = ref(null)

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

async function loadData() {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    if (filters.status) params.status = filters.status
    if (filters.bill_type) params.bill_type = filters.bill_type

    const [res, statsRes] = await Promise.all([
      getPayments(params),
      getPaymentStats().catch(() => null),
    ])
    payments.value = Array.isArray(res) ? res : []
    totalBills.value = Array.isArray(res) ? res.length : 0
    if (statsRes) {
      stats.total_pending = statsRes.total_pending || 0
      stats.total_overdue = statsRes.total_overdue || 0
      stats.total_confirmed = statsRes.total_confirmed || 0
    }
  } catch (e) {
    ElMessage.error('加载账单列表失败')
  } finally {
    loading.value = false
  }
}

function openDetailDialog(row) {
  currentBill.value = row
  showDetailDialog.value = true
}

async function handleCancelBill(row) {
  try {
    await ElMessageBox.confirm(
      `确认取消账单 ${row.bill_no}？`,
      '取消账单',
      { confirmButtonText: '确认取消', cancelButtonText: '返回', type: 'warning' }
    )
    await updatePayment(row.id, { status: 'cancelled' })
    ElMessage.success('账单已取消')
    loadData()
  } catch (e) {
    if (e !== 'cancel' && e?.response) {
      ElMessage.error(e.response.data?.detail || '操作失败')
    }
  }
}

async function handleCheckOverdue() {
  checkingOverdue.value = true
  try {
    const res = await triggerOverdueCheck()
    ElMessage.success(`逾期检查完成，共标记 ${res.overdue_count} 笔逾期账单`)
    loadData()
  } catch (e) {
    ElMessage.error('逾期检查失败')
  } finally {
    checkingOverdue.value = false
  }
}

async function handleGenerateBills() {
  generatingBills.value = true
  try {
    const res = await triggerNextMonthBills()
    ElMessage.success(`下月账单生成完成，共生成 ${res.count} 笔账单`)
    loadData()
  } catch (e) {
    ElMessage.error('生成账单失败')
  } finally {
    generatingBills.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
.stats-row { display: flex; gap: 16px; margin-bottom: 16px; }
.stat-card {
  flex: 1; padding: 16px 20px; border-radius: 8px; color: #fff; text-align: center;
}
.stat-card.total { background: linear-gradient(135deg, #909399, #b0b3b8); }
.stat-card.pending { background: linear-gradient(135deg, #e6a23c, #f0ad4e); }
.stat-card.overdue { background: linear-gradient(135deg, #f56c6c, #e74c3c); }
.stat-card.confirmed { background: linear-gradient(135deg, #67c23a, #27ae60); }
.stat-value { font-size: 24px; font-weight: bold; }
.stat-label { font-size: 13px; opacity: 0.9; margin-top: 4px; }
.filter-bar { margin-bottom: 12px; display: flex; align-items: center; }
.header-actions { display: flex; gap: 8px; }

::deep(.el-table) { width: 100% !important; }
::deep(.el-table__inner-wrapper) { width: 100% !important; }
</style>
