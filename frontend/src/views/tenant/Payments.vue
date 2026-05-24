<template>
  <div class="page-container">
    <div class="page-header">
      <h2>租金支付</h2>
      <el-button v-if="contracts.length" type="primary" @click="showCreateDialog = true">缴纳租金</el-button>
    </div>
    <el-table :data="payments" stripe v-loading="loading">
      <el-table-column prop="payment_no" label="支付单号" width="220" />
      <el-table-column label="金额" width="100">
        <template #default="{ row }">¥{{ row.amount }}</template>
      </el-table-column>
      <el-table-column label="支付方式" width="100">
        <template #default="{ row }">{{ methodLabel(row.payment_method) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="应缴日期" width="120">
        <template #default="{ row }">{{ formatDate(row.due_date) }}</template>
      </el-table-column>
      <el-table-column label="实缴日期" width="120">
        <template #default="{ row }">{{ formatDate(row.paid_at) }}</template>
      </el-table-column>
      <el-table-column label="逾期天数" width="90">
        <template #default="{ row }">{{ row.overdue_days || 0 }}天</template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" type="primary" size="small" @click="handlePay(row)">支付</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && payments.length === 0" description="暂无数据" />
    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <el-dialog v-model="showCreateDialog" title="缴纳租金" width="480px">
      <el-form ref="createFormRef" :model="createForm" label-width="90px" :rules="createRules">
        <el-form-item label="合同" prop="contract_id">
          <el-select v-model="createForm.contract_id" placeholder="选择合同" style="width: 100%" @change="onContractChange">
            <el-option v-for="c in contracts" :key="c.id" :label="`${c.contract_no || '#'+c.id} - ¥${c.monthly_rent}/月`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额" prop="amount">
          <el-input v-model.number="createForm.amount" type="number" />
        </el-form-item>
        <el-form-item label="支付方式" prop="payment_method">
          <el-select v-model="createForm.payment_method" placeholder="选择方式" style="width: 100%">
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信" value="wechat" />
            <el-option label="银行转账" value="bank" />
            <el-option label="现金" value="cash" />
          </el-select>
        </el-form-item>
        <el-form-item label="应缴日期" prop="due_date">
          <el-date-picker v-model="createForm.due_date" type="date" placeholder="选择日期" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreatePayment">确认支付</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getPayments, createPayment, updatePayment } from '../../api/payment'
import { getContracts } from '../../api/contract'
import { ElMessage, ElMessageBox } from 'element-plus'

const payments = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)

const showCreateDialog = ref(false)
const creating = ref(false)
const contracts = ref([])
const createFormRef = ref(null)
const createForm = reactive({ contract_id: '', amount: '', payment_method: '', due_date: '' })
const createRules = {
  contract_id: [{ required: true, message: '请选择合同', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
  payment_method: [{ required: true, message: '请选择支付方式', trigger: 'change' }],
}

function onContractChange(val) {
  const c = contracts.value.find(c => c.id === val)
  if (c) createForm.amount = c.monthly_rent
}

const statusMap = { pending: '待支付', paid: '已支付', overdue: '逾期', cancelled: '已取消', refunded: '已退款' }
const statusTypeMap = { pending: 'warning', paid: 'success', overdue: 'danger', cancelled: 'info', refunded: 'info' }
const methodMap = { alipay: '支付宝', wechat: '微信', bank: '银行转账', cash: '现金' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function methodLabel(m) { return methodMap[m] || m || '-' }
function formatDate(d) { return d ? new Date(d).toLocaleDateString('zh-CN') : '' }

async function loadData() {
  loading.value = true
  try {
    const [res, contractRes] = await Promise.all([
      getPayments({ skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value }),
      getContracts({ status: 'active', limit: 50 }),
    ])
    payments.value = Array.isArray(res) ? res : []
    contracts.value = Array.isArray(contractRes) ? contractRes : []
    total.value = Array.isArray(res) ? res.length : 0
  } catch (e) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

async function handleCreatePayment() {
  const valid = await createFormRef.value.validate().catch(() => false)
  if (!valid) return
  creating.value = true
  try {
    const data = { ...createForm }
    if (data.due_date) data.due_date = new Date(data.due_date).toISOString()
    await createPayment(data)
    ElMessage.success('支付记录已创建')
    showCreateDialog.value = false
    createForm.contract_id = ''
    createForm.amount = ''
    createForm.payment_method = ''
    createForm.due_date = ''
    loadData()
  } catch (e) {
    ElMessage.error('创建支付记录失败')
  } finally {
    creating.value = false
  }
}

async function handlePay(row) {
  try {
    await ElMessageBox.confirm('确认支付？请选择支付方式', '支付确认', {
      confirmButtonText: '支付宝',
      cancelButtonText: '微信',
      distinguishCancelAndClose: true,
    }).then(() => pay(row, 'alipay')).catch((action) => {
      if (action === 'cancel') pay(row, 'wechat')
    })
  } catch (e) {
    ElMessage.error('支付操作失败')
  }
}

async function pay(row, method) {
  try {
    await updatePayment(row.id, { status: 'paid', payment_method: method })
    ElMessage.success('支付成功')
    loadData()
  } catch (e) {
    ElMessage.error('支付失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
</style>
