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
      <el-table-column label="操作" width="280">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" @click="manageImages(row)">图片</el-button>
          <el-button v-if="row.review_status === 'draft' || row.review_status === 'rejected'" 
                     type="primary" size="small" @click="handleSubmitReview(row)">提交审核</el-button>
          <el-button v-if="row.review_status === 'approved' && row.status === 'published'" 
                     size="small" @click="handleUnpublish(row)">取消发布</el-button>
          <el-button v-if="row.review_status === 'approved' && row.status === 'unpublished'" 
                     type="success" size="small" @click="handleRepublish(row)">发布</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && properties.length === 0" description="暂无房源，点击右上角发布" />

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑房源' : '发布房源'" width="700px">
      <!-- 状态提示 -->
      <el-alert v-if="editingId && currentEditProperty" :title="getEditRestrictionTip(currentEditProperty)" type="warning" :closable="false" style="margin-bottom: 16px" />
      
      <el-form :model="form" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="标题"><el-input v-model="form.title" :disabled="isFieldDisabled('title')" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="地址"><el-input v-model="form.address" :disabled="isFieldDisabled('address')" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="区域"><el-input v-model="form.region" placeholder="如：朝阳区" :disabled="isFieldDisabled('region')" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型"><el-input v-model="form.property_type" placeholder="如：公寓" :disabled="isFieldDisabled('property_type')" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="户型"><el-input v-model="form.floor_plan" placeholder="如：2室1厅" :disabled="isFieldDisabled('floor_plan')" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="面积"><el-input v-model="form.area" placeholder="㎡" :disabled="isFieldDisabled('area')" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="月租金"><el-input v-model="form.rent" :disabled="isFieldDisabled('rent')" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="押金"><el-input v-model="form.deposit" :disabled="isFieldDisabled('deposit')" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="装修"><el-input v-model="form.decoration" :disabled="isFieldDisabled('decoration')" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="朝向"><el-input v-model="form.orientation" :disabled="isFieldDisabled('orientation')" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="楼层"><el-input v-model="form.floor_number" placeholder="如：5/18" :disabled="isFieldDisabled('floor_number')" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="总楼层"><el-input v-model="form.total_floors" :disabled="isFieldDisabled('total_floors')" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="配套设施"><el-input v-model="form.facilities" placeholder='JSON格式，如：{"wifi":true,"ac":true}' :disabled="isFieldDisabled('facilities')" /></el-form-item>
        <el-form-item label="周边环境"><el-input v-model="form.surrounding" type="textarea" :rows="2" :disabled="isFieldDisabled('surrounding')" /></el-form-item>
        <el-form-item label="房源描述"><el-input v-model="form.description" type="textarea" :rows="3" :disabled="isFieldDisabled('description')" /></el-form-item>
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
import { getMyProperties, createProperty, updateProperty, deleteProperty, submitForReview, unpublishProperty, republishProperty, getPropertyImages, addPropertyImage, updatePropertyImage, deletePropertyImage, uploadFile } from '../../api/property'
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
const currentEditProperty = ref(null) // 当前编辑的房源对象

// 核心字段定义（修改需重新审核）
const CORE_FIELDS = ['address', 'floor_plan', 'area', 'rent', 'deposit', 'floor_number', 'total_floors']

const reviewMap = { draft: '草稿', pending: '待审核', reviewing: '审核中', approved: '已通过', rejected: '已拒绝' }
const reviewTypeMap = { draft: 'info', pending: 'warning', reviewing: 'primary', approved: 'success', rejected: 'danger' }
const statusMap = { published: '已发布', unpublished: '未发布', vacant: '空置', rented: '已出租', maintenance: '维修中' }
const statusTypeMap = { published: 'success', unpublished: 'info', vacant: 'success', rented: 'warning', maintenance: 'danger' }
function reviewLabel(s) { return reviewMap[s] || s }
function reviewType(s) { return reviewTypeMap[s] || 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }

async function loadData() {
  loading.value = true
  try {
    const res = await getMyProperties({ limit: 50 })
    properties.value = Array.isArray(res) ? res : []
  } catch (e) {
    ElMessage.error('加载房源列表失败')
  } finally {
    loading.value = false
  }
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    currentEditProperty.value = row
    Object.keys(defaultForm).forEach((k) => { form[k] = row[k] ?? defaultForm[k] })
  } else {
    editingId.value = null
    currentEditProperty.value = null
    Object.assign(form, defaultForm)
  }
  dialogVisible.value = true
}

