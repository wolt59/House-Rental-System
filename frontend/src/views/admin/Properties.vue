<template>
  <div class="page-container">
    <div class="page-header"><h2>房源管理</h2></div>
    <el-form :inline="true" :model="filters" style="margin-bottom: 16px">
      <el-form-item label="审核状态">
        <el-select v-model="filters.review_status" clearable placeholder="全部" style="width: 130px" @change="loadData">
          <el-option label="草稿" value="draft" />
          <el-option label="待审核" value="pending" />
          <el-option label="审核中" value="reviewing" />
          <el-option label="已通过" value="approved" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
      </el-form-item>
      <el-form-item label="房源状态">
        <el-select v-model="filters.status" clearable placeholder="全部" style="width: 130px" @change="loadData">
          <el-option label="已发布" value="published" />
          <el-option label="未发布" value="unpublished" />
          <el-option label="已出租" value="rented" />
        </el-select>
      </el-form-item>
      <el-form-item label="搜索">
        <el-input v-model="filters.keyword" placeholder="标题/地址" clearable @keyup.enter="loadData" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadData">搜索</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>
    <el-table :data="properties" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="标题" min-width="150" show-overflow-tooltip />
      <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
      <el-table-column label="房东" min-width="100" show-overflow-tooltip>
        <template #default="{ row }">{{ userNames[row.owner_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="租金" width="100" align="right">
        <template #default="{ row }">¥{{ row.rent }}/月</template>
      </el-table-column>
      <el-table-column label="审核状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="reviewType(row.review_status)" size="small">{{ reviewLabel(row.review_status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="房源状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="320" align="center">
        <template #default="{ row }">
          <el-button v-if="row.review_status === 'pending' || row.review_status === 'reviewing'" 
                     type="success" size="small" @click="handleReview(row, 'approved')">通过</el-button>
          <el-button v-if="row.review_status === 'pending' || row.review_status === 'reviewing'" 
                     type="danger" size="small" @click="handleReview(row, 'rejected')">拒绝</el-button>
          <el-button v-if="row.review_status === 'approved' && row.status === 'published'" 
                     type="warning" size="small" @click="handleAdminUnpublish(row)">下架</el-button>
          <el-button v-if="row.review_status === 'approved' && row.status === 'unpublished'" 
                     type="success" size="small" @click="handleAdminRepublish(row)">恢复发布</el-button>
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && properties.length === 0" description="暂无数据" />

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <el-dialog v-model="detailVisible" title="房源详情" width="600px">
      <el-descriptions :column="2" border v-if="currentProperty">
        <el-descriptions-item label="标题">{{ currentProperty.title }}</el-descriptions-item>
        <el-descriptions-item label="地址">{{ currentProperty.address }}</el-descriptions-item>
        <el-descriptions-item label="租金">¥{{ currentProperty.rent }}/月</el-descriptions-item>
        <el-descriptions-item label="面积">{{ currentProperty.area }}㎡</el-descriptions-item>
        <el-descriptions-item label="户型">{{ currentProperty.floor_plan }}</el-descriptions-item>
        <el-descriptions-item label="房东">{{ userNames[currentProperty.owner_id] || '加载中...' }}</el-descriptions-item>
        <el-descriptions-item label="审核状态">{{ reviewLabel(currentProperty.review_status) }}</el-descriptions-item>
        <el-descriptions-item label="房源状态">{{ statusLabel(currentProperty.status) }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentProperty.description || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getProperties, reviewProperty, unpublishProperty, republishProperty, deleteProperty } from '../../api/property'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'

const properties = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const detailVisible = ref(false)
const currentProperty = ref(null)
const filters = reactive({ review_status: '', status: '', keyword: '' })
const { resolveItems, userNames, propertyNames } = useNameResolver()

const reviewMap = { draft: '草稿', pending: '待审核', reviewing: '审核中', approved: '已通过', rejected: '已拒绝' }
const reviewTypeMap = { draft: 'info', pending: 'warning', reviewing: 'primary', approved: 'success', rejected: 'danger' }
const statusMap = { published: '已发布', unpublished: '未发布', rented: '已出租' }
const statusTypeMap = { published: 'success', unpublished: 'info', rented: 'warning' }
function reviewLabel(s) { return reviewMap[s] || s }
function reviewType(s) { return reviewTypeMap[s] || 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }

function resetFilters() {
  filters.review_status = ''
  filters.status = ''
  filters.keyword = ''
  loadData()
}

async function loadData() {
  loading.value = true
  try {
    const params = { skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value }
    if (filters.review_status) params.review_status = filters.review_status
    if (filters.status) params.status = filters.status
    if (filters.keyword) params.keyword = filters.keyword
    const res = await getProperties(params)
    properties.value = res.items || []
    if (properties.value.length) await resolveItems(properties.value, ['owner_id'])
    total.value = res.total || 0
  } catch (e) { ElMessage.error('加载房源列表失败') } finally {
    loading.value = false
  }
}

async function handleReview(row, reviewStatus) {
  let comment = ''
  if (reviewStatus === 'rejected') {
    try {
      const result = await ElMessageBox.prompt('请输入拒绝原因', '拒绝审核', { confirmButtonText: '确定', cancelButtonText: '取消' })
      comment = result.value
    } catch {
      return // 用户取消
    }
  }
  try {
    await reviewProperty(row.id, { review_status: reviewStatus, comment })
    ElMessage.success(reviewStatus === 'approved' ? '已通过' : '已拒绝')
    loadData()
  } catch (e) {
    ElMessage.error('审核操作失败')
  }
}

function viewDetail(row) {
  currentProperty.value = row
  detailVisible.value = true
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除该房源？此操作不可恢复', '确认删除', { type: 'warning' })
  } catch {
    return // 用户取消
  }
  try {
    await deleteProperty(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {
    ElMessage.error('删除房源失败')
  }
}

async function handleAdminUnpublish(row) {
  try {
    const result = await ElMessageBox.prompt('请输入下架原因', '下架房源', { 
      confirmButtonText: '确定', 
      cancelButtonText: '取消',
      inputPattern: /.+/,
      inputErrorMessage: '请输入下架原因'
    })
    await unpublishProperty(row.id, { reason: result.value })
    ElMessage.success('已下架')
    loadData()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }
}

async function handleAdminRepublish(row) {
  try {
    await republishProperty(row.id)
    ElMessage.success('已恢复发布')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }

/* 让表格占满容器宽度 */
:deep(.el-table) {
  width: 100% !important;
}

:deep(.el-table__inner-wrapper) {
  width: 100% !important;
}
</style>
