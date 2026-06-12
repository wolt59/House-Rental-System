<template>
  <div class="page-container">
    <div class="page-header">
      <h2>⭐ 我的收藏</h2>
      <span class="header-sub">共 {{ total }} 套收藏房源</span>
    </div>

    <div v-loading="loading" class="card-grid">
      <el-card
        v-for="fav in favorites"
        :key="fav.id"
        shadow="hover"
        class="property-card"
        @click="goDetail(fav.property_id)"
      >
        <div class="card-img">
          <img :src="fav.property_cover || placeholder" alt="" />
        </div>
        <div class="card-info">
          <h3>{{ fav.property_title || '已下架房源' }}</h3>
          <p class="address">{{ fav.property_address || '-' }}</p>
          <div class="meta">
            <span class="rent">¥{{ fav.property_rent || 0 }}/月</span>
            <el-tag
              v-if="fav.property_status"
              size="small"
              :type="statusType(fav.property_status)"
            >
              {{ statusLabel(fav.property_status) }}
            </el-tag>
          </div>
          <div class="fav-actions">
            <span class="fav-time">
              <el-icon><Clock /></el-icon>
              收藏于 {{ formatDate(fav.created_at) }}
            </span>
            <el-button
              size="small"
              type="danger"
              plain
              @click.stop="handleRemove(fav)"
            >
              取消收藏
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <el-empty v-if="!loading && favorites.length === 0" description="还没有收藏任何房源">
      <el-button type="primary" @click="$router.push('/properties')">去看看房源</el-button>
    </el-empty>

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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock } from '@element-plus/icons-vue'
import { getMyFavorites, toggleFavorite } from '../../api/propertyInteraction'

const router = useRouter()
const favorites = ref([])
const total = ref(0)
const loading = ref(false)
const pageSize = 12
const currentPage = ref(1)

const placeholder =
  'data:image/svg+xml;charset=UTF-8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200"><rect fill="%23e8e8e8" width="300" height="200"/><text fill="%23999999" font-family="sans-serif" font-size="14" x="50%25" y="50%25" text-anchor="middle" dy=".3em">暂无图片</text></svg>'

const statusTypeMap = {
  published: 'success',
  unpublished: 'info',
  rented: 'warning',
  vacant: '',
  maintenance: 'info',
}
const statusLabelMap = {
  published: '可租',
  unpublished: '未发布',
  rented: '已出租',
  vacant: '空置',
  maintenance: '维护中',
}

function statusType(s) {
  return statusTypeMap[s] || 'info'
}
function statusLabel(s) {
  return statusLabelMap[s] || s || '-'
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

function goDetail(propertyId) {
  if (!propertyId) return
  router.push(`/properties/${propertyId}`)
}

async function loadData() {
  loading.value = true
  try {
    const res = await getMyFavorites({
      skip: (currentPage.value - 1) * pageSize,
      limit: pageSize,
    })
    favorites.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载收藏列表失败')
  } finally {
    loading.value = false
  }
}

async function handleRemove(fav) {
  try {
    await ElMessageBox.confirm('确定要取消收藏该房源吗？', '提示', {
      type: 'warning',
      confirmButtonText: '取消收藏',
      cancelButtonText: '再想想',
    })
  } catch {
    return
  }
  try {
    await toggleFavorite(fav.property_id)
    ElMessage.success('已取消收藏')
    await loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.header-sub {
  margin-left: 12px;
  color: #909399;
  font-size: 14px;
  font-weight: 400;
}

.property-card {
  cursor: pointer;
}

.property-card .meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.property-card .rent {
  font-size: 16px;
  font-weight: 700;
  color: #f56c6c;
}

.fav-actions {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 8px;
  border-top: 1px dashed #ebeef5;
}

.fav-time {
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
