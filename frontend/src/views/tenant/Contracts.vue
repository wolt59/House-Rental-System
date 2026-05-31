<template>
  <div class="page-container">
    <div class="page-header"><h2>我的合同</h2></div>
    
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <!-- 全部合同 -->
      <el-tab-pane name="all">
        <template #label>
          <span>全部合同 ({{ contracts.length }})</span>
        </template>
        
        <el-table :data="contracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="房东" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.landlord_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="租期" min-width="220">
            <template #default="{ row }">{{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}</template>
          </el-table-column>
          <el-table-column label="月租金" width="100" align="right">
            <template #default="{ row }">¥{{ row.monthly_rent }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="320" align="center">
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
      </el-tab-pane>

      <!-- 待签署 -->
      <el-tab-pane name="pending_sign">
        <template #label>
          <span>待签署 ({{ pendingSignContracts.length }})</span>
        </template>
        
        <el-table :data="pendingSignContracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="房东" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.landlord_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="200" align="center">
            <template #default="{ row }">
              <el-button v-if="canSign(row)" type="primary" size="small" @click="handleSign(row)">签约</el-button>
              <el-button size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && pendingSignContracts.length === 0" description="暂无待签署的合同" />
      </el-tab-pane>

      <!-- 生效中 -->
      <el-tab-pane name="active">
        <template #label>
          <span>生效中 ({{ activeContracts.length }})</span>
        </template>
        
        <el-table :data="activeContracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="房东" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.landlord_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="租期" min-width="220">
            <template #default="{ row }">{{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}</template>
          </el-table-column>
          <el-table-column label="月租金" width="100" align="right">
            <template #default="{ row }">¥{{ row.monthly_rent }}</template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && activeContracts.length === 0" description="暂无生效合同" />
      </el-tab-pane>

      <!-- 即将到期 -->
      <el-tab-pane name="expiring">
        <template #label>
          <span>即将到期 ({{ expiringContracts.length }})</span>
        </template>
        
        <el-table :data="expiringContracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="房东" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.landlord_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="到期日期" min-width="150">
            <template #default="{ row }">{{ formatDate(row.end_date) }}</template>
          </el-table-column>
          <el-table-column label="剩余天数" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getDaysRemainingType(row)">{{ getDaysRemaining(row) }}天</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && expiringContracts.length === 0" description="暂无即将到期的合同" />
      </el-tab-pane>

      <!-- 已结束（包含已到期和已终止） -->
      <el-tab-pane name="expired">
        <template #label>
          <span>已结束 ({{ expiredContracts.length }})</span>
        </template>
        
        <el-table :data="expiredContracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="房东" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.landlord_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="结束日期" min-width="150">
            <template #default="{ row }">{{ formatDate(row.end_date) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && expiredContracts.length === 0" description="暂无已结束的合同" />
      </el-tab-pane>

      <!-- 解约协商中 -->
      <el-tab-pane name="terminate_negotiating">
        <template #label>
          <span>
            解约协商中 ({{ negotiatingContracts.length }})
          </span>
        </template>
        
        <el-table :data="negotiatingContracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="房东" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.landlord_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="月租金" width="100" align="right">
            <template #default="{ row }">¥{{ row.monthly_rent }}</template>
          </el-table-column>
          <el-table-column label="状态" width="120" align="center">
            <template #default="{ row }">
              <el-tag type="warning" size="small">解约协商中</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="280" align="center">
            <template #default="{ row }">
              <el-button type="success" size="small" @click="handleApproveTermination(row)">同意解约</el-button>
              <el-button type="danger" size="small" @click="handleRejectTermination(row)">拒绝解约</el-button>
              <el-button size="small" @click="viewDetail(row)">查看详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && negotiatingContracts.length === 0" description="暂无解约协商中的合同" />
      </el-tab-pane>
    </el-tabs>

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

    <!-- 同意解约对话框 -->
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

    <!-- 拒绝解约对话框 -->
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
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  getContracts,
  signContractTenant,
  withdrawSignatureTenant,
  cancelContract,
  rejectContract,
} from '../../api/contract'
import { 
  getTerminationRequests,
  approveTerminationRequest,
  rejectTerminationRequest 
} from '../../api/contract_termination'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'
import request from '../../utils/request'

const router = useRouter()

const { resolveItems, userNames, propertyNames } = useNameResolver()

// Tab切换
const activeTab = ref('all')

const contracts = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const rejectVisible = ref(false)
const rejecting = ref(false)
const currentContract = ref(null)
const rejectForm = reactive({ reason: '' })
const landlordInfo = ref(null)
const tenantInfo = ref(null)

// 解约申请处理相关
const approveTerminationVisible = ref(false)
const rejectTerminationVisible = ref(false)
const approvingTermination = ref(false)
const rejectingTermination = ref(false)
const currentTerminationContract = ref(null)
const approveTerminationForm = reactive({ opinion: '' })
const rejectTerminationForm = reactive({ reason: '' })

