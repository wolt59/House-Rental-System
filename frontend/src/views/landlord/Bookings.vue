<template>
  <div class="page-container">
    <div class="page-header"><h2>预约管理</h2></div>
    <el-table :data="bookings" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="租客" width="100">
        <template #default="{ row }">用户#{{ row.tenant_id }}</template>
      </el-table-column>
      <el-table-column label="房源" width="120">
        <template #default="{ row }">房源#{{ row.property_id }}</template>
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
          <el-button v-if="row.status === 'approved'" type="success" size="small" @click="handleAction(row, 'completed')">完成</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getBookings, updateBooking } from '../../api/booking'
import { ElMessage } from 'element-plus'

const bookings = ref([])
const loading = ref(false)

const statusMap = { pending: '待确认', approved: '已确认', rejected: '已拒绝', cancelled: '已取消', completed: '已完成' }
const statusTypeMap = { pending: 'warning', approved: 'success', rejected: 'danger', cancelled: 'info', completed: '' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function formatDate(d) { return d ? new Date(d).toLocaleString('zh-CN') : '' }

async function loadData() {
  loading.value = true
  try {
    const res = await getBookings({ limit: 50 })
    bookings.value = Array.isArray(res) ? res : []
  } catch (e) {} finally {
    loading.value = false
  }
}

async function handleAction(row, status) {
  try {
    await updateBooking(row.id, { status })
    ElMessage.success('操作成功')
    loadData()
  } catch (e) {}
}

onMounted(loadData)
</script>
