<template>
  <div class="page-container">
    <div class="page-header">
      <h2>投诉管理</h2>
      <el-button type="primary" @click="loadData">刷新</el-button>
    </div>

    <el-tabs v-model="statusFilter" @tab-change="loadData" style="margin-bottom: 8px">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="待处理" name="open" />
      <el-tab-pane label="处理中" name="in_progress" />
      <el-tab-pane label="已解决" name="resolved" />
      <el-tab-pane label="已关闭" name="closed" />
    </el-tabs>

    <el-table :data="list" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="房源" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column label="租客" width="100" show-overflow-tooltip>
        <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="140" show-overflow-tooltip />
      <el-table-column prop="complaint_type" label="类型" width="90" align="center" />
      <el-table-column prop="content" label="内容" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="handled_by" label="处理人" width="100" show-overflow-tooltip />
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button v-if="row.status === 'open'" type="primary" size="small" @click="handleProcess(row)">处理</el-button>
          <el-button v-if="row.status === 'in_progress'" type="success" size="small" @click="handleResolve(row)">解决</el-button>
          <el-button v-if="row.status === 'resolved'" type="info" size="small" @click="handleClose(row)">关闭</el-button>
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && list.length === 0" description="暂无投诉数据" />

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="投诉详情" width="600px">
      <el-descriptions :column="2" border v-if="currentItem">
        <el-descriptions-item label="标题">{{ currentItem.title }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ currentItem.complaint_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(currentItem.status) }}</el-descriptions-item>
        <el-descriptions-item label="处理人">{{ currentItem.handled_by || '-' }}</el-descriptions-item>
        <el-descriptions-item label="租客">{{ userNames[currentItem.tenant_id] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房源">{{ propertyNames[currentItem.property_id] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(currentItem.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDate(currentItem.updated_at) }}</el-descriptions-item>
        <el-descriptions-item label="内容" :span="2">{{ currentItem.content }}</el-descriptions-item>
        <el-descriptions-item label="处理结果" :span="2">{{ currentItem.result || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 处理对话框 -->
    <el-dialog v-model="processVisible" title="处理投诉" width="500px">
      <el-form :model="processForm" label-width="80px">
        <el-form-item label="处理人">
          <el-input v-model="processForm.handled_by" placeholder="填写处理人员姓名" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="processForm.remark" type="textarea" :rows="3" placeholder="处理说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="processVisible = false">取消</el-button>
        <el-button type="primary" @click="submitProcess">开始处理</el-button>
      </template>
    </el-dialog>

    <!-- 解决对话框 -->
    <el-dialog v-model="resolveVisible" title="标记为已解决" width="500px">
      <el-form :model="resolveForm" label-width="80px">
        <el-form-item label="处理结果">
          <el-input v-model="resolveForm.result" type="textarea" :rows="4" placeholder="详细说明处理结果" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resolveVisible = false">取消</el-button>
        <el-button type="success" @click="submitResolve">确认解决</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getComplaints, updateComplaint } from '../../api/complaint'
import { ElMessage } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'

const list = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(15)
const currentPage = ref(1)
const statusFilter = ref('')
const detailVisible = ref(false)
const processVisible = ref(false)
const resolveVisible = ref(false)
const currentItem = ref(null)
const processForm = reactive({ handled_by: '', remark: '' })
const resolveForm = reactive({ result: '' })

const { resolveItems, userNames, propertyNames } = useNameResolver()

const statusMap = {
  open: '待处理',
  in_progress: '处理中',
  resolved: '已解决',
  closed: '已关闭',
}
const statusTypeMap = {
  open: 'danger',
  in_progress: 'warning',
  resolved: 'success',
  closed: 'info',
}

function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function formatDate(d) { return d ? new Date(d).toLocaleString('zh-CN') : '' }

async function loadData() {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    if (statusFilter.value) params.status = statusFilter.value

    const res = await getComplaints(params)
    list.value = res.items || []
    await resolveItems(list.value, ['tenant_id', 'property_id'])
    total.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载投诉列表失败')
  } finally {
    loading.value = false
  }
}

function viewDetail(row) {
  currentItem.value = row
  detailVisible.value = true
}

function handleProcess(row) {
  currentItem.value = row
  processForm.handled_by = ''
  processForm.remark = ''
  processVisible.value = true
}

async function submitProcess() {
  try {
    await updateComplaint(currentItem.value.id, {
      status: 'in_progress',
      handled_by: processForm.handled_by,
      remark: processForm.remark,
    })
    ElMessage.success('已开始处理')
    processVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function handleResolve(row) {
  currentItem.value = row
  resolveForm.result = ''
  resolveVisible.value = true
}

async function submitResolve() {
  try {
    await updateComplaint(currentItem.value.id, {
      status: 'resolved',
      result: resolveForm.result,
      resolved_at: new Date().toISOString(),
    })
    ElMessage.success('已标记为已解决')
    resolveVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function handleClose(row) {
  try {
    await updateComplaint(row.id, { status: 'closed' })
    ElMessage.success('已关闭')
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

:deep(.el-table) {
  width: 100% !important;
}

:deep(.el-table__inner-wrapper) {
  width: 100% !important;
}
</style>
