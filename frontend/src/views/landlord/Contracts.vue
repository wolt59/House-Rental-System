<template>
  <div class="page-container">
    <div class="page-header">
      <h2>合同管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">创建合同</el-button>
    </div>
    <el-table :data="contracts" stripe v-loading="loading">
      <el-table-column prop="contract_no" label="合同编号" width="200" />
      <el-table-column label="房源" width="100">
        <template #default="{ row }">房源#{{ row.property_id }}</template>
      </el-table-column>
      <el-table-column label="租客" width="100">
        <template #default="{ row }">用户#{{ row.tenant_id }}</template>
      </el-table-column>
      <el-table-column label="月租金" width="100">
        <template #default="{ row }">¥{{ row.monthly_rent }}</template>
      </el-table-column>
      <el-table-column label="状态" width="140">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending_sign' || row.status === 'pending_landlord_sign'" type="primary" size="small" @click="handleSign(row)">签约</el-button>
          <el-button v-if="row.status === 'active'" type="danger" size="small" @click="handleTerminate(row)">终止</el-button>
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreateDialog" title="创建合同" width="600px">
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="房源ID"><el-input v-model.number="createForm.property_id" /></el-form-item>
        <el-form-item label="租客ID"><el-input v-model.number="createForm.tenant_id" /></el-form-item>
        <el-form-item label="开始日期"><el-date-picker v-model="createForm.start_date" type="date" style="width: 100%" /></el-form-item>
        <el-form-item label="结束日期"><el-date-picker v-model="createForm.end_date" type="date" style="width: 100%" /></el-form-item>
        <el-form-item label="月租金"><el-input v-model="createForm.monthly_rent" /></el-form-item>
        <el-form-item label="押金"><el-input v-model="createForm.deposit" /></el-form-item>
        <el-form-item label="缴费日"><el-input v-model.number="createForm.payment_day" placeholder="1-28" /></el-form-item>
        <el-form-item label="合同条款"><el-input v-model="createForm.terms" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

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
import { ref, reactive, onMounted } from 'vue'
import { getContracts, createContract, signContractLandlord, terminateContract } from '../../api/contract'
import { ElMessage, ElMessageBox } from 'element-plus'

const contracts = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const detailVisible = ref(false)
const creating = ref(false)
const currentContract = ref(null)
const createForm = reactive({ property_id: '', tenant_id: '', start_date: '', end_date: '', monthly_rent: '', deposit: '', payment_day: '', terms: '' })

const statusMap = { pending_sign: '待签约', pending_tenant_sign: '待租客签约', pending_landlord_sign: '待房东签约', active: '生效中', terminated: '已终止', expired: '已过期' }
const statusTypeMap = { pending_sign: 'warning', pending_tenant_sign: 'warning', pending_landlord_sign: 'info', active: 'success', terminated: 'danger', expired: 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function formatDate(d) { return d ? new Date(d).toLocaleDateString('zh-CN') : '' }

async function loadData() {
  loading.value = true
  try {
    const res = await getContracts({ limit: 50 })
    contracts.value = Array.isArray(res) ? res : []
  } catch (e) {} finally {
    loading.value = false
  }
}

async function handleCreate() {
  creating.value = true
  try {
    const data = { ...createForm }
    data.monthly_rent = parseFloat(data.monthly_rent)
    if (data.deposit) data.deposit = parseFloat(data.deposit)
    if (data.start_date) data.start_date = new Date(data.start_date).toISOString()
    if (data.end_date) data.end_date = new Date(data.end_date).toISOString()
    await createContract(data)
    ElMessage.success('合同已创建')
    showCreateDialog.value = false
    loadData()
  } catch (e) {} finally {
    creating.value = false
  }
}

async function handleSign(row) {
  try {
    await ElMessageBox.confirm('确定签署此合同？', '确认签约')
    await signContractLandlord(row.id)
    ElMessage.success('签约成功')
    loadData()
  } catch (e) {}
}

async function handleTerminate(row) {
  try {
    await ElMessageBox.confirm('确定终止此合同？', '确认终止', { type: 'warning' })
    await terminateContract(row.id)
    ElMessage.success('合同已终止')
    loadData()
  } catch (e) {}
}

function viewDetail(row) {
  currentContract.value = row
  detailVisible.value = true
}

onMounted(loadData)
</script>
