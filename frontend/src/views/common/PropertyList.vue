<template>
  <div class="page-container">
    <div class="page-header">
      <h2>房源列表</h2>
    </div>
    
    <!-- 搜索与筛选区 -->
    <div class="filter-form">
      <el-form :inline="true" :model="filters" class="filter-form-inner">
        <!-- 关键词搜索 -->
        <el-form-item label="搜索">
          <el-input v-model="filters.keyword" placeholder="标题/地址/小区/标签" clearable style="width: 220px" @keyup.enter="onFilterChange" />
        </el-form-item>
        
        <!-- 区域 -->
        <el-form-item label="区域">
          <el-input v-model="filters.region" placeholder="如：朝阳区" clearable style="width: 140px" />
        </el-form-item>
        
        <!-- 价格区间 -->
        <el-form-item label="价格">
          <el-input-number v-model="filters.rent_min" :min="0" placeholder="最低" style="width: 120px" controls-position="right" />
          <span style="margin: 0 8px">-</span>
          <el-input-number v-model="filters.rent_max" :min="0" placeholder="最高" style="width: 120px" controls-position="right" />
        </el-form-item>
        
        <!-- 房源类型 -->
        <el-form-item label="类型">
          <el-select v-model="filters.rental_type" clearable placeholder="全部" style="width: 100px">
            <el-option label="整租" value="整租" />
            <el-option label="合租" value="合租" />
            <el-option label="公寓" value="公寓" />
            <el-option label="商铺" value="商铺" />
          </el-select>
        </el-form-item>
        
        <!-- 户型（卧室数） -->
        <el-form-item label="户型">
          <el-select v-model="filters.bedrooms" clearable placeholder="全部" style="width: 90px">
            <el-option v-for="n in 5" :key="n" :label="n + '室'" :value="n" />
          </el-select>
        </el-form-item>
        
        <!-- 装修 -->
        <el-form-item label="装修">
          <el-select v-model="filters.decoration" clearable placeholder="全部" style="width: 90px">
            <el-option label="毛坯" value="毛坯" />
            <el-option label="简装" value="简装" />
            <el-option label="精装" value="精装" />
            <el-option label="豪装" value="豪装" />
          </el-select>
        </el-form-item>
        
        <!-- 排序 -->
        <el-form-item label="排序">
          <el-select v-model="filters.sort_by" @change="onFilterChange" style="width: 120px">
            <el-option label="综合排序" value="" />
            <el-option label="价格从低到高" value="price_asc" />
            <el-option label="价格从高到低" value="price_desc" />
            <el-option label="最新发布" value="newest" />
            <el-option label="最多浏览" value="views" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="onFilterChange">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <!-- 结果统计 -->
    <div class="result-info" v-if="!loading">
      <span>共找到 <strong>{{ total }}</strong> 套房源</span>
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
            <span>{{ p.area ? p.area + '㎡' : (p.building_area ? p.building_area + '㎡' : '-') }}</span>
          </div>
          <div class="tags">
            <el-tag size="small" v-if="p.region">{{ p.region }}</el-tag>
            <el-tag size="small" v-if="p.rental_type" type="warning">{{ p.rental_type }}</el-tag>
            <el-tag size="small" v-if="p.decoration" type="info">{{ p.decoration }}</el-tag>
            <span class="view-count" v-if="p.view_count > 0">
              <el-icon><View /></el-icon> {{ p.view_count }}
            </span>
          </div>
        </div>
      </el-card>
    </div>
    <el-empty v-if="!loading && properties.length === 0" description="未找到相关房源" />
    <div class="pagination-wrap" v-if="total > pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { View } from '@element-plus/icons-vue'
import { getProperties } from '../../api/property'

const properties = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = 12
const currentPage = ref(1)
const filters = reactive({ 
  keyword: '', region: '', floor_plan: '', 
  rent_min: null, rent_max: null,
  rental_type: '', bedrooms: null, decoration: '',
  sort_by: ''
})

const statusTypeMap = {
  published: 'success',
  unpublished: 'info',
  rented: 'warning'
}

function statusType(status) {
  return statusTypeMap[status] || 'info'
}

function getCoverImage(p) {
  if (p.images && p.images.length > 0) {
    const cover = p.images.find((i) => i.is_cover === 1)
    return cover?.image_url || p.images[0].image_url
  }
  return 'https://via.placeholder.com/300x200?text=No+Image'
}

function resetFilters() {
  filters.keyword = ''
  filters.region = ''
  filters.floor_plan = ''
  filters.rent_min = null
  filters.rent_max = null
  filters.rental_type = ''
  filters.bedrooms = null
  filters.decoration = ''
  filters.sort_by = ''
  currentPage.value = 1
  loadData()
}

function onFilterChange() {
  currentPage.value = 1
  loadData()
}

async function loadData() {
  loading.value = true
  try {
    const params = { skip: (currentPage.value - 1) * pageSize, limit: pageSize }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.region) params.region = filters.region
    if (filters.floor_plan) params.floor_plan = filters.floor_plan
    if (filters.rent_min != null) params.rent_min = filters.rent_min
    if (filters.rent_max != null) params.rent_max = filters.rent_max
    if (filters.rental_type) params.rental_type = filters.rental_type
    if (filters.bedrooms != null) params.bedrooms = filters.bedrooms
    if (filters.decoration) params.decoration = filters.decoration
    if (filters.sort_by) params.sort_by = filters.sort_by
    const res = await getProperties(params)
    properties.value = (res && res.items) || []
    total.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载房源列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.filter-form-inner {
  flex-wrap: wrap;
}

.result-info {
  margin-bottom: 16px;
  color: #606266;
  font-size: 14px;
}

.result-info strong {
  color: #409eff;
  font-size: 16px;
}

.view-count {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 2px;
}

.property-card {
  cursor: pointer;
}

.property-card .tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

/* Uses global .page-container, .page-header, .card-grid, .property-card, .filter-form, .pagination-wrap */
</style>
