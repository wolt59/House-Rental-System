<template>
  <div class="page-container">
    <div class="page-header">
      <h2>投诉管理</h2>
      <el-button type="primary" @click="showDialog = true">提交投诉</el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="标题" width="200" />
      <el-table-column prop="complaint_type" label="类型" width="100" />
      <el-table-column prop="content" label="内容" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="handled_by" label="处理人" width="100" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" title="提交投诉" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="房源ID">
          <el-input v-model.number="form.property_id" />
        </el-form-item>
        <el-form-item label="投诉类型">
          <el-select v-model="form.complaint_type">
            <el-option label="房源问题" value="房源" />
            <el-option label="服务问题" value="服务" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="投诉详情" width="500px">
      <el-descriptions :column="1" border v-if="currentItem">
        <el-descriptions-item label="标题">{{ currentItem.title }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ currentItem.complaint_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="内容">{{ currentItem.content }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(currentItem.status) }}</el-descriptions-item>
        <el-descriptions-item label="处理人">{{ currentItem.handled_by || '-' }}</el-descriptions-item>
        <el-descriptions-item label="处理结果">{{ currentItem.result || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getComplaints, createComplaint } from '../../api/complaint'
import { ElMessage } from 'element-plus'

const list = ref([])
const loading = ref(false)
const showDialog = ref(false)
const detailVisible = ref(false)
const submitting = ref(false)
const currentItem = ref(null)
const form = reactive({ property_id: '', complaint_type: '', title: '', content: '' })

const statusMap = { open: '待处理', in_progress: '处理中', resolved: '已解决', closed: '已关闭' }
const statusTypeMap = { open: 'danger', in_progress: 'warning', resolved: 'success', closed: 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }

async function loadData() {
  loading.value = true
  try {
    const res = await getComplaints({ limit: 50 })
    list.value = Array.isArray(res) ? res : []
  } catch (e) {} finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!form.property_id || !form.content) {
    ElMessage.warning('请填写房源ID和内容')
    return
  }
  submitting.value = true
  try {
    await createComplaint(form)
    ElMessage.success('投诉已提交')
    showDialog.value = false
    form.property_id = ''
    form.complaint_type = ''
    form.title = ''
    form.content = ''
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
