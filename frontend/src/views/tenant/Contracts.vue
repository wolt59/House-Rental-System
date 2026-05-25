<template>
  <div class="page-container">
    <div class="page-header"><h2>我的合同</h2></div>
    <el-table :data="contracts" stripe v-loading="loading">
      <el-table-column prop="contract_no" label="合同编号" width="180" />
      <el-table-column label="房源" width="150">
        <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="房东" width="100">
        <template #default="{ row }">{{ userNames[row.landlord_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="租期" min-width="200">
        <template #default="{ row }">{{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}</template>
      </el-table-column>
      <el-table-column label="月租金" width="100">
        <template #default="{ row }">¥{{ row.monthly_rent }}</template>
      </el-table-column>
      <el-table-column label="状态" width="140">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="280">
        <template #default="{ row }">
          <el-button v-if="canSign(row)" type="primary" size="small" @click="handleSign(row)">签约</el-button>
          <el-button v-if="canWithdraw(row)" type="warning" size="small" @click="handleWithdraw(row)">撤回</el-button>
          <el-button v-if="canCancel(row)" type="info" size="small" @click="handleCancel(row)">取消</el-button>
          <el-button v-if="canReject(row)" type="danger" size="small" @click="handleReject(row)">拒绝</el-button>
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && contracts.length === 0" description="暂无数据" />

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <el-dialog v-model="detailVisible" title="合同详情" width="700px">
      <el-descriptions :column="2" border v-if="currentContract">
        <el-descriptions-item label="合同编号">{{ currentContract.contract_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(currentContract.status)" size="small">{{ statusLabel(currentContract.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="月租金">¥{{ currentContract.monthly_rent }}</el-descriptions-item>
        <el-descriptions-item label="押金">{{ currentContract.deposit ? '¥' + currentContract.deposit : '-' }}</el-descriptions-item>
        <el-descriptions-item label="开始日期">{{ formatDate(currentContract.start_date) }}</el-descriptions-item>
        <el-descriptions-item label="结束日期">{{ formatDate(currentContract.end_date) }}</el-descriptions-item>
        <el-descriptions-item label="缴费日">{{ currentContract.payment_day || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ currentContract.remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房东签约">{{ currentContract.signed_by_landlord ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="租客签约">{{ currentContract.signed_by_tenant ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item v-if="currentContract.landlord_signed_at" label="房东签约时间" :span="2">
          {{ formatDateTime(currentContract.landlord_signed_at) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentContract.tenant_signed_at" label="租客签约时间" :span="2">
          {{ formatDateTime(currentContract.tenant_signed_at) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentContract.terminate_reason" label="终止原因" :span="2">
          {{ currentContract.terminate_reason }}
        </el-descriptions-item>
        <el-descriptions-item label="合同条款" :span="2">{{ currentContract.terms || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="rejectVisible" title="拒绝合同" width="500px">
      <el-form :model="rejectForm" label-width="80px">
        <el-form-item label="拒绝原因">
          <el-input v-model="rejectForm.reason" type="textarea" :rows="3" placeholder="请输入拒绝原因（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :loading="rejecting" @click="confirmReject">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import {
  getContracts,
  signContractTenant,
  withdrawSignatureTenant,
  cancelContract,
  rejectContract,
} from '../../api/contract'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'

const { resolveItems, userNames, propertyNames } = useNameResolver()

const contracts = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const detailVisible = ref(false)
const rejectVisible = ref(false)
const rejecting = ref(false)
const currentContract = ref(null)
const rejectForm = reactive({ reason: '' })

// 使用枚举常量管理状态
const statusMap = {
  draft: '草稿',
  pending_sign: '待签约',
  pending_tenant_sign: '待租客签约',
  pending_landlord_sign: '待房东签约',
  active: '生效中',
  terminated: '已终止',
  cancelled: '已取消',
  rejected: '已拒绝',
  expired: '已过期',
}
const statusTypeMap = {
  draft: 'info',
  pending_sign: 'warning',
  pending_tenant_sign: 'warning',
  pending_landlord_sign: 'info',
  active: 'success',
  terminated: 'danger',
  cancelled: 'info',
  rejected: 'danger',
  expired: 'info',
}

function statusLabel(s) {
  return statusMap[s] || s
}
function statusType(s) {
  return statusTypeMap[s] || 'info'
}
function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('zh-CN') : ''
}
function formatDateTime(d) {
  return d ? new Date(d).toLocaleString('zh-CN') : ''
}

// 判断是否可以签约
function canSign(row) {
  return row.status === 'pending_sign' || row.status === 'pending_tenant_sign'
}

// 判断是否可以撤回签署
function canWithdraw(row) {
  return row.signed_by_tenant && row.status !== 'active'
}

// 判断是否可以取消
function canCancel(row) {
  const cancellableStatuses = ['draft', 'pending_sign', 'pending_tenant_sign', 'pending_landlord_sign']
  return cancellableStatuses.includes(row.status)
}

// 判断是否可以拒绝
function canReject(row) {
  const rejectableStatuses = ['draft', 'pending_sign', 'pending_tenant_sign', 'pending_landlord_sign']
  return rejectableStatuses.includes(row.status)
}

async function loadData() {
  loading.value = true
  try {
    const res = await getContracts({ skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value })
    contracts.value = Array.isArray(res) ? res : []
    await resolveItems(contracts.value, ['landlord_id', 'property_id'])
    total.value = Array.isArray(res) ? res.length : 0
  } catch (e) {
    ElMessage.error('加载合同列表失败')
  } finally {
    loading.value = false
  }
}

async function handleSign(row) {
  try {
    await ElMessageBox.confirm('确定签署此合同？签署后合同将生效。', '确认签约', { type: 'warning' })
  } catch {
    return // 用户取消操作
  }
  try {
    await signContractTenant(row.id)
    ElMessage.success('签约成功')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '签约失败')
  }
}

async function handleWithdraw(row) {
  try {
    await ElMessageBox.confirm('确定撤回签署？撤回后需要重新签署合同。', '确认撤回', { type: 'warning' })
  } catch {
    return
  }
  try {
    await withdrawSignatureTenant(row.id)
    ElMessage.success('已撤回签署')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '撤回签署失败')
  }
}

async function handleCancel(row) {
  try {
    await ElMessageBox.confirm('确定取消此合同？取消后将通知对方。', '确认取消', { type: 'warning' })
  } catch {
    return
  }
  try {
    await cancelContract(row.id)
    ElMessage.success('合同已取消')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '取消合同失败')
  }
}

async function handleReject(row) {
  currentContract.value = row
  rejectForm.reason = ''
  rejectVisible.value = true
}

async function confirmReject() {
  rejecting.value = true
  try {
    await rejectContract(currentContract.value.id, { reason: rejectForm.reason })
    ElMessage.success('已拒绝合同')
    rejectVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '拒绝合同失败')
  } finally {
    rejecting.value = false
  }
}

function viewDetail(row) {
  currentContract.value = row
  detailVisible.value = true
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
