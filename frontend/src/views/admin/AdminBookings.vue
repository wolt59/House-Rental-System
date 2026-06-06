<template>
  <div class="page-container">
    <div class="page-header">
      <h2>预约管理</h2>
    </div>

    <el-tabs v-model="activeTab" @tab-change="loadData">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="待处理" name="pending" />
      <el-tab-pane label="已通过" name="approved" />
      <el-tab-pane label="已完成" name="completed" />
      <el-tab-pane label="已拒绝" name="rejected" />
      <el-tab-pane label="协商中" name="negotiating" />
    </el-tabs>

    <el-table :data="bookings" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="租客" width="100" show-overflow-tooltip>
        <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="房源" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="预约时间" min-width="170">
        <template #default="{ row }">{{ formatDate(row.appointment_time) }}</template>
      </el-table-column>
      <el-table-column label="备注" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">{{ row.note || '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" align="center">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && bookings.length === 0" description="暂无预约数据" />

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="预约详情" width="600px">
      <el-descriptions :column="2" border v-if="currentItem">
        <el-descriptions-item label="租客">{{ userNames[currentItem.tenant_id] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房源" :span="2">
          {{ propertyNames[currentItem.property_id] || '-' }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentItem.tenant" label="租客电话">
          {{ currentItem.tenant.phone || '-' }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentItem.tenant" label="租客邮箱">
          {{ currentItem.tenant.email || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="预约时间">{{ formatDate(currentItem.appointment_time) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(currentItem.status) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ currentItem.note || '-' }}</el-descriptions-item>
        <el-descriptions-item label="拒绝原因" :span="2" v-if="currentItem.reject_reason">
          <span style="color: #f56c6c">{{ currentItem.reject_reason }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="改期建议" :span="2" v-if="currentItem.reschedule_proposal">
          {{ currentItem.reschedule_proposal }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(currentItem.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDateTime(currentItem.updated_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getBookings } from '../../api/booking'
import { ElMessage } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'

const bookings = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(15)
const currentPage = ref(1)
const activeTab = ref('all')
const detailVisible = ref(false)
const currentItem = ref(null)

const { resolveItems, userNames, propertyNames } = useNameResolver()

const statusMap = {
  pending: '待确认',
  approved: '已通过',
  rejected: '已拒绝',
  completed: '已完成',
  cancelled: '已取消',
  negotiating: '协商中',
}
const statusTypeMap = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  completed: 'info',
  cancelled: 'info',
  negotiating: 'warning',
}

function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function formatDate(d) { return d ? new Date(d).toLocaleString('zh-CN') : '-' }
function formatDateTime(d) { return d ? new Date(d).toLocaleString('zh-CN') : '-' }

async function loadData() {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    if (activeTab.value !== 'all') {
      params.status = activeTab.value
    }
    const res = await getBookings(params)
    bookings.value = res.items || []
    await resolveItems(bookings.value, ['tenant_id'])
    total.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载预约列表失败')
  } finally {
    loading.value = false
  }
}

function viewDetail(row) {
  currentItem.value = row
  detailVisible.value = true
}

onMounted(loadData)
</script>

<style scoped>
.page-header {
  margin-bottom: 8px;
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
