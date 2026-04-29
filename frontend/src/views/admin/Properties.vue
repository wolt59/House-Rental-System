<template>
  <div class="page-container">
    <div class="page-header"><h2>房源管理</h2></div>
    <el-form :inline="true" :model="filters" style="margin-bottom: 16px">
      <el-form-item label="审核状态">
        <el-select v-model="filters.review_status" clearable placeholder="全部" @change="loadData">
          <el-option label="待审核" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
      </el-form-item>
      <el-form-item label="房源状态">
        <el-select v-model="filters.status" clearable placeholder="全部" @change="loadData">
          <el-option label="空置" value="vacant" />
          <el-option label="已出租" value="rented" />
          <el-option label="维修中" value="maintenance" />
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
      <el-table-column prop="title" label="标题" width="200" />
      <el-table-column prop="address" label="地址" />
      <el-table-column label="房东" width="100">
        <template #default="{ row }">用户#{{ row.owner_id }}</template>
      </el-table-column>
      <el-table-column label="租金" width="100">
        <template #default="{ row }">¥{{ row.rent }}/月</template>
      </el-table-column>
      <el-table-column label="审核状态" width="100">
        <template #default="{ row }">
          <el-tag :type="reviewType(row.review_status)" size="small">{{ reviewLabel(row.review_status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="房源状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260">
        <template #default="{ row }">
          <el-button v-if="row.review_status === 'pending'" type="success" size="small" @click="handleReview(row, 'approved')">通过</el-button>
          <el-button v-if="row.review_status === 'pending'" type="danger" size="small" @click="handleReview(row, 'rejected')">拒绝</el-button>
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="detailVisible" title="房源详情" width="600px">
      <el-descriptions :column="2" border v-if="currentProperty">
        <el-descriptions-item label="标题">{{ currentProperty.title }}</el-descriptions-item>
        <el-descriptions-item label="地址">{{ currentProperty.address }}</el-descriptions-item>
        <el-descriptions-item label="租金">¥{{ currentProperty.rent }}/月</el-descriptions-item>
        <el-descriptions-item label="面积">{{ currentProperty.area }}㎡</el-descriptions-item>
        <el-descriptions-item label="户型">{{ currentProperty.floor_plan }}</el-descriptions-item>
        <el-descriptions-item label="房东">用户#{{ currentProperty.owner_id }}</el-descriptions-item>
        <el-descriptions-item label="审核状态">{{ reviewLabel(currentProperty.review_status) }}</el-descriptions-item>
        <el-descriptions-item label="房源状态">{{ statusLabel(currentProperty.status) }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentProperty.description || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getProperties, reviewProperty, deleteProperty } from '../../api/property'
import { ElMessage, ElMessageBox } from 'element-plus'

const properties = ref([])
const loading = ref(false)
const detailVisible = ref(false)
const currentProperty = ref(null)
const filters = reactive({ review_status: '', status: '', keyword: '' })

const reviewMap = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
const reviewTypeMap = { pending: 'warning', approved: 'success', rejected: 'danger' }
const statusMap = { vacant: '空置', rented: '已出租', maintenance: '维修中' }
const statusTypeMap = { vacant: 'success', rented: 'warning', maintenance: 'danger' }
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
    const params = { limit: 50 }
    if (filters.review_status) params.review_status = filters.review_status
    if (filters.status) params.status = filters.status
    if (filters.keyword) params.keyword = filters.keyword
    const res = await getProperties(params)
    properties.value = Array.isArray(res) ? res : []
  } catch (e) {} finally {
    loading.value = false
  }
}

async function handleReview(row, reviewStatus) {
  try {
    const comment = reviewStatus === 'rejected'
      ? (await ElMessageBox.prompt('请输入拒绝原因', '拒绝审核', { confirmButtonText: '确定', cancelButtonText: '取消' })).value
      : ''
    await reviewProperty(row.id, { review_status: reviewStatus, comment })
    ElMessage.success(reviewStatus === 'approved' ? '已通过' : '已拒绝')
    loadData()
  } catch (e) {}
}

function viewDetail(row) {
  currentProperty.value = row
  detailVisible.value = true
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除该房源？此操作不可恢复', '确认删除', { type: 'warning' })
    await deleteProperty(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {}
}

onMounted(loadData)
</script>
