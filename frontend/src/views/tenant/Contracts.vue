<template>
  <div class="page-container">
    <div class="page-header">
      <h2>我的合同</h2>
    </div>

    <el-tabs v-model="activeTab" class="contract-tabs">
      <el-tab-pane
        v-for="tab in CONTRACT_TABS"
        :key="tab.name"
        :name="tab.name"
      >
        <template #label>
          <span>{{ tab.label }} ({{ tabCounts[tab.name] ?? 0 }})</span>
        </template>
      </el-tab-pane>
    </el-tabs>

    <el-table
      :data="displayContracts"
      stripe
      v-loading="loading"
      class="contract-table"
      table-layout="fixed"
    >
      <el-table-column prop="contract_no" label="合同编号" width="172" show-overflow-tooltip />
      <el-table-column label="房源" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="房东" width="96" show-overflow-tooltip>
        <template #default="{ row }">{{ userNames[row.landlord_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column v-if="tableColumns.showLeasePeriod" label="租期" min-width="200">
        <template #default="{ row }">{{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}</template>
      </el-table-column>
      <el-table-column v-if="tableColumns.showExpiringEndDate" label="到期日期" width="118" align="center">
        <template #default="{ row }">{{ formatDate(row.end_date) }}</template>
      </el-table-column>
      <el-table-column v-if="tableColumns.showDaysRemaining" label="剩余天数" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getDaysRemainingType(row)">{{ getDaysRemaining(row) }}天</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="月租金" width="96" align="right">
        <template #default="{ row }">¥{{ row.monthly_rent }}</template>
      </el-table-column>
      <el-table-column v-if="tableColumns.showStatus" label="状态" width="108" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column
        v-if="tableColumns.showSignColumns"
        label="房东签署"
        width="88"
        align="center"
      >
        <template #default="{ row }">{{ row.signed_by_landlord ? '✓' : '✗' }}</template>
      </el-table-column>
      <el-table-column
        v-if="tableColumns.showSignColumns"
        label="租客签署"
        width="88"
        align="center"
      >
        <template #default="{ row }">{{ row.signed_by_tenant ? '✓' : '✗' }}</template>
      </el-table-column>
      <el-table-column
        label="操作"
        align="center"
        fixed="right"
        :width="tableColumns.operationWidth"
        :min-width="tableColumns.operationMinWidth"
      >
        <template #default="{ row }">
          <template v-if="row.status === 'draft'">
            <el-button type="info" size="small" @click="handleCancel(row)">取消</el-button>
          </template>
          <template v-else-if="row.status === 'pending_sign'">
            <el-button v-if="canSign(row)" type="primary" size="small" @click="handleSign(row)">签约</el-button>
            <el-button v-if="canWithdraw(row)" type="warning" size="small" @click="handleWithdraw(row)">撤回</el-button>
            <el-button type="danger" size="small" @click="handleReject(row)">拒绝</el-button>
            <el-button type="info" size="small" @click="handleCancel(row)">取消</el-button>
          </template>
          <template v-else-if="row.status === 'part_signed'">
            <el-button v-if="canSign(row)" type="primary" size="small" @click="handleSign(row)">签约</el-button>
            <el-button v-if="canWithdraw(row)" type="warning" size="small" @click="handleWithdraw(row)">撤回</el-button>
          </template>
          <template v-else-if="row.status === 'active'">
            <el-button type="success" size="small" @click="handleDownloadPDF(row)">PDF</el-button>
          </template>
          <template v-else-if="row.status === 'terminate_negotiating'">
            <el-button type="success" size="small" @click="handleApproveTermination(row)">同意解约</el-button>
            <el-button type="danger" size="small" @click="handleRejectTermination(row)">拒绝解约</el-button>
          </template>
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty
      v-if="!loading && displayContracts.length === 0"
      :description="emptyDescription"
    />

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

    <el-dialog v-model="approveTerminationVisible" title="同意解约申请" width="500px">
      <el-alert
        title="提示"
        type="warning"
        description="同意解约后，合同将正式终止，请谨慎操作。"
        show-icon
        :closable="false"
        style="margin-bottom: 20px"
      />
      <el-form :model="approveTerminationForm" label-width="100px">
        <el-form-item label="处理意见">
          <el-input
            v-model="approveTerminationForm.opinion"
            type="textarea"
            :rows="3"
            placeholder="请输入处理意见（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approveTerminationVisible = false">取消</el-button>
        <el-button type="success" :loading="approvingTermination" @click="confirmApproveTermination">确认同意</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="rejectTerminationVisible" title="拒绝解约申请" width="500px">
      <el-form :model="rejectTerminationForm" label-width="80px">
        <el-form-item label="拒绝原因" required>
          <el-input
            v-model="rejectTerminationForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入拒绝原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectTerminationVisible = false">取消</el-button>
        <el-button type="danger" :loading="rejectingTermination" @click="confirmRejectTermination">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  getContracts,
  withdrawSignatureTenant,
  cancelContract,
  rejectContract,
} from '../../api/contract'
import {
  getTerminationRequests,
  approveTerminationRequest,
  rejectTerminationRequest,
} from '../../api/contract_termination'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'
import {
  CONTRACT_TABS,
  useContractListTabs,
  useContractTableColumns,
  statusLabel,
  statusType,
  getDaysRemaining,
  getDaysRemainingType,
} from '../../composables/useContractListTabs'

