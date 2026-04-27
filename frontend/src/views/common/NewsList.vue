<template>
  <div class="page-container">
    <div class="page-header"><h2>新闻资讯</h2></div>
    <el-row :gutter="16">
      <el-col :span="8" v-for="n in newsList" :key="n.id">
        <el-card shadow="hover" @click="$router.push(`/news/${n.id}`)" style="cursor: pointer; margin-bottom: 16px">
          <h4 style="margin-bottom: 8px">{{ n.title }}</h4>
          <p style="font-size: 13px; color: #909399; margin-bottom: 8px">{{ (n.content || '').substring(0, 80) }}...</p>
          <div style="font-size: 12px; color: #c0c4cc">
            <el-tag size="small" v-if="n.category">{{ n.category }}</el-tag>
            {{ formatDate(n.published_at || n.created_at) }}
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-if="newsList.length === 0" description="暂无新闻" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getNewsList } from '../../api/news'

const newsList = ref([])

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN')
}

onMounted(async () => {
  try {
    const res = await getNewsList({ skip: 0, limit: 20 })
    newsList.value = Array.isArray(res) ? res : []
  } catch (e) {}
})
</script>
