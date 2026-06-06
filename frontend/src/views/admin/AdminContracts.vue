<template>
  <div class="page-container">
    <div class="page-header">
      <h2>合同管理</h2>
      <div class="header-actions">
        <el-select v-model="statusFilter" placeholder="按状态筛选" clearable style="width: 200px" @change="loadData">
          <el-option v-for="(v, k) in CONTRACT_STATUS_LABELS" :key="k" :label="v" :value="k" />
        </el-select>
        <el-button type="primary" @click="loadData">刷新</el-button>
      </div>
    </div>

    <el-table :data="contracts" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="contract_no" label="合同编号" width="170" show-overflow-tooltip />
      <el-table-column label="房东" width="100" show-overflow-tooltip>
        <template #default="{ row }">{{ userNames[row.landlord_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="租客" width="100" show-overflow-tooltip>
        <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="房源" width="150" show-overflow-tooltip>
        <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="租期" min-width="180">
        <template #default="{ row }">{{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}</template>
      </el-table-column>
      <el-table-column label="月租金" width="90" align="right">
        <template #default="{ row }">¥{{ row.monthly_rent }}</template>
      </el-table-column>
      <el-table-column label="签署" width="120" align="center">
        <template #default="{ row }">
          <span :style="{ color: row.signed_by_landlord ? '#67c23a' : '#c0c4cc' }">房东{{ row.signed_by_landlord ? '✓' : '✗' }}</span>
          &nbsp;
          <span :style="{ color: row.signed_by_tenant ? '#67c23a' : '#c0c4cc' }">租客{{ row.signed_by_tenant ? '✓' : '✗' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="200" align="center" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button
            v-if="canCancel(row)"
            type="warning" size="small"
            @click="handleCancel(row)"
          >取消</el-button>
          <el-button
            v-if="row.status === 'active'"
            type="danger" size="small"
            @click="handleTerminate(row)"
          >终止</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && contracts.length === 0" description="暂无合同数据" />

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <!-- 合同详情对话框 -->
    <el-dialog v-model="detailVisible" title="合同详情" width="700px">
      <el-descriptions :column="2" border v-if="currentContract">
        <el-descriptions-item label="合同编号">{{ currentContract.contract_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(currentContract.status)" size="small">{{ statusLabel(currentContract.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="房东">{{ userNames[currentContract.landlord_id] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="租客">{{ userNames[currentContract.tenant_id] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房源">{{ propertyNames[currentContract.property_id] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="月租金">¥{{ currentContract.monthly_rent }}</el-descriptions-item>
        <el-descriptions-item label="押金">{{ currentContract.deposit ? '¥' + currentContract.deposit : '-' }}</el-descriptions-item>
        <el-descriptions-item label="开始日期">{{ formatDate(currentContract.start_date) }}</el-descriptions-item>
        <el-descriptions-item label="结束日期">{{ formatDate(currentContract.end_date) }}</el-descriptions-item>
        <el-descriptions-item label="缴费日">{{ currentContract.payment_day ? '每月' + currentContract.payment_day + '日' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="房东签署">{{ currentContract.signed_by_landlord ? '已签署' : '未签署' }}</el-descriptions-item>
        <el-descriptions-item label="租客签署">{{ currentContract.signed_by_tenant ? '已签署' : '未签署' }}</el-descriptions-item>
        <el-descriptions-item label="房东签署时间" v-if="currentContract.landlord_signed_at">{{ formatDateTime(currentContract.landlord_signed_at) }}</el-descriptions-item>
        <el-descriptions-item label="租客签署时间" v-if="currentContract.tenant_signed_at">{{ formatDateTime(currentContract.tenant_signed_at) }}</el-descriptions-item>
        <el-descriptions-item label="合同条款" :span="2">{{ currentContract.terms || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ currentContract.remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="终止原因" :span="2" v-if="currentContract.terminate_reason">
          <span style="color: #f56c6c">{{ currentContract.terminate_reason }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="终止时间" v-if="currentContract.terminated_at">{{ formatDateTime(currentContract.terminated_at) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(currentContract.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDateTime(currentContract.updated_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 取消/终止确认对话框 -->
    <el-dialog v-model="actionVisible" :title="actionTitle" width="500px">
      <el-alert
        :title="actionAlertTitle"
        type="warning"
        :description="actionAlertDesc"
        show-icon
        :closable="false"
        style="margin-bottom: 20px"
      />
      <el-form :model="actionForm" label-width="80px">
        <el-form-item label="原因" required>
          <el-input v-model="actionForm.reason" type="textarea" :rows="3" :placeholder="actionPlaceholder" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="actionVisible = false">取消</el-button>
        <el-button :type="actionType" :loading="submitting" @click="confirmAction">{{ actionConfirmText }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getContracts, cancelContract, terminateContract } from '../../api/contract'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'
import {
  CONTRACT_STATUS_LABELS,
  statusLabel,
  statusType,
} from '../../composables/useContractListTabs'

const contracts = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(15)
const currentPage = ref(1)
const statusFilter = ref('')
const { resolveItems, userNames, propertyNames } = useNameResolver()

const detailVisible = ref(false)
const currentContract = ref(null)

const actionVisible = ref(false)
const submitting = ref(false)
const actionTitle = ref('')
const actionType = ref('warning')
const actionConfirmText = ref('确认')
const actionAlertTitle = ref('')
const actionAlertDesc = ref('')
const actionPlaceholder = ref('请填写原因')
const actionForm = reactive({ reason: '' })

let actionTarget = null
let actionMode = 'cancel'

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('zh-CN') : ''
}

function formatDateTime(d) {
  return d ? new Date(d).toLocaleString('zh-CN') : ''
}

function canCancel(row) {
  return ['draft', 'pending_sign', 'pending_landlord_sign', 'pending_tenant_sign', 'part_signed'].includes(row.status)
}

async function loadData() {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    if (statusFilter.value) params.status_filter = statusFilter.value

    const res = await getContracts(params)
    contracts.value = Array.isArray(res) ? res : []
    await resolveItems(contracts.value, ['tenant_id', 'landlord_id', 'property_id'])
    total.value = Array.isArray(res) ? res.length : 0
  } catch (e) {
    ElMessage.error('加载合同列表失败')
  } finally {
    loading.value = false
  }
}

function viewDetail(row) {
  currentContract.value = row
  detailVisible.value = true
}

function handleCancel(row) {
  actionTarget = row
  actionMode = 'cancel'
  actionTitle.value = '取消合同'
  actionType.value = 'warning'
  actionConfirmText.value = '确认取消'
  actionAlertTitle.value = '确认取消此合同？'
  actionAlertDesc.value = '取消合同后，双方将无法继续签署，合同将变为已取消状态。此操作不可逆。'
  actionPlaceholder.value = '请填写取消原因（可选）'
  actionForm.reason = ''
  actionVisible.value = true
}

function handleTerminate(row) {
  actionTarget = row
  actionMode = 'terminate'
  actionTitle.value = '终止合同'
  actionType.value = 'danger'
  actionConfirmText.value = '确认终止'
  actionAlertTitle.value = '确认终止此生效中的合同？'
  actionAlertDesc.value = '终止合同后，房源将恢复为空置状态，未完成的账单将被取消。此操作不可逆，请谨慎操作。'
  actionPlaceholder.value = '请填写终止原因（必填）'
  actionForm.reason = ''
  actionVisible.value = true
}

async function confirmAction() {
  if (actionMode === 'terminate' && !actionForm.reason.trim()) {
    ElMessage.warning('请填写终止原因')
    return
  }

  submitting.value = true
  try {
    if (actionMode === 'cancel') {
      await cancelContract(actionTarget.id)
      ElMessage.success('合同已取消')
    } else {
      await terminateContract(actionTarget.id, { reason: actionForm.reason })
      ElMessage.success('合同已终止')
    }
    actionVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

:deep(.el-table) {
  width: 100% !important;
}

:deep(.el-table__inner-wrapper) {
  width: 100% !important;
}
</style>
