<template>
  <div class="detail-page" v-loading="loading">
    <!-- 返回栏 -->
    <div class="detail-topbar">
      <el-button text @click="$router.back()" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>返回
      </el-button>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: '/news' }">新闻资讯</el-breadcrumb-item>
        <el-breadcrumb-item>{{ news?.title || '详情' }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div v-if="news" class="detail-container">
      <!-- 文章头部 -->
      <div class="article-header">
        <el-tag effect="dark" round size="large" class="header-tag">{{ news.category || '综合' }}</el-tag>
        <h1 class="article-title">{{ news.title }}</h1>
        <div class="article-meta">
          <div class="meta-left">
            <el-avatar :size="40" class="author-avatar">
              {{ (news.author_name || '佚')[0] }}
            </el-avatar>
            <div class="meta-info">
              <span class="meta-author-name">{{ news.author_name || '佚名' }}</span>
              <span class="meta-time">
                <el-icon><Clock /></el-icon>
                {{ formatFullDate(news.published_at || news.created_at) }}
                <span class="meta-dot">·</span>
                <el-icon><View /></el-icon>
                {{ news.view_count || 0 }} 阅读
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 文章内容 -->
      <div class="article-body">
        <div class="article-content" v-html="renderedContent"></div>
      </div>

      <!-- 底部信息 -->
      <el-divider />
      <div class="article-footer">
        <span>发布于 {{ formatFullDate(news.published_at || news.created_at) }}</span>
        <span>最后更新于 {{ formatFullDate(news.updated_at) }}</span>
      </div>

      <!-- 回到顶部 -->
      <el-backtop :right="40" :bottom="40" />
    </div>

    <!-- 加载失败 -->
    <el-empty v-if="!loading && !news" description="新闻不存在或已删除">
      <el-button type="primary" @click="$router.push('/news')">返回新闻列表</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getNews } from '../../api/news'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Clock, View } from '@element-plus/icons-vue'

const route = useRoute()
const news = ref(null)
const loading = ref(false)

const renderedContent = computed(() => {
  if (!news.value?.content) return ''
  return news.value.content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
})

function formatFullDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(async () => {
  loading.value = true
  try {
    news.value = await getNews(route.params.id)
  } catch (e) {
    ElMessage.error('加载新闻详情失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.detail-page {
  min-height: calc(100vh - var(--header-height));
  background: #f8fafc;
}

.detail-topbar {
  max-width: 860px;
  margin: 0 auto;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  font-size: 14px;
  color: #64748b;
}

.detail-container {
  max-width: 860px;
  margin: 0 auto;
  padding: 0 24px 60px;
}

/* Article Header */
.article-header {
  background: #fff;
  border-radius: 16px;
  padding: 40px 48px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.header-tag {
  margin-bottom: 20px;
  font-size: 13px;
}

.article-title {
  font-size: 32px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.35;
  margin: 0 0 24px;
  letter-spacing: 0.5px;
}

.article-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
}

.meta-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.author-avatar {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-weight: 700;
  font-size: 16px;
}

.meta-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-author-name {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}

.meta-time {
  font-size: 13px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-dot {
  margin: 0 4px;
}

/* Article Body */
.article-body {
  margin-top: 24px;
  background: #fff;
  border-radius: 16px;
  padding: 40px 48px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.article-content {
  font-size: 16px;
  line-height: 2;
  color: #334155;
  word-wrap: break-word;
}

/* Article Footer */
.article-footer {
  text-align: center;
  font-size: 13px;
  color: #94a3b8;
  display: flex;
  justify-content: center;
  gap: 24px;
  padding: 8px 0;
}
</style>
