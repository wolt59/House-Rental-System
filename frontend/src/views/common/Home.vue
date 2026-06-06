<template>
  <div class="page-container" v-loading="loading">
    <div class="hero-section">
      <div class="hero-bg">
        <div class="hero-shape hero-shape-1"></div>
        <div class="hero-shape hero-shape-2"></div>
      </div>
      <div class="hero-content">
        <h1>找到您的理想居所</h1>
        <p>高效、便捷、安全的房屋租赁平台</p>
        <div class="hero-actions">
          <el-button type="primary" size="large" round @click="$router.push('/search')">开始搜索房源</el-button>
          <el-button size="large" round plain @click="$router.push('/properties')">浏览全部房源</el-button>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-header">
        <h2>最新房源</h2>
        <el-button text type="primary" @click="$router.push('/properties')">查看全部 →</el-button>
      </div>
      <div class="card-grid">
        <el-card v-for="p in properties" :key="p.id" shadow="hover" class="property-card" @click="$router.push(`/properties/${p.id}`)">
          <div class="card-img">
            <img :src="getCoverImage(p)" alt="" />
          </div>
          <div class="card-info">
            <h3>{{ p.title }}</h3>
            <p class="address">{{ p.address }}</p>
            <div class="meta">
              <span class="rent">¥{{ p.rent }}/月</span>
              <span v-if="p.floor_plan">· {{ p.floor_plan }}</span>
              <span v-if="p.area">· {{ p.area }}㎡</span>
            </div>
          </div>
        </el-card>
      </div>
      <el-empty v-if="!loading && properties.length === 0" description="暂无房源" />
    </div>

    <div class="section">
      <div class="section-header">
        <h2>新闻</h2>
        <el-button text type="primary" @click="$router.push('/news')">查看全部 →</el-button>
      </div>
      <el-row :gutter="20">
        <el-col :span="8" v-for="n in newsList" :key="n.id">
          <el-card shadow="hover" class="news-card" @click="$router.push(`/news/${n.id}`)">
            <div class="news-badge">{{ n.category || '资讯' }}</div>
            <h4>{{ n.title }}</h4>
            <p class="news-meta">{{ formatDate(n.published_at || n.created_at) }}</p>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-if="!loading && newsList.length === 0" description="暂无新闻" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getProperties } from '../../api/property'
import { getNewsList } from '../../api/news'
import { ElMessage } from 'element-plus'

const properties = ref([])
const newsList = ref([])
const loading = ref(false)

function getCoverImage(p) {
  if (p.images && p.images.length > 0) {
    const cover = p.images.find((i) => i.is_cover === 1)
    return cover?.image_url || p.images[0].image_url
  }
  return 'data:image/svg+xml;charset=UTF-8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200"><rect fill="%23e8e8e8" width="300" height="200"/><text fill="%23999999" font-family="sans-serif" font-size="14" x="50%25" y="50%25" text-anchor="middle" dy=".3em">暂无图片</text></svg>'
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN')
}

onMounted(async () => {
  loading.value = true
  try {
    const [pRes, nRes] = await Promise.all([
      getProperties({ skip: 0, limit: 6 }),
      getNewsList({ skip: 0, limit: 3 }),
    ])
    properties.value = Array.isArray(pRes) ? pRes : []
    newsList.value = nRes?.items || []
  } catch (e) {
    ElMessage.error('加载首页数据失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
/* ===== Hero ===== */
.hero-section {
  position: relative;
  overflow: hidden;
  padding: 80px 40px;
  border-radius: var(--radius-lg);
  margin-bottom: 32px;
  background: linear-gradient(135deg, #1e293b 0%, #334155 50%, #0f172a 100%);
}

.hero-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.hero-shape {
  position: absolute;
  border-radius: 50%;
}

.hero-shape-1 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, var(--primary), transparent);
  opacity: 0.15;
  top: -200px;
  right: -100px;
  animation: heroFloat 8s ease-in-out infinite;
}

.hero-shape-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #a78bfa, transparent);
  opacity: 0.1;
  bottom: -100px;
  left: 10%;
  animation: heroFloat 10s ease-in-out infinite reverse;
}

@keyframes heroFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(20px, -20px) scale(1.1); }
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
  color: #fff;
}

.hero-content h1 {
  font-size: 40px;
  font-weight: 800;
  margin-bottom: 12px;
  letter-spacing: -0.5px;
}

.hero-content p {
  font-size: 18px;
  opacity: 0.8;
  margin-bottom: 32px;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.hero-actions .el-button--primary {
  height: 48px;
  padding: 0 32px;
  font-size: 16px;
}

.hero-actions .el-button--default.is-plain {
  height: 48px;
  padding: 0 32px;
  font-size: 16px;
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
  background: transparent;
}

.hero-actions .el-button--default.is-plain:hover {
  border-color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

/* ===== Sections ===== */
.section { margin-bottom: 32px; }

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

/* ===== Property Card ===== */
.property-card {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  overflow: hidden;
}

.property-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg) !important;
}

.card-img {
  height: 200px;
  overflow: hidden;
  border-radius: var(--radius) var(--radius) 0 0;
}

.card-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.property-card:hover .card-img img { transform: scale(1.08); }

.card-info { padding: 16px; }

.card-info h3 {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-info .address {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-info .meta {
  font-size: 13px;
  color: var(--text-secondary);
}

.card-info .meta .rent {
  color: var(--danger);
  font-weight: 700;
  font-size: 18px;
}

/* ===== News Card ===== */
.news-card {
  cursor: pointer;
  transition: all 0.3s;
  border-radius: var(--radius) !important;
  height: 100%;
}

.news-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg) !important;
}

.news-badge {
  display: inline-block;
  padding: 2px 10px;
  background: var(--primary-bg);
  color: var(--primary);
  font-size: 12px;
  font-weight: 600;
  border-radius: 20px;
  margin-bottom: 12px;
}

.news-card h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
  line-height: 1.4;
}

.news-meta {
  font-size: 13px;
  color: var(--text-muted);
}
</style>
