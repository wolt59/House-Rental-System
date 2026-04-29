<template>
  <div class="page-container">
    <div class="page-header">
      <h2>房源管理</h2>
      <el-button type="primary" @click="openDialog()">发布房源</el-button>
    </div>
    <el-table :data="properties" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="标题" width="200" />
      <el-table-column prop="address" label="地址" />
      <el-table-column label="租金" width="100">
        <template #default="{ row }">¥{{ row.rent }}/月</template>
      </el-table-column>
      <el-table-column label="审核状态" width="100">
        <template #default="{ row }">
          <el-tag :type="reviewType(row.review_status)" size="small">{{ reviewLabel(row.review_status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="房源状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" @click="manageImages(row)">图片</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑房源' : '发布房源'" width="700px">
      <el-form :model="form" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="区域"><el-input v-model="form.region" placeholder="如：朝阳区" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型"><el-input v-model="form.property_type" placeholder="如：公寓" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="户型"><el-input v-model="form.floor_plan" placeholder="如：2室1厅" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="面积"><el-input v-model="form.area" placeholder="㎡" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="月租金"><el-input v-model="form.rent" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="押金"><el-input v-model="form.deposit" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="装修"><el-input v-model="form.decoration" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="朝向"><el-input v-model="form.orientation" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="楼层"><el-input v-model="form.floor_number" placeholder="如：5/18" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="总楼层"><el-input v-model="form.total_floors" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="配套设施"><el-input v-model="form.facilities" placeholder='JSON格式，如：{"wifi":true,"ac":true}' /></el-form-item>
        <el-form-item label="周边环境"><el-input v-model="form.surrounding" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="房源描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">{{ editingId ? '保存' : '发布' }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="imageDialogVisible" title="房源图片管理" width="700px">
      <div style="margin-bottom: 16px">
        <el-upload :show-file-list="false" :before-upload="handleImageUpload" accept="image/*">
          <el-button type="primary" size="small">上传图片</el-button>
        </el-upload>
      </div>
      <el-row :gutter="12">
        <el-col :span="6" v-for="img in images" :key="img.id">
          <el-card :body-style="{ padding: '8px' }">
            <img :src="img.image_url" style="width: 100%; height: 120px; object-fit: cover; border-radius: 4px" />
            <div style="margin-top: 8px; display: flex; justify-content: space-between; align-items: center">
              <el-tag size="small" v-if="img.is_cover" type="success">封面</el-tag>
              <el-button v-else size="small" @click="setCover(img)">设为封面</el-button>
              <el-button type="danger" size="small" @click="handleDeleteImage(img)">删除</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getMyProperties, createProperty, updateProperty, deleteProperty, getPropertyImages, addPropertyImage, updatePropertyImage, deletePropertyImage, uploadFile } from '../../api/property'
import { ElMessage, ElMessageBox } from 'element-plus'

const properties = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const imageDialogVisible = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const currentPropertyId = ref(null)
const images = ref([])

const defaultForm = { title: '', address: '', region: '', property_type: '', floor_plan: '', area: '', rent: '', deposit: '', decoration: '', orientation: '', floor_number: '', total_floors: '', facilities: '', surrounding: '', description: '' }
const form = reactive({ ...defaultForm })

const reviewMap = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
const reviewTypeMap = { pending: 'warning', approved: 'success', rejected: 'danger' }
const statusMap = { vacant: '空置', rented: '已出租', maintenance: '维修中' }
const statusTypeMap = { vacant: 'success', rented: 'warning', maintenance: 'danger' }
function reviewLabel(s) { return reviewMap[s] || s }
function reviewType(s) { return reviewTypeMap[s] || 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }

async function loadData() {
  loading.value = true
  try {
    const res = await getMyProperties({ limit: 50 })
    properties.value = Array.isArray(res) ? res : []
  } catch (e) {} finally {
    loading.value = false
  }
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    Object.keys(defaultForm).forEach((k) => { form[k] = row[k] ?? defaultForm[k] })
  } else {
    editingId.value = null
    Object.assign(form, defaultForm)
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  submitting.value = true
  try {
    // 后端 Pydantic 对数字字段不接受 ''，需要在提交前清理空字符串
    // 这样即使可选字段没填，也能避免 422。
    if (!form.title?.trim() || !form.address?.trim() || form.rent === '') {
      ElMessage.warning('请填写：标题、地址、月租金')
      return
    }

    const data = {}
    Object.entries(form).forEach(([k, v]) => {
      if (v === '' || v === null || v === undefined) return
      data[k] = v
    })

    // 数字字段做类型转换（保留 0 值的场景）
    if ('area' in data) data.area = parseFloat(data.area)
    if ('rent' in data) data.rent = parseFloat(data.rent)
    if ('deposit' in data) data.deposit = parseFloat(data.deposit)
    if ('total_floors' in data) data.total_floors = parseInt(data.total_floors)
    if (editingId.value) {
      await updateProperty(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createProperty(data)
      ElMessage.success('发布成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {} finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除此房源？', '提示', { type: 'warning' })
    await deleteProperty(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {}
}

async function manageImages(row) {
  currentPropertyId.value = row.id
  try {
    const res = await getPropertyImages(row.id)
    images.value = Array.isArray(res) ? res : []
  } catch (e) {}
  imageDialogVisible.value = true
}

async function handleImageUpload(file) {
  try {
    const res = await uploadFile(file)
    await addPropertyImage(currentPropertyId.value, { image_url: res.url, image_type: 'photo', is_cover: images.value.length === 0 ? 1 : 0, sort_order: images.value.length })
    ElMessage.success('上传成功')
    manageImages({ id: currentPropertyId.value })
  } catch (e) {}
  return false
}

async function setCover(img) {
  try {
    await updatePropertyImage(img.id, { is_cover: 1 })
    ElMessage.success('已设为封面')
    manageImages({ id: currentPropertyId.value })
  } catch (e) {}
}

async function handleDelete(row) {
  try {
    // 第一步：检查是否有合同
    const hasContract = row.contracts && row.contracts.some(c =>
      c.status === 'active' || c.status === 'pending_sign'
    )

    if (hasContract) {
      ElMessage.error('该房源有生效或待签署的合同，无法删除。请先终止相关合同。')
      return
    }

    // 第二步：检查是否有待处理事项
    const warnings = []
    if (row.bookings && row.bookings.some(b => b.status === 'pending')) {
      warnings.push('有待处理的预约')
    }
    if (row.maintenance_requests && row.maintenance_requests.some(m => m.status === 'open')) {
      warnings.push('有待处理的维修申请')
    }
    if (row.complaints && row.complaints.some(c => c.status === 'open')) {
      warnings.push('有待处理的投诉')
    }

    // 第三步：构建确认消息
    let confirmMessage = '确定删除该房源？此操作不可恢复'
    if (warnings.length > 0) {
      confirmMessage += '\n\n⚠️ 警告：' + warnings.join('、')
      confirmMessage += '\n\n删除后将同时清除这些待处理事项。'
    }

    await ElMessageBox.confirm(confirmMessage, '确认删除', {
      type: 'warning',
      distinguishCancelAndClose: true,
      confirmButtonText: '确认删除',
      cancelButtonText: '取消'
    })

    await deleteProperty(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      const errorMsg = e.response?.data?.detail || e.message || '删除失败'
      ElMessage.error(errorMsg)
    }
  }
}

onMounted(loadData)
</script>
