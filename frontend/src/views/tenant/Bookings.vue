<template>
  <div class="page-container">
    <div class="page-header">
      <h2>我的预约</h2>
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
      <el-tab-pane label="待确认" name="pending" />
      <el-tab-pane label="待协商" name="negotiating" />
      <el-tab-pane label="已结束" name="ended" />
      <el-tab-pane label="已拒绝" name="rejected" />
      <el-tab-pane label="已取消" name="cancelled" />
      <el-tab-pane label="未来日程" name="upcoming" />
    </el-tabs>

    <el-table :data="bookings" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="房源" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">房源 #{{ row.property_id }}</template>
      </el-table-column>
      <el-table-column label="预约时间" min-width="180">
        <template #default="{ row }">{{ formatDate(row.appointment_time) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="note" label="备注" min-width="150" show-overflow-tooltip />
      <el-table-column label="操作" min-width="320" align="center">
        <template #default="{ row }">
          <el-button v-if="row.status === 'completed' && !bookingWithApplications.has(row.id)" type="primary" size="small" @click="showContractApplicationDialog(row)">发起合约申请</el-button>
          <el-button v-if="row.status === 'approved'" type="success" size="small" @click="handleComplete(row)">标记完成</el-button>
          <el-button v-if="row.status === 'pending'" type="danger" size="small" @click="handleCancel(row)">取消</el-button>
          <el-button v-if="row.status === 'negotiating'" type="primary" size="small" @click="handleAcceptReschedule(row)">同意改期</el-button>
          <el-button v-if="row.status === 'negotiating'" type="warning" size="small" @click="handleRejectReschedule(row)">拒绝改期</el-button>
          <el-button v-if="row.status === 'negotiating'" type="danger" size="small" @click="handleCancel(row)">取消</el-button>
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
      <el-descriptions :column="1" border v-if="currentItem">
        <el-descriptions-item label="房源ID">{{ currentItem.property_id }}</el-descriptions-item>
        <el-descriptions-item label="房源名称" v-if="currentItem.property">{{ currentItem.property.title }}</el-descriptions-item>
        <el-descriptions-item label="房东姓名" v-if="currentItem.property && currentItem.property.owner">{{ currentItem.property.owner.full_name || currentItem.property.owner.username }}</el-descriptions-item>
        <el-descriptions-item label="房东邮箱" v-if="currentItem.property && currentItem.property.owner">{{ currentItem.property.owner.email }}</el-descriptions-item>
        <el-descriptions-item label="房东电话" v-if="currentItem.property && currentItem.property.owner && currentItem.property.owner.phone">{{ currentItem.property.owner.phone }}</el-descriptions-item>
        <el-descriptions-item label="预约时间">{{ formatDate(currentItem.appointment_time) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(currentItem.status) }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ currentItem.note || '-' }}</el-descriptions-item>
        <el-descriptions-item label="拒绝原因" v-if="currentItem.reject_reason">{{ currentItem.reject_reason }}</el-descriptions-item>
        <el-descriptions-item label="改期建议" v-if="currentItem.reschedule_proposal">{{ currentItem.reschedule_proposal }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(currentItem.created_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getBookings, updateBooking, completeBooking, respondReschedule } from '../../api/booking'
import { autoCreateContract } from '../../api/contract'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import request from '../../utils/request'

const router = useRouter()
const bookings = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const activeTab = ref('all')
const sortBy = ref('appointment_time')
const sortOrder = ref('asc')
const detailVisible = ref(false)
const currentItem = ref(null)
const bookingWithApplications = ref(new Set()) // 存储已有申请的booking_id

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

// 加载已有申请的booking状态
async function loadApplicationStatus() {
  try {
    // 获取所有已完成的booking
    const completedBookings = bookings.value.filter(b => b.status === 'completed')
    if (completedBookings.length === 0) return
    
    // 清空之前的记录
    bookingWithApplications.value.clear()
    
    // 获取当前用户的所有合约申请
    const applications = await request.get('/api/v1/contract-applications/', {
      params: { skip: 0, limit: 100 } // 获取足够多的申请
    })
    
    // 检查每个booking是否已有申请
    for (const booking of completedBookings) {
      const hasApplication = applications.some(app => app.booking_id === booking.id)
      if (hasApplication) {
        bookingWithApplications.value.add(booking.id)
      }
    }
  } catch (e) {
    console.error('加载申请状态失败:', e)
  }
}

async function loadData() {
  loading.value = true
  try {
    const params = { 
      skip: (currentPage.value - 1) * pageSize.value, 
      limit: pageSize.value,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }
    
    // 未来日程：后端筛选已同意状态，前端再按时间过滤
    if (activeTab.value === 'upcoming') {
      const res = await getBookings({ status: 'approved', skip: 0, limit: 100, sort_by: sortBy.value, sort_order: sortOrder.value })
      const allBookings = Array.isArray(res) ? res : []
      const now = new Date()
      bookings.value = allBookings.filter(b => new Date(b.appointment_time) > now)
      total.value = bookings.value.length
      return
    }
    
    // 已结束：显示已完成的预约
    if (activeTab.value === 'ended') {
      const res = await getBookings({ ...params, status: 'completed' })
      bookings.value = Array.isArray(res) ? res : []
      total.value = bookings.value.length
      await loadApplicationStatus()
      return
    }
    
    // 其他标签页按原逻辑处理
    if (activeTab.value !== 'all') {
      params.status = activeTab.value
    } else {
      // "全部"展示所有记录，不做分页
      params.limit = 9999
      params.skip = 0
    }
    const res = await getBookings(params)
    bookings.value = Array.isArray(res) ? res : []
    total.value = Array.isArray(res) ? res.length : 0
    await loadApplicationStatus()
  } catch (e) {
    ElMessage.error('加载预约列表失败')
  } finally {
    loading.value = false
  }
}

async function handleRequestContract(row) {
  try {
    await ElMessageBox.confirm(
      '系统将根据房源信息自动生成合同（租金、押金从房源信息获取），确认申请？',
      '申请签约',
      { type: 'info' }
    )
  } catch {
    return
  }
  try {
    await autoCreateContract({ property_id: row.property_id })
    ElMessage.success('合同已自动创建，请前往"我的合同"签署')
    setTimeout(() => router.push('/tenant/contracts'), 1500)
  } catch (e) {
    const msg = e.response?.data?.detail || '创建合同失败'
    ElMessage.error(msg)
  }
}

async function handleComplete(row) {
  try {
    await ElMessageBox.confirm('确认已完成线下看房？', '提示', { type: 'info' })
  } catch {
    return
  }
  try {
    await completeBooking(row.id)
    ElMessage.success('已标记为完成，现在可以发起合约申请')
    row.status = 'completed'
    row.updated_at = new Date().toISOString()
    // 如果当前在「未来日程」tab，移除已完成的记录
    if (activeTab.value === 'upcoming') {
      const idx = bookings.value.findIndex(b => b.id === row.id)
      if (idx !== -1) { bookings.value.splice(idx, 1); total.value = Math.max(0, total.value - 1) }
    }
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function handleCancel(row) {
  try {
    await ElMessageBox.confirm('确定取消此预约？', '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await updateBooking(row.id, { status: 'cancelled', cancel_reason: '租客主动取消' })
    ElMessage.success('已取消')
    row.status = 'cancelled'
    row.cancel_reason = '租客主动取消'
    row.updated_at = new Date().toISOString()
    // 当前在筛选tab且新状态不匹配时，从列表移除
    if (!['all', 'cancelled'].includes(activeTab.value)) {
      const idx = bookings.value.findIndex(b => b.id === row.id)
      if (idx !== -1) { bookings.value.splice(idx, 1); total.value = Math.max(0, total.value - 1) }
    }
  } catch (e) {
    ElMessage.error('取消预约失败')
  }
}

async function handleAcceptReschedule(row) {
  try {
    await ElMessageBox.confirm('同意房东的改期建议？', '提示', { type: 'info' })
  } catch {
    return
  }
  try {
    await respondReschedule(row.id, { response: 'accept' })
    ElMessage.success('已同意改期')
    row.status = 'approved'
    row.updated_at = new Date().toISOString()
    // 当前在「待协商」tab时，移除该记录
    if (activeTab.value === 'negotiating') {
      const idx = bookings.value.findIndex(b => b.id === row.id)
      if (idx !== -1) { bookings.value.splice(idx, 1); total.value = Math.max(0, total.value - 1) }
    }
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function handleRejectReschedule(row) {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因（可选）', '拒绝改期', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPlaceholder: '拒绝原因',
    })
    await respondReschedule(row.id, { response: 'reject', message: value || '' })
    ElMessage.success('已拒绝改期')
    row.status = 'pending'
    row.updated_at = new Date().toISOString()
    // 当前在「待协商」tab时，移除该记录
    if (activeTab.value === 'negotiating') {
      const idx = bookings.value.findIndex(b => b.id === row.id)
      if (idx !== -1) { bookings.value.splice(idx, 1); total.value = Math.max(0, total.value - 1) }
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

function viewDetail(row) {
  currentItem.value = row
  detailVisible.value = true
}

async function showContractApplicationDialog(row) {
  try {
    await ElMessageBox.confirm(
      '看房已完成，是否现在发起合约申请？\n\n系统将自动使用房源的租金和押金信息生成合同草稿，提交后房东审核通过即可开始签署流程。',
      '发起合约申请',
      { 
        confirmButtonText: '确认申请',
        cancelButtonText: '取消',
        type: 'info',
        distinguishCancelAndClose: true
      }
    )
  } catch {
    return
  }
  
  try {
    // 直接调用API创建合约申请，使用默认参数
    await request.post('/api/v1/contract-applications/', {
      booking_id: row.id,
      start_date: new Date().toISOString(), // 使用当前日期作为开始日期
      end_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(), // 默认一年
      payment_method: '押一付三', // 默认付款方式
      additional_notes: ''
    })
    
    ElMessage.success('合约申请提交成功，请等待房东处理')
    
    // 更新本地状态，隐藏按钮
    bookingWithApplications.value.add(row.id)
  } catch (e) {
    const msg = e.response?.data?.detail || '提交失败，请稍后重试'
    ElMessage.error(msg)
  }
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
