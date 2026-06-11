<template>
  <div class="page-container">
    <div class="page-header">
      <h2>房源管理</h2>
      <el-button type="primary" @click="$router.push('/landlord/property/create')">发布房源</el-button>
    </div>

    <el-form :inline="true" :model="filters" style="margin-bottom: 16px">
      <el-form-item label="审核状态">
        <el-select v-model="filters.review_status" clearable placeholder="全部" style="width: 120px" @change="onFilterChange">
          <el-option label="草稿" value="draft" />
          <el-option label="待审核" value="pending" />
          <el-option label="审核中" value="reviewing" />
          <el-option label="已通过" value="approved" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
      </el-form-item>
      <el-form-item label="房源状态">
        <el-select v-model="filters.status" clearable placeholder="全部" style="width: 120px" @change="onFilterChange">
          <el-option label="已发布" value="published" />
          <el-option label="未发布" value="unpublished" />
          <el-option label="已出租" value="rented" />
        </el-select>
      </el-form-item>
    </el-form>

    <el-table :data="properties" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="标题" min-width="150" show-overflow-tooltip />
      <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
      <el-table-column label="租金" width="100" align="right">
        <template #default="{ row }">¥{{ row.rent }}/月</template>
      </el-table-column>
      <el-table-column label="审核状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="reviewType(row.review_status)" size="small">{{ reviewLabel(row.review_status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="房源状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="320" align="center">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/landlord/property/${row.id}/edit`)">编辑</el-button>
          <el-button size="small" @click="manageImages(row)">图片</el-button>
          <el-button v-if="row.review_status === 'draft' || row.review_status === 'rejected'" 
                     type="primary" size="small" @click="handleSubmitReview(row)">提交审核</el-button>
          <el-button v-if="row.review_status === 'pending' || row.review_status === 'reviewing'" 
                     type="warning" size="small" @click="handleWithdrawReview(row)">撤销审核</el-button>
          <el-button v-if="row.review_status === 'approved' && row.status === 'published'" 
                     type="warning" size="small" @click="handleUnpublish(row)">取消发布</el-button>
          <el-button v-if="row.review_status === 'approved' && row.status === 'unpublished'" 
                     type="success" size="small" @click="handleRepublish(row)">发布</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <el-empty v-if="!loading && properties.length === 0" description="暂无房源，点击右上角发布" />

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
import { useRouter } from 'vue-router'
import { getMyProperties, deleteProperty, submitForReview, withdrawReview, unpublishProperty, republishProperty, getPropertyImages, addPropertyImage, updatePropertyImage, deletePropertyImage, uploadFile } from '../../api/property'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const properties = ref([])
const loading = ref(false)
const imageDialogVisible = ref(false)
const currentPropertyId = ref(null)
const images = ref([])

const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const filters = reactive({ review_status: '', status: '' })

const reviewMap = { draft: '草稿', pending: '待审核', reviewing: '审核中', approved: '已通过', rejected: '已拒绝' }
const reviewTypeMap = { draft: 'info', pending: 'warning', reviewing: 'primary', approved: 'success', rejected: 'danger' }
const statusMap = { published: '已发布', unpublished: '未发布', rented: '已出租' }
const statusTypeMap = { published: 'success', unpublished: 'info', rented: 'warning' }
function reviewLabel(s) { return reviewMap[s] || s }
function reviewType(s) { return reviewTypeMap[s] || 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }

async function loadData() {
  loading.value = true
  try {
    const params = { skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value }
    if (filters.review_status) params.review_status = filters.review_status
    if (filters.status) params.status = filters.status
    const res = await getMyProperties(params)
    properties.value = (res && res.items) || []
    total.value = (res && res.total) || 0
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error('加载房源列表失败')
    }
  } finally {
    loading.value = false
  }
}

function onFilterChange() {
  currentPage.value = 1
  loadData()
}

// 提交审核
async function handleSubmitReview(row) {
  try {
    await submitForReview(row.id)
    ElMessage.success('已提交审核')
    loadData()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.response?.data?.detail || '提交失败')
    }
  }
}

// 撤销审核
async function handleWithdrawReview(row) {
  try {
    await ElMessageBox.confirm('确定撤销审核申请？撤销后房源将变回草稿状态，可修改后重新提交。', '确认撤销', {
      type: 'warning',
      confirmButtonText: '确认撤销',
      cancelButtonText: '取消'
    })
    await withdrawReview(row.id)
    ElMessage.success('已撤销审核申请')
    loadData()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }
}

// 取消发布
async function handleUnpublish(row) {
  try {
    await ElMessageBox.confirm('确定取消发布？取消后房源将变回未发布状态，可修改后重新发布。', '确认取消', {
      type: 'warning',
      confirmButtonText: '确认取消',
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

// 重新发布
async function handleRepublish(row) {
  try {
    await republishProperty(row.id)
    ElMessage.success('已发布')
    loadData()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }
}

async function manageImages(row) {
  currentPropertyId.value = row.id
  try {
    const res = await getPropertyImages(row.id)
    images.value = Array.isArray(res) ? res : []
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error('加载图片管理失败')
    }
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
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error('图片上传失败')
    }
  }
  return false
}

async function setCover(img) {
  try {
    await updatePropertyImage(img.id, { is_cover: 1 })
    ElMessage.success('已设为封面')
    manageImages({ id: currentPropertyId.value })
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error('设置封面失败')
    }
  }
}

async function handleDeleteImage(img) {
  try {
    await ElMessageBox.confirm('确定删除该图片？', '提示', { type: 'warning' })
    await deletePropertyImage(img.id)
    ElMessage.success('删除成功')
    manageImages({ id: currentPropertyId.value })
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error('删除失败')
    }
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

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }

/* 让表格占满容器宽度 */
:deep(.el-table) {
  width: 100% !important;
}

:deep(.el-table__inner-wrapper) {
  width: 100% !important;
}
</style>
