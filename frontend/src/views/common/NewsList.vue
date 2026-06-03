<template>
  <div class="page-container">
    <div class="page-header">
      <h2>新闻资讯</h2>
    </div>

    <!-- 分类筛选 -->
    <div class="filter-bar">
      <el-radio-group v-model="activeCategory" @change="onCategoryChange" size="small">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="租赁资讯">租赁资讯</el-radio-button>
        <el-radio-button value="维修通知">维修通知</el-radio-button>
        <el-radio-button value="政策法规">政策法规</el-radio-button>
        <el-radio-button value="生活指南">生活指南</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 新闻列表 -->
    <div class="news-list" v-loading="loading">
      <div
        v-for="item in newsList"
        :key="item.id"
        class="news-item"
        @click="$router.push(`/news/${item.id}`)"
      >
        <div class="news-body">
          <div class="news-main">
            <h3 class="news-title">{{ item.title }}</h3>
            <p class="news-excerpt">{{ (item.content || '').substring(0, 160) }}{{ (item.content || '').length > 160 ? '...' : '' }}</p>
            <div class="news-meta">
              <el-tag size="small" effect="plain" v-if="item.category">{{ item.category }}</el-tag>
              <span class="meta-item">{{ item.author_name || '佚名' }}</span>
              <span class="meta-divider">·</span>
              <span class="meta-item">{{ formatDate(item.published_at || item.created_at) }}</span>
              <span class="meta-divider">·</span>
              <span class="meta-item">{{ item.view_count || 0 }} 阅读</span>
            </div>
          </div>
          <div class="news-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <el-empty v-if="!loading && newsList.length === 0" description="暂无新闻资讯" />

    <div class="pagination-wrap" v-if="total > pageSize">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="pageSize"
        v-model:current-page="currentPage"
        @current-change="loadData"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getNewsList } from '../../api/news'
import { ElMessage } from 'element-plus'
import { ArrowRight } from '@element-plus/icons-vue'

const newsList = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(15)
const currentPage = ref(1)
const activeCategory = ref('')

function formatDate(d) {
  if (!d) return ''
  const date = new Date(d)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) return '刚刚'
    return `${hours} 小时前`
  }
  if (days < 7) return `${days} 天前`
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

function onCategoryChange() {
  currentPage.value = 1
  loadData()
}

async function loadData() {
  loading.value = true
  try {
    const params = { skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value }
    if (activeCategory.value) params.category = activeCategory.value
    const res = await getNewsList(params)
    newsList.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载新闻列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.filter-bar {
  margin-bottom: 20px;
}

/* 新闻列表 */
.news-list {
  background: var(--bg-card);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.news-item {
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid var(--border);
}

.news-item:last-child {
  border-bottom: none;
}

.news-item:hover {
  background: var(--primary-bg);
}

.news-body {
  display: flex;
  align-items: center;
  padding: 18px 24px;
}

.news-main {
  flex: 1;
  min-width: 0;
}

.news-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.news-item:hover .news-title {
  color: var(--primary);
}

.news-excerpt {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 10px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-muted);
}

.meta-divider {
  color: #d0d5dd;
}

.news-arrow {
  flex-shrink: 0;
  margin-left: 16px;
  color: #c0c4cc;
  font-size: 18px;
  transition: transform 0.2s, color 0.2s;
}

.news-item:hover .news-arrow {
  transform: translateX(4px);
  color: var(--primary);
}
</style>