const router = useRouter()
const { resolveItems, userNames, propertyNames } = useNameResolver()

const activeTab = ref('all')
const contracts = ref([])
const loading = ref(false)
const { tabCounts, contractsForTab } = useContractListTabs(contracts)

const displayContracts = computed(() => contractsForTab(activeTab.value))
const tableColumns = useContractTableColumns(activeTab)

const emptyDescription = computed(() => {
  const tab = CONTRACT_TABS.find((t) => t.name === activeTab.value)
  return tab ? `暂无「${tab.label}」` : '暂无数据'
})

const rejectVisible = ref(false)
const rejecting = ref(false)
const currentContract = ref(null)
const rejectForm = reactive({ reason: '' })

const approveTerminationVisible = ref(false)
const rejectTerminationVisible = ref(false)
const approvingTermination = ref(false)
const rejectingTermination = ref(false)
const currentTerminationContract = ref(null)
const approveTerminationForm = reactive({ opinion: '' })
const rejectTerminationForm = reactive({ reason: '' })

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('zh-CN') : ''
}

function canSign(row) {
// 租客只能在房东已签署且租客未签署的情况下进行签署
  // 可以是 PART_SIGNED 或 PENDING_TENANT_SIGN 状态
  return !row.signed_by_tenant && 
         row.signed_by_landlord &&
         (row.status === 'part_signed' || row.status === 'pending_tenant_sign')
}

function canWithdraw(row) {
  return row.signed_by_tenant && (row.status === 'part_signed' || row.status === 'pending_sign')
}

async function loadData() {
  loading.value = true
  try {
    const res = await getContracts({ skip: 0, limit: 100 })
    contracts.value = Array.isArray(res) ? res : []
    await resolveItems(contracts.value, ['landlord_id', 'property_id'])
  } catch {
    ElMessage.error('加载合同列表失败')
  } finally {
    loading.value = false
  }
}

function handleSign(row) {
  router.push(`/tenant/contract/${row.id}/sign`)
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

function handleReject(row) {
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
  router.push(`/tenant/contract/${row.id}`)
}

function handleDownloadPDF(row) {
  router.push({ path: `/tenant/contract/${row.id}`, query: { export: 'pdf' } })
}

function handleApproveTermination(row) {
  currentTerminationContract.value = row
  approveTerminationForm.opinion = ''
  approveTerminationVisible.value = true
}

async function confirmApproveTermination() {
  approvingTermination.value = true
  try {
    const requests = await getTerminationRequests({
      contract_id: currentTerminationContract.value.id,
    })
    if (!requests?.length) {
      ElMessage.error('未找到解约申请记录')
      return
    }
    await approveTerminationRequest(requests[0].id, {
      opinion: approveTerminationForm.opinion,
    })
    ElMessage.success('已同意解约申请，合同已终止')
    approveTerminationVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '同意解约失败')
  } finally {
    approvingTermination.value = false
  }
}

function handleRejectTermination(row) {
  currentTerminationContract.value = row
  rejectTerminationForm.reason = ''
  rejectTerminationVisible.value = true
}

async function confirmRejectTermination() {
  if (!rejectTerminationForm.reason) {
    ElMessage.warning('请输入拒绝原因')
    return
  }

  rejectingTermination.value = true
  try {
    const requests = await getTerminationRequests({
      contract_id: currentTerminationContract.value.id,
    })
    if (!requests?.length) {
      ElMessage.error('未找到解约申请记录')
      return
    }
    await rejectTerminationRequest(requests[0].id, rejectTerminationForm.reason)
    ElMessage.success('已拒绝解约申请')
    rejectTerminationVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '拒绝解约失败')
  } finally {
    rejectingTermination.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-header {
  margin-bottom: 20px;
}

.contract-tabs {
  margin-bottom: 16px;
}

.contract-table {
  width: 100%;
}

.contract-table :deep(.el-table__header-wrapper table),
.contract-table :deep(.el-table__body-wrapper table) {
  width: 100% !important;
  table-layout: fixed;
}

.contract-table :deep(.el-table__cell) {
  padding: 10px 0;
}

.contract-table :deep(.el-table__header .el-table__cell) {
  font-weight: 600;
}
</style>
