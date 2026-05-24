<template>
  <div class="page-container">
    <div class="page-header">
      <h2>房源列表</h2>
    </div>
    <div class="filter-form">
      <el-form :inline="true" :model="filters">
        <el-form-item label="区域">
          <el-input v-model="filters.region" placeholder="区域/商圈" clearable />
        </el-form-item>
        <el-form-item label="户型">
          <el-input v-model="filters.floor_plan" placeholder="如：2室1厅" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>
    <div class="card-grid" v-loading="loading">
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
          <div class="tags">
            <el-tag size="small" v-if="p.region">{{ p.region }}</el-tag>
            <el-tag size="small" :type="p.status === 'vacant' ? 'success' : 'warning'">
              {{ p.status === 'vacant' ? '空置' : '已出租' }}
            </el-tag>
          </div>
        </div>
      </el-card>
    </div>
    <el-empty v-if="!loading && properties.length === 0" description="暂无房源" />
    <div class="pagination-wrap" v-if="total > pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getProperties } from '../../api/property'

const properties = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = 12
const currentPage = ref(1)
const filters = reactive({ region: '', floor_plan: '' })

function getCoverImage(p) {
  if (p.images && p.images.length > 0) {
    const cover = p.images.find((i) => i.is_cover === 1)
    return cover?.image_url || p.images[0].image_url
  }
  return 'https://via.placeholder.com/300x200?text=No+Image'
}

function resetFilters() {
  filters.region = ''
  filters.floor_plan = ''
  currentPage.value = 1
  loadData()
}

async function loadData() {
  loading.value = true
  try {
    const params = { skip: (currentPage.value - 1) * pageSize, limit: pageSize }
    if (filters.region) params.region = filters.region
    if (filters.floor_plan) params.floor_plan = filters.floor_plan
    const res = await getProperties(params)
    properties.value = Array.isArray(res) ? res : []
    total.value = properties.value.length
  } catch (e) {
    ElMessage.error('加载房源列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
/* Uses global .page-container, .page-header, .card-grid, .property-card, .filter-form, .pagination-wrap */
</style>
