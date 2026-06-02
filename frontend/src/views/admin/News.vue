<template>
  <div class="page-container">
    <div class="page-header">
      <h2>新闻审核</h2>
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
      <el-table-column label="作者" width="110" align="center">
        <template #default="{ row }">{{ row.author_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          <el-tooltip v-if="row.status==='rejected' && row.review_message" :content="row.review_message" placement="top">
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
      <el-table-column label="操作" min-width="200" align="center" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'published'">
            <el-button type="danger" size="small" @click="openReject(row)">下架</el-button>
          </template>
          <template v-if="row.status === 'rejected'">
            <el-button type="success" size="small" @click="handleApprove(row)">恢复发布</el-button>
          </template>
          <el-button size="small" text @click="$router.push(`/news/${row.id}`)">查看</el-button>
          <el-button size="small" text type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && displayNews.length === 0" :description="emptyDesc" />

    <el-dialog v-model="rejectVisible" title="下架新闻" width="480px" :close-on-click-modal="false">
      <el-form label-width="80px">
        <el-form-item label="新闻标题">
          <span style="font-weight:600">{{ rejectTarget?.title }}</span>
        </el-form-item>
        <el-form-item label="下架原因" required>
          <el-input v-model="rejectMsg" type="textarea" :rows="4" placeholder="请填写下架原因，将通知给房东..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :loading="reviewLoading" @click="handleRejectSubmit">确认下架</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getAllNewsAdmin, reviewNews, deleteNews } from '../../api/news'
import { ElMessage, ElMessageBox } from 'element-plus'
import { WarningFilled } from '@element-plus/icons-vue'

const NEWS_TABS = [
  { name: '', label: '全部' },
  { name: 'published', label: '已发布' },
  { name: 'rejected', label: '已下架' },
  { name: 'draft', label: '草稿' },
]

const newsList = ref([])
const loading = ref(false)
const activeTab = ref('')
const reviewLoading = ref(false)
const rejectVisible = ref(false)
const rejectTarget = ref(null)
const rejectMsg = ref('')

const tabCounts = computed(() => {
  const counts = {}
  NEWS_TABS.forEach(t => { counts[t.name] = 0 })
  newsList.value.forEach(n => {
    counts[''] = (counts[''] || 0) + 1
    if (counts[n.status] !== undefined) counts[n.status]++
  })
  return counts
})

const displayNews = computed(() => {
  if (!activeTab.value) return newsList.value
  return newsList.value.filter(n => n.status === activeTab.value)
})

const emptyDesc = computed(() => {
  const tab = NEWS_TABS.find(t => t.name === activeTab.value)
  return tab && tab.name ? `暂无「${tab.label}」` : '暂无数据'
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

function onTabChange() {}

async function loadData() {
  loading.value = true
  try {
    const res = await getAllNewsAdmin({ skip: 0, limit: 200 })
    newsList.value = res.items || []
  } catch (e) {
    ElMessage.error('加载新闻列表失败')
  } finally {
    loading.value = false
  }
}

async function handleApprove(row) {
  reviewLoading.value = true
  try {
    await reviewNews(row.id, { action: 'approve' })
    ElMessage.success('已恢复发布')
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    reviewLoading.value = false
  }
}

function openReject(row) {
  rejectTarget.value = row
  rejectMsg.value = ''
  rejectVisible.value = true
}

async function handleRejectSubmit() {
  if (!rejectMsg.value.trim()) {
    ElMessage.warning('请填写下架原因')
    return
  }
  reviewLoading.value = true
  try {
    await reviewNews(rejectTarget.value.id, { action: 'reject', message: rejectMsg.value })
    ElMessage.success('已下架')
    rejectVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    reviewLoading.value = false
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
</style>
