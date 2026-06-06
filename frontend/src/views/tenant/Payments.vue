<template>
  <div class="page-container">
    <div class="page-header">
      <h2>我的账单</h2>
      <el-button type="primary" @click="loadData" :loading="loading">刷新</el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card pending">
        <div class="stat-value">¥{{ stats.total_pending }}</div>
        <div class="stat-label">待支付</div>
      </div>
      <div class="stat-card overdue">
        <div class="stat-value">¥{{ stats.total_overdue }}</div>
        <div class="stat-label">已逾期</div>
      </div>
      <div class="stat-card confirmed">
        <div class="stat-value">¥{{ stats.total_confirmed }}</div>
        <div class="stat-label">已确认收款</div>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-select v-model="filters.status" placeholder="状态筛选" clearable style="width: 140px" @change="loadData">
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
      <el-table-column label="房源" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.property_title || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="类型" width="80" align="center">
        <template #default="{ row }">{{ billTypeMap[row.bill_type] || row.bill_type }}</template>
      </el-table-column>
      <el-table-column label="周期" width="100" align="center">
        <template #default="{ row }">{{ row.period || '-' }}</template>
      </el-table-column>
      <el-table-column label="应收金额" width="110" align="right">
        <template #default="{ row }">¥{{ row.due_amount }}</template>
      </el-table-column>
      <el-table-column label="实付金额" width="110" align="right">
        <template #default="{ row }">{{ row.actual_amount ? '¥' + row.actual_amount : '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusMap[row.status] || row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="截止日期" min-width="115">
        <template #default="{ row }">{{ formatDate(row.due_date) }}</template>
      </el-table-column>
      <el-table-column label="逾期" width="70" align="center">
        <template #default="{ row }">
          <span v-if="row.status === 'overdue'" style="color: red">{{ row.overdue_days }}天</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="180" align="center" fixed="right">
        <template #default="{ row }">
          <el-button v-if="['pending', 'overdue', 'rejected'].includes(row.status)" type="primary" size="small" @click="openSubmitDialog(row)">
            去支付
          </el-button>
          <el-button v-if="row.status === 'rejected' && row.rejected_reason" type="warning" size="small" @click="showRejectReason(row)">
            查看驳回原因
          </el-button>
          <el-button type="info" size="small" plain @click="openDetailDialog(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && payments.length === 0" description="暂无账单" />
    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <!-- 提交付款对话框 -->
    <el-dialog v-model="showSubmitDialog" title="提交付款凭证" width="540px">
      <el-form ref="submitFormRef" :model="submitForm" label-width="100px" :rules="submitRules">
        <el-form-item label="账单编号">
          <span>{{ currentBill?.bill_no || '-' }}</span>
        </el-form-item>
        <el-form-item label="应收金额">
          <span style="font-weight: bold; font-size: 18px; color: #409eff">
            ¥{{ currentBill?.due_amount || 0 }}
          </span>
        </el-form-item>
        <el-form-item label="实付金额" prop="actual_amount">
          <el-input v-model.number="submitForm.actual_amount" type="number" placeholder="请输入实际支付金额" />
        </el-form-item>
        <el-form-item label="支付方式" prop="payment_method">
          <el-select v-model="submitForm.payment_method" placeholder="选择支付方式" style="width: 100%">
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信" value="wechat" />
            <el-option label="银行卡转账" value="bank" />
            <el-option label="现金" value="cash" />
          </el-select>
        </el-form-item>
        <el-form-item label="支付时间" prop="payment_time">
          <el-date-picker v-model="submitForm.payment_time" type="datetime" placeholder="选择支付时间" style="width: 100%" />
        </el-form-item>
        <el-form-item label="转账备注">
          <el-input v-model="submitForm.transaction_note" type="textarea" :rows="3" placeholder="选填，转账备注信息" />
        </el-form-item>
        <el-form-item label="付款凭证">
          <el-upload
            class="payment-upload"
            :action="uploadUrl"
            :headers="uploadHeaders"
            :limit="1"
            :on-success="onUploadSuccess"
            :on-remove="onUploadRemove"
            :before-upload="beforeUpload"
            :file-list="uploadFileList"
            list-type="picture-card"
            accept="image/*"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div v-if="submitForm.payment_proof" class="uploaded-url">
            <span class="upload-label">已上传凭证：</span>
            <el-link :href="submitForm.payment_proof" target="_blank" type="success" :underline="false">
              <el-icon><PictureFilled /></el-icon> 查看
            </el-link>
          </div>
          <div class="form-tip">支持上传支付宝/微信/银行转账截图，图片大小不超过 10MB</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="showSubmitDialog = false">取消</el-button>
        <el-button type="primary" size="small" :loading="submitting" @click="handleSubmitPayment">确认提交</el-button>
      </template>
    </el-dialog>

    <!-- 账单详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="账单详情" width="560px">
      <el-descriptions :column="2" border v-if="currentBill">
        <el-descriptions-item label="账单编号">{{ currentBill.bill_no }}</el-descriptions-item>
        <el-descriptions-item label="合同编号">{{ currentBill.contract_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房源">{{ currentBill.property_title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房东">{{ currentBill.landlord_name || '-' }}</el-descriptions-item>
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
        <el-descriptions-item label="备注">{{ currentBill.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getPayments, getPaymentStats, submitPayment } from '../../api/payment'
import { ElMessage } from 'element-plus'
import { Plus, PictureFilled } from '@element-plus/icons-vue'

const payments = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)

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
  status: '',
  bill_type: '',
  due_date_from: defaultRange.from + 'T00:00:00',
  due_date_to: defaultRange.to + 'T23:59:59',
})

