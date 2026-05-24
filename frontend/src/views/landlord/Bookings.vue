<template>
  <div class="page-container">
    <div class="page-header"><h2>预约管理</h2></div>
    <el-table :data="bookings" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="租客" width="100">
        <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="房源" width="120">
        <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
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
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" type="success" size="small" @click="handleAction(row, 'approved')">确认</el-button>
          <el-button v-if="row.status === 'pending'" type="danger" size="small" @click="handleAction(row, 'rejected')">拒绝</el-button>
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
import { ElMessage } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'

const { resolveItems, userNames, propertyNames } = useNameResolver()

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
    await resolveItems(bookings.value, ['tenant_id', 'property_id'])
    total.value = Array.isArray(res) ? res.length : 0
  } catch (e) { ElMessage.error('加载预约列表失败') } finally {
    loading.value = false
  }
}

async function handleAction(row, status) {
  try {
    await updateBooking(row.id, { status })
    ElMessage.success('操作成功')
    loadData()
  } catch (e) { ElMessage.error('操作失败') }
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
</style>
