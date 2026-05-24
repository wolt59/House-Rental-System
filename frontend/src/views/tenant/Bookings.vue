<template>
  <div class="page-container">
    <div class="page-header"><h2>我的预约</h2></div>
    <el-table :data="bookings" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="房源" width="200">
        <template #default="{ row }">房源 #{{ row.property_id }}</template>
      </el-table-column>
      <el-table-column label="预约时间" width="170">
        <template #default="{ row }">{{ formatDate(row.appointment_time) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="note" label="备注" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button v-if="row.status === 'approved'" type="primary" size="small" @click="handleRequestContract(row)">申请签约</el-button>
          <el-button v-if="row.status === 'pending'" type="danger" size="small" @click="handleCancel(row)">取消</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && bookings.length === 0" description="暂无数据" />
    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getBookings, updateBooking } from '../../api/booking'
import { autoCreateContract } from '../../api/contract'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const bookings = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)

const statusMap = { pending: '待确认', approved: '已确认', rejected: '已拒绝', cancelled: '已取消', completed: '已完成' }
const statusTypeMap = { pending: 'warning', approved: 'success', rejected: 'danger', cancelled: 'info', completed: 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function formatDate(d) { return d ? new Date(d).toLocaleString('zh-CN') : '' }

async function loadData() {
  loading.value = true
  try {
    const res = await getBookings({ skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value })
    bookings.value = Array.isArray(res) ? res : []
    total.value = Array.isArray(res) ? res.length : 0
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
    const res = await autoCreateContract({ property_id: row.property_id })
    ElMessage.success('合同已自动创建，请前往"我的合同"签署')
    loadData()
    setTimeout(() => router.push('/tenant/contracts'), 1500)
  } catch (e) {
    const msg = e.response?.data?.detail || '创建合同失败'
    ElMessage.error(msg)
  }
}

async function handleCancel(row) {
  try {
    await ElMessageBox.confirm('确定取消此预约？', '提示', { type: 'warning' })
  } catch {
    return // 用户取消操作
  }
  try {
    await updateBooking(row.id, { status: 'cancelled', cancel_reason: '租客主动取消' })
    ElMessage.success('已取消')
    loadData()
  } catch (e) {
    ElMessage.error('取消预约失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
</style>
