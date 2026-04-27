<template>
  <div class="page-container">
    <div class="hero-section">
      <h1>🏠 智能房屋租赁系统</h1>
      <p>高效、便捷、智能的房屋租赁平台</p>
      <el-button type="primary" size="large" @click="$router.push('/search')">开始搜索房源</el-button>
    </div>

    <div class="section">
      <div class="page-header">
        <h2>最新房源</h2>
        <el-button text type="primary" @click="$router.push('/properties')">查看更多 →</el-button>
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
              <span>{{ p.floor_plan || '-' }}</span>
              <span>{{ p.area ? p.area + '㎡' : '-' }}</span>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <div class="section">
      <div class="page-header">
        <h2>新闻资讯</h2>
        <el-button text type="primary" @click="$router.push('/news')">查看更多 →</el-button>
      </div>
      <el-row :gutter="16">
        <el-col :span="8" v-for="n in newsList" :key="n.id">
          <el-card shadow="hover" @click="$router.push(`/news/${n.id}`)" style="cursor: pointer">
            <h4>{{ n.title }}</h4>
            <p class="news-meta">{{ n.category || '资讯' }} · {{ formatDate(n.published_at || n.created_at) }}</p>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getProperties } from '../../api/property'
import { getNewsList } from '../../api/news'

const properties = ref([])
const newsList = ref([])

function getCoverImage(p) {
  if (p.images && p.images.length > 0) {
    const cover = p.images.find((i) => i.is_cover === 1)
    return cover?.image_url || p.images[0].image_url
  }
  return 'https://via.placeholder.com/300x200?text=No+Image'
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN')
}

onMounted(async () => {
  try {
    const [pRes, nRes] = await Promise.all([
      getProperties({ skip: 0, limit: 6 }),
      getNewsList({ skip: 0, limit: 3 }),
    ])
    properties.value = Array.isArray(pRes) ? pRes : []
    newsList.value = Array.isArray(nRes) ? nRes : []
  } catch (e) {}
})
</script>

<style scoped>
.hero-section {
  text-align: center;
  padding: 60px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: #fff;
  margin-bottom: 30px;
}
.hero-section h1 {
  font-size: 36px;
  margin-bottom: 12px;
}
.hero-section p {
  font-size: 18px;
  margin-bottom: 24px;
  opacity: 0.9;
}
.section {
  margin-bottom: 30px;
}
.property-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.property-card:hover {
  transform: translateY(-4px);
}
.card-img {
  height: 180px;
  overflow: hidden;
  border-radius: 4px;
  margin-bottom: 12px;
}
.card-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.card-info h3 {
  font-size: 16px;
  margin-bottom: 4px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-info .address {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}
.card-info .meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #606266;
}
.card-info .meta .rent {
  color: #f56c6c;
  font-weight: bold;
  font-size: 16px;
}
.news-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}
</style>
