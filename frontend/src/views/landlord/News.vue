<template>
  <div class="page-container">
    <div class="page-header">
      <h2>新闻管理</h2>
      <el-button type="primary" @click="openDialog()">发布新闻</el-button>
    </div>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane v-for="tab in NEWS_TABS" :key="tab.name" :name="tab.name">
        <template #label>
          <span>{{ tab.label }} ({{ tabCounts[tab.name] ?? 0 }})</span>
        </template>
      </el-tab-pane>
    </el-tabs>

    <el-table :data="displayNews" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="65" align="center" />
      <el-table-column label="标题" min-width="260" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="news-title" @click="$router.push(`/news/${row.id}`)">{{ row.title }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="分类" width="110" align="center">
        <template #default="{ row }">
          <el-tag size="small" v-if="row.category">{{ row.category }}</el-tag>
          <span v-else style="color:#c0c4cc">-</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          <el-tooltip v-if="row.status === 'rejected' && row.review_message" :content="row.review_message" placement="top">
            <el-icon class="reject-icon"><WarningFilled /></el-icon>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="浏览量" width="80" align="center">
        <template #default="{ row }">{{ row.view_count || 0 }}</template>
      </el-table-column>
      <el-table-column label="发布时间" width="160" align="center">
        <template #default="{ row }">{{ formatDate(row.published_at || row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" min-width="220" align="center" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button v-if="row.status !== 'published'" type="success" size="small" @click="handlePublish(row)">发布</el-button>
          <el-button type="danger" size="small" text @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="onPageChange" />
    </div>

    <el-empty v-if="!loading && displayNews.length === 0" :description="emptyDesc" />

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑新闻' : '发布新闻'"
      width="620px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" label-width="70px" :rules="rules">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入新闻标题" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category" placeholder="请选择分类" style="width:100%">
            <el-option label="租赁资讯" value="租赁资讯" />
            <el-option label="维修通知" value="维修通知" />
            <el-option label="政策法规" value="政策法规" />
            <el-option label="生活指南" value="生活指南" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="10" placeholder="请输入新闻内容..." show-word-limit maxlength="10000" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button @click="handleSave('draft')" :loading="submitting">存草稿</el-button>
          <el-button type="primary" @click="handleSave('published')" :loading="submitting">立即发布</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { getMyNews, createNews, updateNews, deleteNews } from '../../api/news'
import { ElMessage, ElMessageBox } from 'element-plus'
import { WarningFilled } from '@element-plus/icons-vue'

const NEWS_TABS = [
  { name: '', label: '全部' },
  { name: 'published', label: '已发布' },
  { name: 'draft', label: '草稿' },
  { name: 'rejected', label: '已下架' },
]

const newsList = ref([])
const loading = ref(false)
const activeTab = ref('')
const pageSize = ref(10)
const currentPage = ref(1)
const total = ref(0)
const dialogVisible = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
}
const defaultForm = { title: '', category: '', content: '' }
const form = reactive({ ...defaultForm })

const tabCounts = computed(() => {
  const counts = {}
  NEWS_TABS.forEach(t => { counts[t.name] = 0 })
  newsList.value.forEach(n => {
    counts[''] = (counts[''] || 0) + 1
    if (counts[n.status] !== undefined) counts[n.status]++
  })
  return counts
})

const filteredNews = computed(() => {
  if (!activeTab.value) return newsList.value
  return newsList.value.filter(n => n.status === activeTab.value)
})
const displayNews = computed(() => {
  const list = filteredNews.value
  total.value = list.length
  const start = (currentPage.value - 1) * pageSize.value
  return list.slice(start, start + pageSize.value)
})

const emptyDesc = computed(() => {
  const tab = NEWS_TABS.find(t => t.name === activeTab.value)
  return tab && tab.name ? `暂无「${tab.label}」` : '暂无新闻'
})

function statusType(s) {
  return { draft: 'info', published: 'success', rejected: 'danger' }[s] || 'info'
}
function statusLabel(s) {
  return { draft: '草稿', published: '已发布', rejected: '已下架' }[s] || s
}
function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' })
}

function onTabChange() {
  currentPage.value = 1
}
function onPageChange() {}

async function loadData() {
  loading.value = true
  try {
    const res = await getMyNews({ skip: 0, limit: 200 })
    newsList.value = res.items || res || []
  } catch (e) {
    ElMessage.error('加载新闻列表失败')
  } finally {
    loading.value = false
  }
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    Object.keys(defaultForm).forEach(k => { form[k] = row[k] ?? defaultForm[k] })
  } else {
    editingId.value = null
    Object.assign(form, defaultForm)
  }
  dialogVisible.value = true
}

async function handleSave(status) {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (editingId.value) {
      await updateNews(editingId.value, { ...form, status })
    } else {
      await createNews({ ...form, status })
    }
    ElMessage.success(status === 'published' ? '已发布' : '草稿已保存')
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

async function handlePublish(row) {
  try {
    await updateNews(row.id, { status: 'published' })
    ElMessage.success('已发布')
    loadData()
  } catch (e) {
    ElMessage.error('发布失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除此新闻？', '提示', { type: 'warning' })
  } catch { return }
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
.news-title { color: var(--primary); cursor: pointer; }
.news-title:hover { text-decoration: underline; }
.reject-icon { color: var(--danger); margin-left: 4px; cursor: help; font-size: 14px; vertical-align: middle; }
.dialog-footer { display: flex; justify-content: flex-end; gap: 8px; }
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
</style>