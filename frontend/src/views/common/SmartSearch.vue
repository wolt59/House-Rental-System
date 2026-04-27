<template>
  <div class="page-container">
    <div class="page-header"><h2>智能搜索</h2></div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="按地区搜索" name="region">
        <el-table :data="regionStats" stripe v-loading="regionLoading">
          <el-table-column prop="region" label="区域/商圈" />
          <el-table-column prop="property_count" label="房源数量" width="120" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="searchByRegion(row.region)">查看房源</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="按户型搜索" name="floor_plan">
        <el-table :data="floorPlanStats" stripe v-loading="fpLoading">
          <el-table-column prop="floor_plan" label="户型" />
          <el-table-column prop="property_count" label="房源数量" width="120" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="searchByFloorPlan(row.floor_plan)">查看房源</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <div v-if="searchResults.length > 0" style="margin-top: 24px">
      <h3 style="margin-bottom: 12px">搜索结果</h3>
      <div class="card-grid">
        <el-card v-for="p in searchResults" :key="p.id" shadow="hover" class="property-card" @click="$router.push(`/properties/${p.id}`)">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getRegionStats, getFloorPlanStats } from '../../api/stats'
import { getProperties } from '../../api/property'

const activeTab = ref('region')
const regionStats = ref([])
const floorPlanStats = ref([])
const searchResults = ref([])
const regionLoading = ref(false)
const fpLoading = ref(false)

function getCoverImage(p) {
  if (p.images && p.images.length > 0) {
    const cover = p.images.find((i) => i.is_cover === 1)
    return cover?.image_url || p.images[0].image_url
  }
  return 'https://via.placeholder.com/300x200?text=No+Image'
}

async function searchByRegion(region) {
  try {
    const res = await getProperties({ region, limit: 20 })
    searchResults.value = Array.isArray(res) ? res : []
  } catch (e) {}
}

async function searchByFloorPlan(floor_plan) {
  try {
    const res = await getProperties({ floor_plan, limit: 20 })
    searchResults.value = Array.isArray(res) ? res : []
  } catch (e) {}
}

onMounted(async () => {
  regionLoading.value = true
  fpLoading.value = true
  try {
    const [rRes, fRes] = await Promise.all([getRegionStats(), getFloorPlanStats()])
    regionStats.value = Array.isArray(rRes) ? rRes : []
    floorPlanStats.value = Array.isArray(fRes) ? fRes : []
  } catch (e) {} finally {
    regionLoading.value = false
    fpLoading.value = false
  }
})
</script>

<style scoped>
.property-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.property-card:hover {
  transform: translateY(-4px);
}
.card-img {
  height: 160px;
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
  font-size: 15px;
  margin-bottom: 4px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-info .address {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}
.card-info .meta {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #606266;
}
.card-info .meta .rent {
  color: #f56c6c;
  font-weight: bold;
  font-size: 15px;
}
</style>
