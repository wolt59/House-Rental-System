<template>
  <div class="page-container" v-loading="loading">
    <el-page-header @back="$router.back()" :content="property.title || '房源详情'" />

    <el-row :gutter="24" style="margin-top: 24px">
      <!-- 左侧：图片展示区 -->
      <el-col :span="16">
        <el-card class="image-card">
          <div class="image-gallery">
            <div class="main-image">
              <img :src="currentImage" alt="房源图片" />
            </div>
            <div class="thumb-list" v-if="property.images && property.images.length > 1">
              <img
                v-for="img in property.images"
                :key="img.id"
                :src="img.image_url"
                :class="{ active: currentImage === img.image_url }"
                @click="currentImage = img.image_url"
                class="thumb"
              />
            </div>
          </div>
        </el-card>

        <!-- 房源描述 -->
        <el-card class="section-card" v-if="property.description">
          <div class="section-header">
            <h3>📝 房源描述</h3>
          </div>
          <div class="section-content">
            <p>{{ property.description }}</p>
          </div>
        </el-card>

        <!-- 室内配套设施 -->
        <el-card class="section-card" v-if="property.facilities">
          <div class="section-header">
            <h3>🛋️ 室内配套设施</h3>
          </div>
          <div class="section-content">
            <p>{{ property.facilities }}</p>
          </div>
        </el-card>

        <!-- 周边配套 -->
        <el-card class="section-card" v-if="property.surrounding">
          <div class="section-header">
            <h3>🌳 周边配套</h3>
          </div>
          <div class="section-content">
            <p>{{ property.surrounding }}</p>
          </div>
        </el-card>

        <!-- 看房时间 -->
        <el-card class="section-card" v-if="property.viewing_time_rules">
          <div class="section-header">
            <h3> 看房时间</h3>
          </div>
          <div class="section-content">
            <p>{{ property.viewing_time_rules }}</p>
          </div>
        </el-card>

        <!-- 房东备注 -->
        <el-card class="section-card" v-if="property.landlord_notes">
          <div class="section-header">
            <h3>💬 房东备注</h3>
          </div>
          <div class="section-content notes-content">
            <p>{{ property.landlord_notes }}</p>
          </div>
        </el-card>

        <!-- 评论区 -->
        <el-card class="section-card">
          <div class="section-header comment-header">
            <h3>💭 房源评论 <span class="comment-count">({{ commentTotal }})</span></h3>
          </div>

          <!-- 发表评论 -->
          <div v-if="userStore.isLoggedIn" class="comment-composer">
            <el-input
              v-model="newComment"
              type="textarea"
              :rows="3"
              :maxlength="1000"
              show-word-limit
              placeholder="说点什么吧…（最多 1000 字）"
            />
            <div class="comment-composer-actions">
              <el-button type="primary" :loading="commentSubmitting" @click="handlePostComment">发表评论</el-button>
            </div>
          </div>
          <div v-else class="comment-login-tip">
            <el-button type="primary" link @click="$router.push('/login')">登录</el-button>
            <span>后即可参与评论</span>
          </div>

          <!-- 评论列表 -->
          <div v-loading="commentsLoading" class="comment-list">
            <el-empty v-if="!commentsLoading && comments.length === 0" description="暂无评论，快来抢沙发吧~" :image-size="80" />
            <div v-for="c in comments" :key="c.id" class="comment-item">
              <el-avatar :size="40" :src="c.user_avatar" class="comment-avatar">
                {{ (c.user_name || '?')[0] }}
              </el-avatar>
              <div class="comment-body">
                <div class="comment-meta">
                  <span class="comment-author">{{ c.user_name || '匿名用户' }}</span>
                  <el-tag v-if="c.user_role" size="small" :type="roleTagType(c.user_role)" effect="light" round>
                    {{ roleLabel(c.user_role) }}
                  </el-tag>
                  <span class="comment-time">{{ formatDate(c.created_at) }}</span>
                </div>
                <div v-if="editingCommentId === c.id" class="comment-edit">
                  <el-input
                    v-model="editingContent"
                    type="textarea"
                    :rows="2"
                    :maxlength="1000"
                    show-word-limit
                  />
                  <div class="comment-edit-actions">
                    <el-button size="small" @click="cancelEditComment">取消</el-button>
                    <el-button size="small" type="primary" :loading="editSubmitting" @click="handleUpdateComment(c)">保存</el-button>
                  </div>
                </div>
                <div v-else class="comment-content">{{ c.content }}</div>
                <div v-if="canManageComment(c)" class="comment-actions">
                  <el-button v-if="editingCommentId !== c.id" link type="primary" @click="startEditComment(c)">编辑</el-button>
                  <el-popconfirm title="确定要删除这条评论吗？" @confirm="handleDeleteComment(c)">
                    <template #reference>
                      <el-button link type="danger">删除</el-button>
                    </template>
                  </el-popconfirm>
                </div>
              </div>
            </div>
            <div v-if="commentTotal > commentPageSize" class="comment-pagination">
              <el-pagination
                background
                layout="prev, pager, next"
                :total="commentTotal"
                :page-size="commentPageSize"
                v-model:current-page="commentCurrentPage"
                @current-change="loadComments"
              />
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：信息展示区 -->
      <el-col :span="8">
        <!-- 核心信息卡片 -->
        <el-card class="info-card">
          <h2 class="property-title">{{ property.title }}</h2>
          
          <div class="price-tag">
            <span class="price-value">¥{{ property.rent }}</span>
            <span class="price-unit">/月</span>
          </div>

          <!-- 浏览量 -->
          <div class="view-stats" v-if="property.view_count !== undefined">
            <el-icon><View /></el-icon>
            <span>{{ property.view_count }} 次浏览</span>
          </div>

          <!-- 特色标签 -->
          <div class="tags-container" v-if="property.tags">
            <el-tag 
              v-for="tag in property.tags.split(',')" 
              :key="tag" 
              size="default" 
              class="tag-item"
              effect="light"
              type="success"
            >
              {{ tag.trim() }}
            </el-tag>
          </div>

          <!-- 基本信息网格 -->
          <div class="info-grid">
            <!-- 位置信息 -->
            <div class="info-item">
              <div class="info-label">地址</div>
              <div class="info-value">{{ property.address }}</div>
            </div>
            
            <div class="info-row">
              <div class="info-item">
                <div class="info-label">城市</div>
                <div class="info-value">{{ property.city || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">区域</div>
                <div class="info-value">{{ property.region || '-' }}</div>
              </div>
            </div>

            <div class="info-item" v-if="property.community_name">
              <div class="info-label">小区</div>
              <div class="info-value">{{ property.community_name }}</div>
            </div>

            <!-- 房屋物理属性 -->
            <div class="info-row">
              <div class="info-item">
                <div class="info-label">类型</div>
                <div class="info-value">{{ property.rental_type || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">户型</div>
                <div class="info-value">{{ property.floor_plan || '-' }}</div>
              </div>
            </div>

            <div class="info-row">
              <div class="info-item">
                <div class="info-label">建筑面积</div>
                <div class="info-value">{{ property.building_area ? property.building_area + '㎡' : '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">朝向</div>
                <div class="info-value">{{ property.orientation || '-' }}</div>
              </div>
            </div>

            <div class="info-row">
              <div class="info-item">
                <div class="info-label">楼层</div>
                <div class="info-value">{{ formatFloorNumber(property) }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">装修</div>
                <div class="info-value">{{ property.decoration || '-' }}</div>
              </div>
            </div>
          </div>

          <!-- 租赁信息 -->
          <div class="divider"></div>
          <h4 class="subsection-title">💰 租赁信息</h4>
          <div class="info-grid">
            <div class="info-row">
              <div class="info-item">
                <div class="info-label">押金</div>
                <div class="info-value">{{ property.deposit ? '¥' + property.deposit : '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">付款方式</div>
                <div class="info-value">{{ property.payment_method || '-' }}</div>
              </div>
            </div>

            <div class="info-row">
              <div class="info-item">
                <div class="info-label">最短租期</div>
                <div class="info-value">{{ property.min_lease_term ? property.min_lease_term + '个月' : '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">最早入住</div>
                <div class="info-value">{{ property.earliest_move_in_date || '-' }}</div>
              </div>
            </div>

            <div class="info-row">
              <div class="info-item">
                <div class="info-label">物业费</div>
                <div class="info-value">{{ property.property_fee_bearer || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">水电燃气</div>
                <div class="info-value">{{ property.utility_fee_bearer || '-' }}</div>
              </div>
            </div>

            <div class="info-row">
              <div class="info-item">
                <div class="info-label">其他费用</div>
                <div class="info-value">{{ property.other_fee_bearer || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">允许宠物</div>
                <div class="info-value">{{ property.allow_pets === 1 ? '✓ 允许' : '✗ 不允许' }}</div>
              </div>
            </div>
          </div>

          <!-- 补充信息 -->
          <div class="divider" v-if="hasSupplementInfo"></div>
          <h4 class="subsection-title" v-if="hasSupplementInfo">🏢 房屋补充信息</h4>
          <div class="info-grid" v-if="hasSupplementInfo">
            <div class="info-row">
              <div class="info-item">
                <div class="info-label">建筑年代</div>
                <div class="info-value">{{ property.build_year || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">电梯配置</div>
                <div class="info-value">{{ property.has_elevator === 1 ? '有电梯' : (property.has_elevator === 0 ? '无电梯' : '-') }}</div>
              </div>
            </div>

            <div class="info-row">
              <div class="info-item">
                <div class="info-label">总户数</div>
                <div class="info-value">{{ property.total_households || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">物业类型</div>
                <div class="info-value">{{ property.property_management_type || '-' }}</div>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons" v-if="userStore.isLoggedIn">
            <div
              class="action-btn"
              :class="isFavorited ? 'action-btn-favorited' : 'action-btn-default'"
              @click="handleToggleFavorite"
            >
              <el-icon class="btn-icon">
                <component :is="isFavorited ? StarFilled : Star" />
              </el-icon>
              <span>{{ isFavorited ? '已收藏' : '收藏房源' }} ({{ favoriteCount }})</span>
            </div>
            <template v-if="userStore.isTenant">
              <div class="action-btn action-btn-primary" @click="showBookingDialog = true">
                <el-icon class="btn-icon"><Calendar /></el-icon>
                <span>预约看房</span>
              </div>
              <div class="action-btn action-btn-default" @click="goToChat">
                <el-icon class="btn-icon"><ChatDotRound /></el-icon>
                <span>联系房东</span>
              </div>
            </template>
          </div>
          <div v-else class="action-buttons">
            <el-button type="primary" round @click="$router.push('/login')">登录后收藏与评论</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 预约看房弹窗 -->
    <el-dialog v-model="showBookingDialog" title="预约看房" width="600px">
      <el-form ref="bookingFormRef" :model="bookingForm" label-width="90px" :rules="bookingRules">
        <el-row :gutter="16">
          <el-col :span="24">
            <el-form-item label="预约时间" prop="appointment_time">
              <el-date-picker 
                v-model="bookingForm.appointment_time" 
                type="datetime" 
                placeholder="选择日期和时间" 
                style="width: 100%" 
                :disabled-date="d => {
                  const today = new Date(new Date().toDateString());
                  const maxDate = new Date(today.getTime() + 30 * 86400000);
                  return d.getTime() < today.getTime() || d.getTime() > maxDate.getTime();
                }" 
                :default-time="new Date(2000, 1, 1, 10, 0, 0)"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="补充留言">
          <el-input v-model="bookingForm.note" type="textarea" :rows="3" placeholder="如有特殊需求请备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBookingDialog = false">取消</el-button>
        <el-button type="primary" :loading="bookingLoading" @click="handleBooking">确认预约</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../../store/user'
import { getProperty } from '../../api/property'
import { createBooking } from '../../api/booking'
import {
  getPropertySummary,
  toggleFavorite,
  getPropertyComments,
  createPropertyComment,
  updatePropertyComment,
  deletePropertyComment,
} from '../../api/propertyInteraction'
import { ElMessage } from 'element-plus'
import { Calendar, ChatDotRound, View, Star, StarFilled } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const property = ref({})
const loading = ref(false)
const currentImage = ref('')
const showBookingDialog = ref(false)
const bookingLoading = ref(false)

const bookingForm = ref({ appointment_time: '', note: '' })
const bookingFormRef = ref(null)

const bookingRules = {
  appointment_time: [{ required: true, message: '请选择预约时间', trigger: 'change' }],
}

// 收藏 / 评论 相关状态
const isFavorited = ref(false)
const favoriteCount = ref(0)
const favoriteLoading = ref(false)

const comments = ref([])
const commentsLoading = ref(false)
const commentTotal = ref(0)
const commentPageSize = 10
const commentCurrentPage = ref(1)
const newComment = ref('')
const commentSubmitting = ref(false)
const editingCommentId = ref(null)
const editingContent = ref('')
const editSubmitting = ref(false)

function formatLocalISO(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

const statusType = computed(() => {
  const map = { 
    published: 'success', 
    unpublished: 'info',
    rented: 'warning'
  }
  return map[property.value.status] || 'info'
})
const statusLabel = computed(() => {
  const map = { 
    published: '已发布', 
    unpublished: '未发布',
    rented: '已出租'
  }
  return map[property.value.status] || property.value.status
})

// 判断是否有补充信息
const hasSupplementInfo = computed(() => {
  return property.value.build_year || 
         property.value.has_elevator !== null || 
         property.value.total_households || 
         property.value.property_management_type
})

// 格式化楼层显示
function formatFloorNumber(property) {
  if (property.floor_number && property.total_floors) {
    return `${property.floor_number}/${property.total_floors}`
  }
  return property.floor_number || '-'
}

async function loadData() {
  loading.value = true
  try {
    const res = await getProperty(route.params.id)
    property.value = res
    if (res.images && res.images.length > 0) {
      const cover = res.images.find((i) => i.is_cover === 1)
      currentImage.value = cover?.image_url || res.images[0].image_url
    } else {
      currentImage.value = 'data:image/svg+xml;charset=UTF-8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400"><rect fill="%23e8e8e8" width="600" height="400"/><text fill="%23999999" font-family="sans-serif" font-size="18" x="50%25" y="50%25" text-anchor="middle" dy=".3em">暂无图片</text></svg>'
    }
  } catch (e) {
    ElMessage.error('加载房源详情失败')
  } finally {
    loading.value = false
  }

  // 加载交互信息（收藏/评论摘要）和评论列表
  await Promise.all([loadSummary(), loadComments()])
}

async function loadSummary() {
  if (!userStore.isLoggedIn) return
  try {
    const res = await getPropertySummary(route.params.id)
    isFavorited.value = !!res.is_favorited
    favoriteCount.value = res.favorite_count || 0
  } catch (e) {
    // 静默失败：交互信息非核心
  }
}

async function loadComments() {
  commentsLoading.value = true
  try {
    const res = await getPropertyComments(route.params.id, {
      skip: (commentCurrentPage.value - 1) * commentPageSize,
      limit: commentPageSize,
    })
    comments.value = res.items || []
    commentTotal.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载评论失败')
  } finally {
    commentsLoading.value = false
  }
}

async function handleToggleFavorite() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  favoriteLoading.value = true
  try {
    const res = await toggleFavorite(parseInt(route.params.id))
    isFavorited.value = !!res.is_favorited
    favoriteCount.value = res.favorite_count || 0
    ElMessage.success(res.is_favorited ? '已加入收藏' : '已取消收藏')
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    favoriteLoading.value = false
  }
}

async function handlePostComment() {
  const content = newComment.value.trim()
  if (!content) {
    ElMessage.warning('评论内容不能为空')
    return
  }
  commentSubmitting.value = true
  try {
    await createPropertyComment({
      property_id: parseInt(route.params.id),
      content,
    })
    newComment.value = ''
    commentCurrentPage.value = 1
    await loadComments()
    ElMessage.success('评论发表成功')
  } catch (e) {
    ElMessage.error('发表评论失败')
  } finally {
    commentSubmitting.value = false
  }
}

function startEditComment(c) {
  editingCommentId.value = c.id
  editingContent.value = c.content
}

function cancelEditComment() {
  editingCommentId.value = null
  editingContent.value = ''
}

async function handleUpdateComment(c) {
  const content = (editingContent.value || '').trim()
  if (!content) {
    ElMessage.warning('评论内容不能为空')
    return
  }
  editSubmitting.value = true
  try {
    await updatePropertyComment(c.id, { content })
    c.content = content
    cancelEditComment()
    ElMessage.success('已更新')
  } catch (e) {
    ElMessage.error('更新失败')
  } finally {
    editSubmitting.value = false
  }
}

async function handleDeleteComment(c) {
  try {
    await deletePropertyComment(c.id)
    ElMessage.success('已删除')
    await loadComments()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function canManageComment(c) {
  if (!userStore.isLoggedIn) return false
  if (userStore.isAdmin) return true
  return c.user_id === userStore.user?.id
}

function roleTagType(role) {
  return { admin: 'danger', landlord: 'warning', tenant: 'primary' }[role] || 'info'
}

function roleLabel(role) {
  return { admin: '管理员', landlord: '房东', tenant: '租客' }[role] || role
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

async function handleBooking() {
  const valid = await bookingFormRef.value.validate().catch(() => false)
  if (!valid) return
  bookingLoading.value = true
  try {
    await createBooking({
      property_id: parseInt(route.params.id),
      appointment_time: formatLocalISO(bookingForm.value.appointment_time),
      note: bookingForm.value.note,
    })
    ElMessage.success('预约成功')
    showBookingDialog.value = false
    bookingForm.value = { appointment_time: '', note: '' }
  } catch (e) {
    ElMessage.error('预约失败')
  } finally {
    bookingLoading.value = false
  }
}

function goToChat() {
  if (!userStore.isLoggedIn) {
    router.push('/login')
    return
  }
  router.push({ path: '/messages', query: { with: property.value.owner_id } })
}

onMounted(loadData)
</script>

<style scoped>
/* 图片展示区 */
.image-card {
  margin-bottom: 24px;
}

.image-gallery .main-image {
  height: 480px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
  background: #f5f7fa;
}

.image-gallery .main-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.thumb-list {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.thumb {
  width: 100px;
  height: 75px;
  object-fit: cover;
  border-radius: 6px;
  cursor: pointer;
  border: 3px solid transparent;
  transition: all 0.3s;
  flex-shrink: 0;
}

.thumb:hover {
  opacity: 0.8;
  transform: scale(1.05);
}

.thumb.active {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

/* 内容卡片 */
.section-card {
  margin-bottom: 24px;
}

.section-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #409eff;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.section-content {
  color: #606266;
  font-size: 15px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.notes-content {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  border-left: 4px solid #e6a23c;
}

/* 信息展示卡片 */
.info-card {
  position: sticky;
  top: 20px;
}

.property-title {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
  line-height: 1.4;
}

.price-tag {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.view-stats {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 13px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.view-stats .el-icon {
  font-size: 14px;
}

.price-value {
  font-size: 32px;
  font-weight: bold;
  color: #f56c6c;
}

.price-unit {
  font-size: 16px;
  color: #909399;
  margin-left: 4px;
}

/* 标签 */
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.tag-item {
  margin: 0 !important;
}

/* 信息网格 */
.info-grid {
  margin-bottom: 16px;
}

.info-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}

.info-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  transition: all 0.3s;
}

.info-item:hover {
  background: #e8f4ff;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.info-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
  word-break: break-word;
}

/* 分割线 */
.divider {
  height: 1px;
  background: #ebeef5;
  margin: 20px 0;
}

.subsection-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
}

/* 操作按钮 */
.action-buttons {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  padding: 0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  user-select: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.action-btn-primary {
  background: #409eff;
  color: #fff;
  border: 2px solid #409eff;
}

.action-btn-primary:hover {
  background: #66b1ff;
  border-color: #66b1ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

.action-btn-default {
  background: #fff;
  color: #606266;
  border: 2px solid #dcdfe6;
}

.action-btn-default:hover {
  color: #409eff;
  border-color: #409eff;
  background: #ecf5ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.btn-icon {
  font-size: 18px;
  flex-shrink: 0;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .image-gallery .main-image {
    height: 360px;
  }
}

@media (max-width: 768px) {
  .info-row {
    grid-template-columns: 1fr;
  }

  .image-gallery .main-image {
    height: 240px;
  }
}

/* 收藏按钮 - 已收藏高亮态 */
.action-btn-favorited {
  background: #fef0f0;
  color: #f56c6c;
  border: 2px solid #f56c6c;
}
.action-btn-favorited:hover {
  background: #fde2e2;
  border-color: #f56c6c;
  color: #f56c6c;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.25);
}

/* 评论区 */
.comment-header h3 {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.comment-count {
  font-size: 13px;
  font-weight: 400;
  color: #909399;
}

.comment-composer {
  margin-bottom: 20px;
}
.comment-composer-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}
.comment-login-tip {
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 14px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 4px;
}

.comment-list {
  min-height: 80px;
}
.comment-item {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px dashed #ebeef5;
}
.comment-item:last-child {
  border-bottom: none;
}
.comment-avatar {
  flex-shrink: 0;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-weight: 600;
}
.comment-body {
  flex: 1;
  min-width: 0;
}
.comment-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}
.comment-author {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.comment-time {
  font-size: 12px;
  color: #909399;
}
.comment-content {
  font-size: 14px;
  color: #303133;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.comment-edit {
  margin-top: 4px;
}
.comment-edit-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
.comment-actions {
  margin-top: 6px;
  display: flex;
  gap: 4px;
}
.comment-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
</style>
