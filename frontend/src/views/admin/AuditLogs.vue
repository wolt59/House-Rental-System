<template>
  <div class="page-container">
    <div class="page-header"><h2>审计日志</h2></div>
    <el-form :inline="true" :model="filters" style="margin-bottom: 16px">
      <el-form-item label="操作类型">
        <el-input v-model="filters.action" placeholder="如：user_login" clearable />
      </el-form-item>
      <el-form-item label="对象类型">
        <el-input v-model="filters.target_type" placeholder="如：user" clearable />
      </el-form-item>
      <el-form-item label="IP地址">
        <el-input v-model="filters.ip_address" placeholder="IP" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadData">搜索</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>
    <el-table :data="logs" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="操作用户" width="100">
        <template #default="{ row }">{{ row.user_id ? (userNames[row.user_id] || '加载中...') : '系统' }}</template>
      </el-table-column>
      <el-table-column prop="action" label="操作" width="160" />
      <el-table-column prop="target_type" label="对象类型" width="120" />
      <el-table-column label="对象ID" width="80">
        <template #default="{ row }">{{ row.target_id || '-' }}</template>
      </el-table-column>
      <el-table-column prop="detail" label="详情" />
      <el-table-column prop="ip_address" label="IP" width="130" />
      <el-table-column label="时间" width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && logs.length === 0" description="暂无数据" />

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getAuditLogs } from '../../api/stats'
import { ElMessage } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'

const logs = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const filters = reactive({ action: '', target_type: '', ip_address: '' })
const { resolveItems, userNames } = useNameResolver()

function formatDate(d) { return d ? new Date(d).toLocaleString('zh-CN') : '' }

function resetFilters() {
  filters.action = ''
  filters.target_type = ''
  filters.ip_address = ''
  loadData()
}

async function loadData() {
  loading.value = true
  try {
    const params = { skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value }
    if (filters.action) params.action = filters.action
    if (filters.target_type) params.target_type = filters.target_type
    if (filters.ip_address) params.ip_address = filters.ip_address
    const res = await getAuditLogs(params)
    logs.value = Array.isArray(res) ? res : []
    if (logs.value.length) await resolveItems(logs.value, ['user_id'])
    total.value = Array.isArray(res) ? res.length : 0
  } catch (e) { ElMessage.error('加载审计日志失败') } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
</style>
