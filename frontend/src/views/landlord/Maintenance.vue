<template>
  <div class="page-container">
    <div class="page-header">
      <h2>维修管理</h2>
    </div>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="房源" width="100">
        <template #default="{ row }">房源#{{ row.property_id }}</template>
      </el-table-column>
      <el-table-column label="租客" width="100">
        <template #default="{ row }">用户#{{ row.tenant_id }}</template>
      </el-table-column>
      <el-table-column prop="title" label="标题" width="200" />
      <el-table-column prop="description" label="描述" />
      <el-table-column label="优先级" width="80">
        <template #default="{ row }">
          <el-tag :type="priorityType(row.priority)" size="small">{{ priorityLabel(row.priority) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="assigned_to" label="处理人" width="100" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button v-if="row.status === 'new'" type="primary" size="small" @click="handleProcess(row)">处理</el-button>
          <el-button v-if="row.status === 'in_progress'" type="success" size="small" @click="handleResolve(row)">解决</el-button>
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="detailVisible" title="维修详情" width="600px">
      <el-descriptions :column="2" border v-if="currentItem">
        <el-descriptions-item label="标题">{{ currentItem.title }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ priorityLabel(currentItem.priority) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(currentItem.status) }}</el-descriptions-item>
        <el-descriptions-item label="房源ID">{{ currentItem.property_id }}</el-descriptions-item>
        <el-descriptions-item label="租客ID">{{ currentItem.tenant_id }}</el-descriptions-item>
        <el-descriptions-item label="处理人">{{ currentItem.assigned_to || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(currentItem.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentItem.description }}</el-descriptions-item>
        <el-descriptions-item label="反馈" :span="2">{{ currentItem.feedback || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

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
        <el-button type="primary" @click="submitProcess">确认</el-button>
      </template>
    </el-dialog>

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

const list = ref([])
const loading = ref(false)
const detailVisible = ref(false)
const processVisible = ref(false)
const resolveVisible = ref(false)
const currentItem = ref(null)
const processForm = reactive({ assigned_to: '', remark: '' })
const resolveForm = reactive({ feedback: '' })

const priorityMap = { low: '低', normal: '普通', high: '高', urgent: '紧急' }
const priorityTypeMap = { low: 'info', normal: '', high: 'warning', urgent: 'danger' }
const statusMap = { new: '新建', in_progress: '处理中', resolved: '已解决', closed: '已关闭' }
const statusTypeMap = { new: 'info', in_progress: 'warning', resolved: 'success', closed: '' }

function priorityLabel(p) { return priorityMap[p] || p }
function priorityType(p) { return priorityTypeMap[p] || 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }
function formatDate(d) { return d ? new Date(d).toLocaleDateString('zh-CN') : '' }

async function loadData() {
  loading.value = true
  try {
    // 房东查看自己房源的维修申请
    const res = await getMaintenances({ limit: 50 })
    list.value = Array.isArray(res) ? res : []
  } catch (e) {
    ElMessage.error('加载失败')
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
      remark: processForm.remark
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
      completed_at: new Date().toISOString()
    })
    ElMessage.success('已标记为已解决')
    resolveVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

onMounted(loadData)
</script>
