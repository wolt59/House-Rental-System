<template>
  <div class="page-container">
    <div class="page-header">
      <h2>新闻管理</h2>
      <el-button type="primary" @click="openDialog()">发布新闻</el-button>
    </div>
    <el-table :data="newsList" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="标题" min-width="250" show-overflow-tooltip />
      <el-table-column prop="category" label="分类" min-width="120" show-overflow-tooltip />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">{{ row.status === 'published' ? '已发布' : '草稿' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="浏览量" width="100" align="center">
        <template #default="{ row }">{{ row.view_count }}</template>
      </el-table-column>
      <el-table-column label="操作" min-width="200" align="center">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button v-if="row.status === 'draft'" type="success" size="small" @click="handlePublish(row)">发布</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && newsList.length === 0" description="暂无数据" />

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑新闻' : '发布新闻'" width="600px">
      <el-form ref="formRef" :model="form" label-width="80px" :rules="newsRules">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category">
            <el-option label="租赁资讯" value="租赁资讯" />
            <el-option label="维修通知" value="维修通知" />
            <el-option label="政策法规" value="政策法规" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="8" /></el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="draft">草稿</el-radio>
            <el-radio value="published">发布</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getMyNews, createNews, updateNews, deleteNews } from '../../api/news'
import { ElMessage, ElMessageBox } from 'element-plus'

const newsList = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const dialogVisible = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const newsRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
}
const defaultForm = { title: '', category: '', content: '', status: 'draft' }
const form = reactive({ ...defaultForm })

async function loadData() {
  loading.value = true
  try {
    const res = await getMyNews({ skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value })
    newsList.value = Array.isArray(res) ? res : []
    total.value = Array.isArray(res) ? res.length : 0
  } catch (e) { ElMessage.error('加载新闻列表失败') } finally {
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
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (editingId.value) {
      await updateNews(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await createNews(form)
      ElMessage.success('发布成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) { ElMessage.error(editingId.value ? '更新新闻失败' : '发布新闻失败') } finally {
    submitting.value = false
  }
}

async function handlePublish(row) {
  try {
    await updateNews(row.id, { status: 'published' })
    ElMessage.success('已发布')
    loadData()
  } catch (e) { ElMessage.error('发布失败') }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除此新闻？', '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteNews(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {
    ElMessage.error('删除失败')
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