// 判断字段是否禁用
function isFieldDisabled(field) {
  // 新增房源时所有字段都可编辑
  if (!editingId.value || !currentEditProperty.value) return false
  
  const reviewStatus = currentEditProperty.value.review_status
  const status = currentEditProperty.value.status
  
  // 已出租或维修中：只能修改描述
  if (status === 'rented' || status === 'maintenance') {
    return field !== 'description'
  }
  
  // 待审核或审核中：只能修改描述和周边环境
  if (reviewStatus === 'pending' || reviewStatus === 'reviewing') {
    return field !== 'description' && field !== 'surrounding'
  }
  
  // 草稿或已拒绝：所有字段可编辑
  if (reviewStatus === 'draft' || reviewStatus === 'rejected') {
    return false
  }
  
  // 已通过（已发布/暂停发布）：所有字段可编辑（核心字段修改后会自动转为待审核）
  return false
}

// 获取编辑限制提示
function getEditRestrictionTip(property) {
  const reviewStatus = property.review_status
  const status = property.status
  
  if (status === 'rented' || status === 'maintenance') {
    return '已出租/维修中的房源仅允许修改描述信息'
  }
  
  if (reviewStatus === 'pending' || reviewStatus === 'reviewing') {
    return '审核中的房源仅允许修改描述和周边环境信息'
  }
  
  if (reviewStatus === 'approved' && (status === 'published' || status === 'unpublished')) {
    return '已审核通过的房源，核心字段（地址/户型/面积/租金/押金/楼层）可修改，但修改后会自动转为"待审核"状态'
  }
  
  if (reviewStatus === 'draft' && (status === 'unpublished')) {
    return '房源已被管理员下架，请修改后重新提交审核'
  }
  
  return ''
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
      // 检查是否修改了核心字段
      const hasCoreFieldChanges = CORE_FIELDS.some(field => 
        data[field] !== undefined && data[field] !== currentEditProperty.value[field]
      )
      
      if (hasCoreFieldChanges && currentEditProperty.value.review_status === 'approved') {
        try {
          await ElMessageBox.confirm(
            '您修改了房源的核心字段（地址/户型/面积/租金/押金/楼层），保存后房源将自动转为"待审核"状态，需要管理员重新审核。确认继续？',
            '提示',
            {
              type: 'warning',
              confirmButtonText: '确认保存',
              cancelButtonText: '取消'
            }
          )
        } catch {
          submitting.value = false
          return // 用户取消
        }
      }
      
      await updateProperty(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createProperty(data)
      ElMessage.success('发布成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

async function manageImages(row) {
  currentPropertyId.value = row.id
  try {
    const res = await getPropertyImages(row.id)
    images.value = Array.isArray(res) ? res : []
  } catch (e) {
    ElMessage.error('图片管理加载失败')
  }
  imageDialogVisible.value = true
}

async function handleImageUpload(file) {
  try {
    const res = await uploadFile(file)
    await addPropertyImage(currentPropertyId.value, { image_url: res.url, image_type: 'photo', is_cover: images.value.length === 0 ? 1 : 0, sort_order: images.value.length })
    ElMessage.success('上传成功')
    manageImages({ id: currentPropertyId.value })
  } catch (e) {
    ElMessage.error('图片上传失败')
  }
  return false
}

async function setCover(img) {
  try {
    await updatePropertyImage(img.id, { is_cover: 1 })
    ElMessage.success('已设为封面')
    manageImages({ id: currentPropertyId.value })
  } catch (e) {
    ElMessage.error('设置封面失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除该房源？此操作不可恢复。\n若有生效合同，系统将阻止删除。', '确认删除', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消'
    })
    await deleteProperty(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }
}

async function handleSubmitReview(row) {
  try {
    await ElMessageBox.confirm('确定提交审核？提交后管理员将审核您的房源。', '提交审核', {
      type: 'info',
      confirmButtonText: '确定提交',
      cancelButtonText: '取消'
    })
    await submitForReview(row.id)
    ElMessage.success('已提交审核，请等待管理员审核')
    loadData()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.response?.data?.detail || '提交失败')
    }
  }
}

async function handleUnpublish(row) {
  try {
    await ElMessageBox.confirm('确定取消发布？取消后租客将无法看到该房源。', '取消发布', {
      type: 'warning',
      confirmButtonText: '确定取消',
      cancelButtonText: '取消'
    })
    await unpublishProperty(row.id)
    ElMessage.success('已取消发布')
    loadData()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }
}

async function handleRepublish(row) {
  try {
    await republishProperty(row.id)
    ElMessage.success('已重新发布')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

onMounted(loadData)
</script>
