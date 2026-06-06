<template>
  <div class="page-container">
    <div class="page-header">
      <h2>维修管理</h2>
      <el-button type="primary" @click="loadData">刷新</el-button>
    </div>

    <el-tabs v-model="statusFilter" @tab-change="loadData" style="margin-bottom: 8px">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="新建" name="new" />
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
      <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
      <el-table-column label="优先级" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="priorityType(row.priority)" size="small">{{ priorityLabel(row.priority) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="assigned_to" label="处理人" width="100" show-overflow-tooltip />
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button v-if="row.status === 'new'" type="primary" size="small" @click="handleProcess(row)">处理</el-button>
          <el-button v-if="row.status === 'in_progress'" type="success" size="small" @click="handleResolve(row)">解决</el-button>
          <el-button v-if="row.status === 'resolved'" type="info" size="small" @click="handleClose(row)">关闭</el-button>
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && list.length === 0" description="暂无维修数据" />

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="维修详情" width="600px">
      <el-descriptions :column="2" border v-if="currentItem">
        <el-descriptions-item label="标题">{{ currentItem.title }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ priorityLabel(currentItem.priority) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(currentItem.status) }}</el-descriptions-item>
        <el-descriptions-item label="处理人">{{ currentItem.assigned_to || '-' }}</el-descriptions-item>
        <el-descriptions-item label="租客">{{ userNames[currentItem.tenant_id] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房源">{{ propertyNames[currentItem.property_id] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(currentItem.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDate(currentItem.updated_at) }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentItem.description }}</el-descriptions-item>
        <el-descriptions-item label="反馈" :span="2">{{ currentItem.feedback || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 处理对话框 -->
    <el-dialog v-model="processVisible" title="处理维修申请" width="500px">
      <el-form :model="processForm" label-width="80px">
        <el-form-item label="处理人">
          <el-input v-model="processForm.assigned_to" placeholder="填写维修人员姓名" />
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
        <el-form-item label="反馈">
          <el-input v-model="resolveForm.feedback" type="textarea" :rows="3" placeholder="问题解决情况说明" />
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
import { getMaintenances, updateMaintenance } from '../../api/maintenance'
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
const processForm = reactive({ assigned_to: '', remark: '' })
const resolveForm = reactive({ feedback: '' })

const { resolveItems, userNames, propertyNames } = useNameResolver()

const priorityMap = { low: '低', normal: '普通', high: '高', urgent: '紧急' }
const priorityTypeMap = { low: 'info', normal: 'info', high: 'warning', urgent: 'danger' }
const statusMap = { new: '新建', in_progress: '处理中', resolved: '已解决', closed: '已关闭' }
const statusTypeMap = { new: 'info', in_progress: 'warning', resolved: 'success', closed: 'info' }

function priorityLabel(p) { return priorityMap[p] || p }
function priorityType(p) { return priorityTypeMap[p] || 'info' }
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

    const res = await getMaintenances(params)
    list.value = res.items || []
    await resolveItems(list.value, ['tenant_id', 'property_id'])
    total.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载维修列表失败')
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
  processForm.assigned_to = ''
  processForm.remark = ''
  processVisible.value = true
}

async function submitProcess() {
  try {
    await updateMaintenance(currentItem.value.id, {
      status: 'in_progress',
      assigned_to: processForm.assigned_to,
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
  resolveForm.feedback = ''
  resolveVisible.value = true
}

async function submitResolve() {
  try {
    await updateMaintenance(currentItem.value.id, {
      status: 'resolved',
      feedback: resolveForm.feedback,
      completed_at: new Date().toISOString(),
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
    await updateMaintenance(row.id, { status: 'closed' })
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
