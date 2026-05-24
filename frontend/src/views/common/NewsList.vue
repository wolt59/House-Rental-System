<template>
  <div class="page-container" v-loading="loading">
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
    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getNewsList } from '../../api/news'
import { ElMessage } from 'element-plus'

const newsList = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    const res = await getNewsList({ skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value })
    newsList.value = Array.isArray(res) ? res : []
    total.value = Array.isArray(res) ? res.length : 0
  } catch (e) {
    ElMessage.error('加载新闻列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
</style>
