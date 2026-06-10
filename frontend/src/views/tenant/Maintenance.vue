<template>
  <div class="page-container">
    <div class="page-header">
      <h2>维修申请</h2>
      <el-button type="primary" @click="showDialog = true">提交维修申请</el-button>
    </div>
    <el-tabs v-model="statusFilter" @tab-change="onFilterChange" style="margin-bottom: 12px">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="待处理" name="new" />
      <el-tab-pane label="处理中" name="in_progress" />
      <el-tab-pane label="已解决" name="resolved" />
      <el-tab-pane label="已关闭" name="closed" />
    </el-tabs>

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
    <el-empty v-if="!loading && list.length === 0" description="暂无数据" />

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <el-dialog v-model="showDialog" title="提交维修申请" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="房源">
          <el-select v-model="form.property_id" placeholder="请选择房源" filterable style="width: 100%">
            <el-option v-for="p in myProperties" :key="p.id" :label="p.title" :value="p.id" />
          </el-select>
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
import { ref, reactive, watch, onMounted } from 'vue'
import { getMaintenances, createMaintenance } from '../../api/maintenance'
import { getProperties } from '../../api/property'
import { ElMessage } from 'element-plus'

const list = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const showDialog = ref(false)
const detailVisible = ref(false)
const submitting = ref(false)
const currentItem = ref(null)
const myProperties = ref([])
const statusFilter = ref('')
const form = reactive({ property_id: '', title: '', description: '', priority: 'normal' })

const priorityMap = { low: '低', normal: '普通', high: '高', urgent: '紧急' }
const priorityTypeMap = { low: 'info', normal: 'info', high: 'warning', urgent: 'danger' }
const statusMap = { new: '新建', in_progress: '处理中', resolved: '已解决', closed: '已关闭' }
const statusTypeMap = { new: 'info', in_progress: 'warning', resolved: 'success', closed: 'info' }
function priorityLabel(p) { return priorityMap[p] || p }
function priorityType(p) { return priorityTypeMap[p] || 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }

function onFilterChange() {
  currentPage.value = 1
  loadData()
}

async function loadData() {
  loading.value = true
  try {
    const params = { skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await getMaintenances(params)
    list.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载维修记录失败')
  } finally {
    loading.value = false
  }
}

async function loadMyProperties() {
  try {
    const res = await getProperties({ limit: 100 })
    myProperties.value = (res && res.items) || []
  } catch (e) {
    ElMessage.error('加载房源列表失败')
  }
}

async function handleSubmit() {
  if (!form.property_id || !form.description) {
    ElMessage.warning('请选择房源并填写描述')
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
  } catch (e) {
    ElMessage.error('提交维修申请失败')
  } finally {
    submitting.value = false
  }
}

function viewDetail(row) {
  currentItem.value = row
  detailVisible.value = true
}

onMounted(loadData)

watch(showDialog, (val) => {
  if (val) loadMyProperties()
})
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
</style>
