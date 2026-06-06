<template>
  <div class="page-container">
    <div class="page-header">
      <h2>预约管理</h2>
      <div class="sort-controls">
        <el-select v-model="sortBy" size="small" style="width: 130px" @change="loadData">
          <el-option label="按预约时间" value="appointment_time" />
          <el-option label="按创建时间" value="created_at" />
        </el-select>
        <el-button size="small" @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'; loadData()">
          {{ sortOrder === 'asc' ? '↑ 升序' : '↓ 降序' }}
        </el-button>
      </div>
    </div>
    
    <el-tabs v-model="activeTab" @tab-change="loadData">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="待处理" name="pending" />
      <el-tab-pane label="已处理" name="processed" />
      <el-tab-pane label="未来日程" name="upcoming" />
    </el-tabs>

    <el-table :data="bookings" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="租客" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="房源" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="预约时间" min-width="180">
        <template #default="{ row }">{{ formatDate(row.appointment_time) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="380" align="center">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" type="success" size="small" @click="handleApprove(row)">同意</el-button>
          <el-button v-if="row.status === 'pending'" type="danger" size="small" @click="handleReject(row)">拒绝</el-button>
          <el-button v-if="row.status === 'pending'" type="warning" size="small" @click="handleReschedule(row)">改期</el-button>
          <el-button v-if="row.status === 'approved'" type="success" size="small" @click="handleComplete(row)">标记完成</el-button>
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>



    </el-table>
    <el-empty v-if="!loading && bookings.length === 0" description="暂无数据" />
    <div class="pagination-wrap" v-if="total >= pageSize && activeTab !== 'all'">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="预约详情" width="600px">
      <el-descriptions :column="2" border v-if="currentItem">
        <el-descriptions-item label="租客ID">{{ currentItem.tenant_id }}</el-descriptions-item>
        <el-descriptions-item label="房源ID">{{ currentItem.property_id }}</el-descriptions-item>
        <el-descriptions-item label="房源名称" :span="2" v-if="currentItem.property">{{ currentItem.property.title }}</el-descriptions-item>
        <el-descriptions-item label="租客姓名" v-if="currentItem.tenant">{{ currentItem.tenant.full_name || currentItem.tenant.username }}</el-descriptions-item>
        <el-descriptions-item label="租客邮箱" v-if="currentItem.tenant">{{ currentItem.tenant.email }}</el-descriptions-item>
        <el-descriptions-item label="租客电话" :span="2" v-if="currentItem.tenant && currentItem.tenant.phone">{{ currentItem.tenant.phone }}</el-descriptions-item>
        <el-descriptions-item label="预约时间">{{ formatDate(currentItem.appointment_time) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(currentItem.status) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ currentItem.note || '-' }}</el-descriptions-item>
        <el-descriptions-item label="拒绝原因" :span="2" v-if="currentItem.reject_reason">{{ currentItem.reject_reason }}</el-descriptions-item>
        <el-descriptions-item label="改期建议" :span="2" v-if="currentItem.reschedule_proposal">{{ currentItem.reschedule_proposal }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(currentItem.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDate(currentItem.updated_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 拒绝对话框 -->
    <el-dialog v-model="rejectVisible" title="拒绝预约" width="600px">
      <el-form :model="rejectForm" label-width="90px">
        <el-form-item label="拒绝原因">
          <el-input v-model="rejectForm.reason" type="textarea" :rows="4" placeholder="请填写拒绝原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :loading="submitting" @click="submitReject">确认拒绝</el-button>
      </template>
    </el-dialog>

    <!-- 改期对话框 -->
    <el-dialog v-model="rescheduleVisible" title="协商改期" width="600px">
      <el-form :model="rescheduleForm" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="新预约时间">
              <el-date-picker 
                v-model="rescheduleForm.appointment_time" 
                type="datetime" 
                placeholder="选择时间" 
                style="width: 100%" 
                :disabled-date="d => d.getTime() < Date.now() - 86400000" 
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="改期说明">
              <el-input v-model="rescheduleForm.message" type="textarea" :rows="4" placeholder="请填写改期原因和建议" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="rescheduleVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitReschedule">确认改期</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getBookings, approveBooking, rejectBooking, rescheduleBooking, completeBooking } from '../../api/booking'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'

const { resolveItems, userNames, propertyNames } = useNameResolver()

const bookings = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const activeTab = ref('all')
const sortBy = ref('appointment_time')
const sortOrder = ref('asc')
const detailVisible = ref(false)
const rejectVisible = ref(false)
const rescheduleVisible = ref(false)
const submitting = ref(false)
const currentItem = ref(null)
const rejectForm = reactive({ reason: '' })
const rescheduleForm = reactive({ appointment_time: '', message: '' })

const statusMap = { 
  pending: '待确认', 
  approved: '已同意', 
  rejected: '已拒绝', 
  cancelled: '已取消', 
  completed: '已完成',
  negotiating: '待协商'
}
const statusTypeMap = { 
  pending: 'warning', 
  approved: 'success', 
  rejected: 'danger', 
  cancelled: 'info', 
  completed: 'success',
  negotiating: 'warning'
}
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function formatDate(d) { return d ? new Date(d).toLocaleString('zh-CN') : '' }

async function loadData() {
  loading.value = true
  try {
    const params = { 
      skip: (currentPage.value - 1) * pageSize.value, 
      limit: pageSize.value,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }
    if (activeTab.value === 'pending') {
      params.status = 'pending'
    } else if (activeTab.value === 'processed') {
      params.status = 'approved,completed,rejected,cancelled,negotiating'
    } else if (activeTab.value === 'all') {
      // "全部"展示所有记录，不做分页
      params.limit = 9999
      params.skip = 0
    } else if (activeTab.value === 'upcoming') {
      // 未来日程：后端筛选已同意状态，前端再按时间过滤
      const res = await getBookings({ status: 'approved', skip: 0, limit: 100, sort_by: sortBy.value, sort_order: sortOrder.value })
      const allBookings = (res && res.items) || []
      const now = new Date()
      bookings.value = allBookings.filter(b => new Date(b.appointment_time) > now)
      await resolveItems(bookings.value, ['tenant_id', 'property_id'])
      total.value = bookings.value.length
      return
    }
    const res = await getBookings(params)
    bookings.value = res.items || []
    await resolveItems(bookings.value, ['tenant_id', 'property_id'])
    total.value = res.total || 0
  } catch (e) { 
    ElMessage.error('加载预约列表失败') 
  } finally {
    loading.value = false
  }
}

async function handleApprove(row) {
  try {
    await ElMessageBox.confirm('确认同意此预约？', '提示', { type: 'info' })
  } catch {
    return
  }
  try {
    await approveBooking(row.id)
    ElMessage.success('已同意预约')
    row.status = 'approved'
    row.updated_at = new Date().toISOString()
    // 当前在「待处理」tab时，移除已处理的记录
    if (activeTab.value === 'pending') {
      const idx = bookings.value.findIndex(b => b.id === row.id)
      if (idx !== -1) { bookings.value.splice(idx, 1); total.value = Math.max(0, total.value - 1) }
    }
  } catch (e) { 
    ElMessage.error('操作失败') 
  }
}

function handleReject(row) {
  currentItem.value = row
  rejectForm.reason = ''
  rejectVisible.value = true
}

async function submitReject() {
  if (!rejectForm.reason.trim()) {
    ElMessage.warning('请填写拒绝原因')
    return
  }
  submitting.value = true
  try {
    await rejectBooking(currentItem.value.id, rejectForm.reason)
    ElMessage.success('已拒绝预约')
    rejectVisible.value = false
    const row = currentItem.value
    row.status = 'rejected'
    row.reject_reason = rejectForm.reason
    row.updated_at = new Date().toISOString()
    // 当前在「待处理」tab时，移除已处理的记录
    if (activeTab.value === 'pending') {
      const idx = bookings.value.findIndex(b => b.id === row.id)
      if (idx !== -1) { bookings.value.splice(idx, 1); total.value = Math.max(0, total.value - 1) }
    }
  } catch (e) { 
    ElMessage.error('操作失败') 
  } finally {
    submitting.value = false
  }
}

function handleReschedule(row) {
  currentItem.value = row
  rescheduleForm.appointment_time = ''
  rescheduleForm.message = ''
  rescheduleVisible.value = true
}

async function submitReschedule() {
  if (!rescheduleForm.appointment_time) {
    ElMessage.warning('请选择新的预约时间')
    return
  }
  if (!rescheduleForm.message.trim()) {
    ElMessage.warning('请填写改期说明')
    return
  }
  submitting.value = true
  try {
    await rescheduleBooking(currentItem.value.id, {
      appointment_time: new Date(rescheduleForm.appointment_time).toISOString(),
      message: rescheduleForm.message
    })
    ElMessage.success('已发送改期建议')
    rescheduleVisible.value = false
    const row = currentItem.value
    row.status = 'negotiating'
    row.reschedule_proposal = rescheduleForm.message
    row.updated_at = new Date().toISOString()
    // 当前在「待处理」tab时，移除已改期的记录
    if (activeTab.value === 'pending') {
      const idx = bookings.value.findIndex(b => b.id === row.id)
      if (idx !== -1) { bookings.value.splice(idx, 1); total.value = Math.max(0, total.value - 1) }
    }
  } catch (e) { 
    ElMessage.error('操作失败') 
  } finally {
    submitting.value = false
  }
}

async function handleComplete(row) {
  try {
    await ElMessageBox.confirm('确认租客已完成线下看房？', '提示', { type: 'info' })
  } catch {
    return
  }
  try {
    await completeBooking(row.id)
    ElMessage.success('已标记为完成')
    row.status = 'completed'
    row.updated_at = new Date().toISOString()
    // 当前在「未来日程」tab时，移除已完成的记录
    if (activeTab.value === 'upcoming') {
      const idx = bookings.value.findIndex(b => b.id === row.id)
      if (idx !== -1) { bookings.value.splice(idx, 1); total.value = Math.max(0, total.value - 1) }
    }
  } catch (e) { 
    ElMessage.error('操作失败') 
  }
}

function viewDetail(row) {
  currentItem.value = row
  detailVisible.value = true
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
.sort-controls { display: flex; gap: 8px; align-items: center; }
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }

/* 让表格占满容器宽度 */
:deep(.el-table) {
  width: 100% !important;
}

:deep(.el-table__inner-wrapper) {
  width: 100% !important;
}
</style>
