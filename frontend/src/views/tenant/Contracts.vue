<template>
  <div class="page-container">
    <div class="page-header"><h2>我的合同</h2></div>
    <el-table :data="contracts" stripe v-loading="loading">
      <el-table-column prop="contract_no" label="合同编号" width="200" />
      <el-table-column label="房源" width="120">
        <template #default="{ row }">房源 #{{ row.property_id }}</template>
      </el-table-column>
      <el-table-column label="租期" width="220">
        <template #default="{ row }">{{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}</template>
      </el-table-column>
      <el-table-column label="月租金" width="100">
        <template #default="{ row }">¥{{ row.monthly_rent }}</template>
      </el-table-column>
      <el-table-column label="状态" width="140">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending_sign' || row.status === 'pending_tenant_sign'" type="primary" size="small" @click="handleSign(row)">签约</el-button>
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && contracts.length === 0" description="暂无数据" />

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <el-dialog v-model="detailVisible" title="合同详情" width="600px">
      <el-descriptions :column="2" border v-if="currentContract">
        <el-descriptions-item label="合同编号">{{ currentContract.contract_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(currentContract.status) }}</el-descriptions-item>
        <el-descriptions-item label="月租金">¥{{ currentContract.monthly_rent }}</el-descriptions-item>
        <el-descriptions-item label="押金">{{ currentContract.deposit ? '¥' + currentContract.deposit : '-' }}</el-descriptions-item>
        <el-descriptions-item label="开始日期">{{ formatDate(currentContract.start_date) }}</el-descriptions-item>
        <el-descriptions-item label="结束日期">{{ formatDate(currentContract.end_date) }}</el-descriptions-item>
        <el-descriptions-item label="房东签约">{{ currentContract.signed_by_landlord ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="租客签约">{{ currentContract.signed_by_tenant ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="合同条款" :span="2">{{ currentContract.terms || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getContracts, signContractTenant } from '../../api/contract'
import { ElMessage, ElMessageBox } from 'element-plus'

const contracts = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const detailVisible = ref(false)
const currentContract = ref(null)

const statusMap = { pending_sign: '待签约', pending_tenant_sign: '待租客签约', pending_landlord_sign: '待房东签约', active: '生效中', terminated: '已终止', expired: '已过期' }
const statusTypeMap = { pending_sign: 'warning', pending_tenant_sign: 'warning', pending_landlord_sign: 'info', active: 'success', terminated: 'danger', expired: 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function formatDate(d) { return d ? new Date(d).toLocaleDateString('zh-CN') : '' }

async function loadData() {
  loading.value = true
  try {
    const res = await getContracts({ skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value })
    contracts.value = Array.isArray(res) ? res : []
    total.value = Array.isArray(res) ? res.length : 0
  } catch (e) {
    ElMessage.error('加载合同列表失败')
  } finally {
    loading.value = false
  }
}

async function handleSign(row) {
  try {
    await ElMessageBox.confirm('确定签署此合同？', '确认签约', { type: 'warning' })
  } catch {
    return // 用户取消操作
  }
  try {
    await signContractTenant(row.id)
    ElMessage.success('签约成功')
    loadData()
  } catch (e) {
    ElMessage.error('签约失败')
  }
}

function viewDetail(row) {
  currentContract.value = row
  detailVisible.value = true
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
</style>
