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
        <template #default="{ row }">{{ row.user_id ? '用户#' + row.user_id : '系统' }}</template>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getAuditLogs } from '../../api/stats'

const logs = ref([])
const loading = ref(false)
const filters = reactive({ action: '', target_type: '', ip_address: '' })

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
    const params = { limit: 50 }
    if (filters.action) params.action = filters.action
    if (filters.target_type) params.target_type = filters.target_type
    if (filters.ip_address) params.ip_address = filters.ip_address
    const res = await getAuditLogs(params)
    logs.value = Array.isArray(res) ? res : []
  } catch (e) {} finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
