<template>
  <div class="page-container">
    <div class="page-header"><h2>租金支付</h2></div>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPayments, updatePayment } from '../../api/payment'
import { ElMessage, ElMessageBox } from 'element-plus'

const payments = ref([])
const loading = ref(false)

const statusMap = { pending: '待支付', paid: '已支付', overdue: '逾期', cancelled: '已取消', refunded: '已退款' }
const statusTypeMap = { pending: 'warning', paid: 'success', overdue: 'danger', cancelled: 'info', refunded: '' }
const methodMap = { alipay: '支付宝', wechat: '微信', bank: '银行转账', cash: '现金' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function methodLabel(m) { return methodMap[m] || m || '-' }
function formatDate(d) { return d ? new Date(d).toLocaleDateString('zh-CN') : '' }

async function loadData() {
  loading.value = true
  try {
    const res = await getPayments({ limit: 50 })
    payments.value = Array.isArray(res) ? res : []
  } catch (e) {} finally {
    loading.value = false
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
  } catch (e) {}
}

async function pay(row, method) {
  try {
    await updatePayment(row.id, { status: 'paid', payment_method: method })
    ElMessage.success('支付成功')
    loadData()
  } catch (e) {}
}

onMounted(loadData)
</script>
