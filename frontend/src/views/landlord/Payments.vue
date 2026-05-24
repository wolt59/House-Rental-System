<template>
  <div class="page-container">
    <div class="page-header"><h2>收款管理</h2></div>
    <el-table :data="payments" stripe v-loading="loading">
      <el-table-column prop="payment_no" label="支付单号" width="220" />
      <el-table-column label="租客" width="100">
        <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
      </el-table-column>
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
      <el-table-column label="逾期天数" width="90">
        <template #default="{ row }">{{ row.overdue_days || 0 }}天</template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && payments.length === 0" description="暂无数据" />
    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPayments } from '../../api/payment'
import { ElMessage } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'

const { resolveItems, userNames } = useNameResolver()

const payments = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)

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
    const res = await getPayments({ skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value })
    payments.value = Array.isArray(res) ? res : []
    await resolveItems(payments.value, ['tenant_id'])
    total.value = Array.isArray(res) ? res.length : 0
  } catch (e) { ElMessage.error('加载收款列表失败') } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
</style>
