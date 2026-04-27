<template>
  <div class="page-container" v-loading="loading">
    <el-page-header @back="$router.back()" content="新闻详情" />
    <el-card style="margin-top: 20px" v-if="news">
      <h2>{{ news.title }}</h2>
      <div style="color: #909399; font-size: 13px; margin: 12px 0">
        <el-tag size="small" v-if="news.category">{{ news.category }}</el-tag>
        发布于 {{ formatDate(news.published_at || news.created_at) }}
      </div>
      <el-divider />
      <div class="news-content">{{ news.content }}</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getNews } from '../../api/news'

const route = useRoute()
const news = ref(null)
const loading = ref(false)

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN')
}

onMounted(async () => {
  loading.value = true
  try {
    news.value = await getNews(route.params.id)
  } catch (e) {} finally {
    loading.value = false
  }
})
</script>

<style scoped>
.news-content {
  font-size: 15px;
  line-height: 1.8;
  color: #303133;
  white-space: pre-wrap;
}
</style>