// 合同分类计算属性
const pendingSignContracts = computed(() => contracts.value.filter(c => 
  c.status === 'pending_sign' || 
  c.status === 'part_signed' ||
  (!c.signed_by_tenant && c.status !== 'active' && c.status !== 'draft')
))
const activeContracts = computed(() => {
  const now = new Date()
  return contracts.value.filter(c => {
    if (c.status !== 'active') return false
    const endDate = new Date(c.end_date)
    // 只包含未过期的合同
    return endDate >= now
  })
})
const expiringContracts = computed(() => {
  const now = new Date()
  const thirtyDaysLater = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000)
  return contracts.value.filter(c => {
    if (c.status !== 'active') return false
    const endDate = new Date(c.end_date)
    return endDate > now && endDate <= thirtyDaysLater
  })
})
const expiredContracts = computed(() => {
  const now = new Date()
  return contracts.value.filter(c => {
    // 状态为expired的合同（已到期）
    if (c.status === 'expired') return true
    // 状态为terminated的合同（已终止）
    if (c.status === 'terminated') return true
    // 状态为active但已结束日期的合同
    if (c.status === 'active') {
      const endDate = new Date(c.end_date)
      return endDate < now
    }
    return false
  })
})

// 解约协商中的合同
const negotiatingContracts = computed(() => 
  contracts.value.filter(c => c.status === 'terminate_negotiating')
)

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
  terminate_negotiating: '解约协商中',
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
  terminate_negotiating: 'warning',
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

// 计算合同剩余天数
function getDaysRemaining(row) {
  if (!row.end_date) return 0
  const now = new Date()
  const endDate = new Date(row.end_date)
  const diffTime = endDate - now
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays > 0 ? diffDays : 0
}

// 根据剩余天数获取标签类型
function getDaysRemainingType(row) {
  const days = getDaysRemaining(row)
  if (days <= 7) return 'danger'
  if (days <= 15) return 'warning'
  return 'success'
}

// Tab切换处理
function handleTabChange(tab) {
  if (['all', 'pending_sign', 'active', 'expiring', 'expired'].includes(tab)) {
    loadData()
  }
}

// 判断是否可以签约
function canSign(row) {
  // 租客只能在房东已签署且租客未签署的情况下进行签署
  // 必须是 PART_SIGNED（部分签署）状态，表示房东已签
  return !row.signed_by_tenant && 
         row.signed_by_landlord &&
         row.status === 'part_signed'
}

// 判断是否可以撤回签署
function canWithdraw(row) {
  // 只有当租客已签署且合同未生效时才能撤回
  // 允许撤回的状态：PART_SIGNED（部分签署）
  // 不允许撤回：ACTIVE（已生效）、TERMINATED（已终止）、CANCELLED（已取消）、EXPIRED（已过期）
  return row.signed_by_tenant && 
         (row.status === 'part_signed' || row.status === 'pending_sign')
}

// 判断是否可以取消
function canCancel(row) {
  // 只有草稿或待签约状态可以取消
  const cancellableStatuses = ['draft', 'pending_sign']
  return cancellableStatuses.includes(row.status)
}

// 判断是否可以拒绝
function canReject(row) {
  const rejectableStatuses = ['pending_sign', 'part_signed', 'draft']
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
  // 跳转到签署页面
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
  router.push(`/tenant/contract/${row.id}`)
}

// 处理同意解约申请
async function handleApproveTermination(row) {
  currentTerminationContract.value = row
  approveTerminationForm.opinion = ''
  approveTerminationVisible.value = true
}

async function confirmApproveTermination() {
  approvingTermination.value = true
  try {
    // 首先需要获取该合同对应的解约申请ID
    const requests = await getTerminationRequests({ contract_id: currentTerminationContract.value.id })
    
    if (!requests || requests.length === 0) {
      ElMessage.error('未找到解约申请记录')
      return
    }
    
    const terminationRequest = requests[0]
    
    // 调用同意接口
    await approveTerminationRequest(terminationRequest.id, { 
      opinion: approveTerminationForm.opinion 
    })
    
    ElMessage.success('已同意解约申请，合同已终止')
    approveTerminationVisible.value = false
    loadData()
  } catch (e) {
    console.error('同意解约失败:', e)
    ElMessage.error(e.response?.data?.detail || '同意解约失败')
  } finally {
    approvingTermination.value = false
  }
}

// 处理拒绝解约申请
async function handleRejectTermination(row) {
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
    // 首先需要获取该合同对应的解约申请ID
    const requests = await getTerminationRequests({ contract_id: currentTerminationContract.value.id })
    
    if (!requests || requests.length === 0) {
      ElMessage.error('未找到解约申请记录')
      return
    }
    
    const terminationRequest = requests[0]
    
    // 调用拒绝接口
    await rejectTerminationRequest(terminationRequest.id, rejectTerminationForm.reason)
    
    ElMessage.success('已拒绝解约申请')
    rejectTerminationVisible.value = false
    loadData()
  } catch (e) {
    console.error('拒绝解约失败:', e)
    ElMessage.error(e.response?.data?.detail || '拒绝解约失败')
  } finally {
    rejectingTermination.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

/* 让表格占满容器宽度 */
:deep(.el-table) {
  width: 100% !important;
}

:deep(.el-table__inner-wrapper) {
  width: 100% !important;
}
</style>
