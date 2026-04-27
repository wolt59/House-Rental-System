<template>
  <div class="page-container">
    <div class="page-header">
      <h2>维修申请</h2>
      <el-button type="primary" @click="showDialog = true">提交维修申请</el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
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
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" title="提交维修申请" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="房源ID">
          <el-input v-model.number="form.property_id" />
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority">
            <el-option label="低" value="low" />
            <el-option label="普通" value="normal" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="维修详情" width="500px">
      <el-descriptions :column="1" border v-if="currentItem">
        <el-descriptions-item label="标题">{{ currentItem.title }}</el-descriptions-item>
        <el-descriptions-item label="描述">{{ currentItem.description }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ priorityLabel(currentItem.priority) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(currentItem.status) }}</el-descriptions-item>
        <el-descriptions-item label="处理人">{{ currentItem.assigned_to || '-' }}</el-descriptions-item>
        <el-descriptions-item label="反馈">{{ currentItem.feedback || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getMaintenances, createMaintenance } from '../../api/maintenance'
import { ElMessage } from 'element-plus'

const list = ref([])
const loading = ref(false)
const showDialog = ref(false)
const detailVisible = ref(false)
const submitting = ref(false)
const currentItem = ref(null)
const form = reactive({ property_id: '', title: '', description: '', priority: 'normal' })

const priorityMap = { low: '低', normal: '普通', high: '高', urgent: '紧急' }
const priorityTypeMap = { low: 'info', normal: '', high: 'warning', urgent: 'danger' }
const statusMap = { new: '新建', in_progress: '处理中', resolved: '已解决', closed: '已关闭' }
const statusTypeMap = { new: 'info', in_progress: 'warning', resolved: 'success', closed: '' }
function priorityLabel(p) { return priorityMap[p] || p }
function priorityType(p) { return priorityTypeMap[p] || 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }

async function loadData() {
  loading.value = true
  try {
    const res = await getMaintenances({ limit: 50 })
    list.value = Array.isArray(res) ? res : []
  } catch (e) {} finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!form.property_id || !form.description) {
    ElMessage.warning('请填写房源ID和描述')
    return
  }
  submitting.value = true
  try {
    await createMaintenance(form)
    ElMessage.success('提交成功')
    showDialog.value = false
    form.property_id = ''
    form.title = ''
    form.description = ''
    form.priority = 'normal'
    loadData()
  } catch (e) {} finally {
    submitting.value = false
  }
}

function viewDetail(row) {
  currentItem.value = row
  detailVisible.value = true
}

onMounted(loadData)
</script>
