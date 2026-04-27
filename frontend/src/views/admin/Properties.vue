<template>
  <div class="page-container">
    <div class="page-header"><h2>房源审核</h2></div>
    <el-form :inline="true" :model="filters" style="margin-bottom: 16px">
      <el-form-item label="审核状态">
        <el-select v-model="filters.review_status" clearable placeholder="全部" @change="loadData">
          <el-option label="待审核" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
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
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button v-if="row.review_status === 'pending'" type="success" size="small" @click="handleReview(row, 'approved')">通过</el-button>
          <el-button v-if="row.review_status === 'pending'" type="danger" size="small" @click="handleReview(row, 'rejected')">拒绝</el-button>
          <el-button size="small" @click="changeStatus(row)">改状态</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getProperties, reviewProperty, changePropertyStatus } from '../../api/property'
import { ElMessage, ElMessageBox } from 'element-plus'

const properties = ref([])
const loading = ref(false)
const filters = reactive({ review_status: '' })

const reviewMap = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
const reviewTypeMap = { pending: 'warning', approved: 'success', rejected: 'danger' }
const statusMap = { vacant: '空置', rented: '已出租', maintenance: '维修中' }
const statusTypeMap = { vacant: 'success', rented: 'warning', maintenance: 'danger' }
function reviewLabel(s) { return reviewMap[s] || s }
function reviewType(s) { return reviewTypeMap[s] || 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }

async function loadData() {
  loading.value = true
  try {
    const params = { limit: 50 }
    if (filters.review_status) params.review_status = filters.review_status
    else params.review_status = undefined
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

async function changeStatus(row) {
  try {
    const { value } = await ElMessageBox.prompt('请输入新状态（vacant/rented/maintenance）', '修改房源状态', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /^(vacant|rented|maintenance)$/,
      inputErrorMessage: '请输入 vacant、rented 或 maintenance',
    })
    await changePropertyStatus(row.id, { status: value })
    ElMessage.success('状态已更新')
    loadData()
  } catch (e) {}
}

onMounted(loadData)
</script>