const showSubmitDialog = ref(false)
const showDetailDialog = ref(false)
const currentBill = ref(null)
const submitting = ref(false)
const submitFormRef = ref(null)
const submitForm = reactive({
  actual_amount: '',
  payment_method: '',
  payment_time: '',
  transaction_note: '',
  payment_proof: '',
})
const submitRules = {
  actual_amount: [{ required: true, message: '请输入实付金额', trigger: 'blur' }],
  payment_method: [{ required: true, message: '请选择支付方式', trigger: 'change' }],
}

// 图片上传
const uploadUrl = '/api/v1/upload'
const uploadHeaders = {
  Authorization: `Bearer ${sessionStorage.getItem('token') || ''}`,
}
const uploadFileList = ref([])

function beforeUpload(file) {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB')
    return false
  }
  return true
}

function onUploadSuccess(response) {
  if (response.url) {
    submitForm.payment_proof = response.url
  }
}

function onUploadRemove() {
  submitForm.payment_proof = ''
}

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

async function loadData() {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    if (filters.status) params.status = filters.status
    if (filters.bill_type) params.bill_type = filters.bill_type
    if (filters.due_date_from) params.due_date_from = filters.due_date_from
    if (filters.due_date_to) params.due_date_to = filters.due_date_to

    const [res, statsRes] = await Promise.all([
      getPayments(params),
      getPaymentStats().catch(() => null),
    ])
    payments.value = (res && res.items) || []
    total.value = (res && res.total) || 0
    if (statsRes) {
      stats.total_pending = statsRes.total_pending || 0
      stats.total_overdue = statsRes.total_overdue || 0
      stats.total_confirmed = statsRes.total_confirmed || 0
    }
  } catch (e) {
    ElMessage.error('加载账单失败')
  } finally {
    loading.value = false
  }
}

function openSubmitDialog(row) {
  currentBill.value = row
  submitForm.actual_amount = row.due_amount
  submitForm.payment_method = ''
  submitForm.payment_time = new Date()
  submitForm.transaction_note = ''
  submitForm.payment_proof = ''
  uploadFileList.value = []
  showSubmitDialog.value = true
}

async function handleSubmitPayment() {
  const valid = await submitFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const data = { ...submitForm }
    if (data.payment_time) {
      data.payment_time = new Date(data.payment_time).toISOString()
    }
    await submitPayment(currentBill.value.id, data)
    ElMessage.success('付款凭证已提交，等待房东确认')
    showSubmitDialog.value = false
    loadData()
  } catch (e) {
    const msg = e?.response?.data?.detail || '提交失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

function openDetailDialog(row) {
  currentBill.value = row
  showDetailDialog.value = true
}

function showRejectReason(row) {
  ElMessage.warning('驳回原因：' + (row.rejected_reason || '未说明'))
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
.stats-row { display: flex; gap: 16px; margin-bottom: 16px; }
.stat-card {
  flex: 1; padding: 16px 20px; border-radius: 8px; color: #fff; text-align: center;
}
.stat-card.pending { background: linear-gradient(135deg, #e6a23c, #f0ad4e); }
.stat-card.overdue { background: linear-gradient(135deg, #f56c6c, #e74c3c); }
.stat-card.confirmed { background: linear-gradient(135deg, #67c23a, #27ae60); }
.stat-value { font-size: 24px; font-weight: bold; }
.stat-label { font-size: 13px; opacity: 0.9; margin-top: 4px; }
.filter-bar { margin-bottom: 12px; display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.form-tip { color: #999; font-size: 12px; margin-top: 4px; }

:deep(.el-table) { width: 100% !important; }
:deep(.el-table__inner-wrapper) { width: 100% !important; }

.payment-upload :deep(.el-upload--picture-card) {
  width: 120px;
  height: 120px;
  line-height: 120px;
}
.payment-upload :deep(.el-upload-list__item) {
  width: 120px;
  height: 120px;
}
.uploaded-url {
  margin-top: 8px;
  font-size: 13px;
  color: #67c23a;
}
.uploaded-url .upload-label {
  color: #606266;
}
</style>
