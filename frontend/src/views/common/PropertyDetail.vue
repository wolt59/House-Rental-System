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

            <div class="info-row">
              <div class="info-item">
                <div class="info-label">类型</div>
                <div class="info-value">{{ property.rental_type || property.property_type || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">户型</div>
                <div class="info-value">{{ formatFloorPlan(property) }}</div>
              </div>
            </div>

            <div class="info-row">
              <div class="info-item">
                <div class="info-label">建筑面积</div>
                <div class="info-value">{{ property.building_area ? property.building_area + '㎡' : (property.area ? property.area + '㎡' : '-') }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">实用面积</div>
                <div class="info-value">{{ property.usable_area ? property.usable_area + '㎡' : '-' }}</div>
              </div>
            </div>

            <div class="info-row">
              <div class="info-item">
                <div class="info-label">朝向</div>
                <div class="info-value">{{ property.orientation || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">楼层</div>
                <div class="info-value">{{ formatFloorNumber(property) }}</div>
              </div>
            </div>

            <div class="info-item">
              <div class="info-label">装修程度</div>
              <div class="info-value">{{ property.decoration || '-' }}</div>
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

          <!-- 状态信息 -->
          <div class="divider"></div>
          <div class="status-bar">
            <div class="status-left">
              <el-tag :type="statusType" size="large">{{ statusLabel }}</el-tag>
            </div>
            <div class="status-right">
              <span class="view-count">👁️ {{ property.view_count || 0 }} 次浏览</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons" v-if="userStore.isLoggedIn && userStore.isTenant">
            <div class="action-btn action-btn-primary" @click="showBookingDialog = true">
              <el-icon class="btn-icon"><Calendar /></el-icon>
              <span>预约看房</span>
            </div>
            <div class="action-btn action-btn-default" @click="showMessageDialog = true">
              <el-icon class="btn-icon"><ChatDotRound /></el-icon>
              <span>联系房东</span>
            </div>
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
                :disabled-date="d => d.getTime() < Date.now() - 86400000" 
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

    <!-- 联系房东弹窗 -->
    <el-dialog v-model="showMessageDialog" title="联系房东" width="600px">
      <el-form :model="messageForm" label-width="90px">
        <el-form-item label="消息内容">
          <el-input v-model="messageForm.content" type="textarea" :rows="4" placeholder="请输入消息内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMessageDialog = false">取消</el-button>
        <el-button type="primary" :loading="msgLoading" @click="handleSendMessage">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '../../store/user'
import { getProperty } from '../../api/property'
import { createBooking } from '../../api/booking'
import { sendMessage } from '../../api/message'
import { ElMessage } from 'element-plus'
import { Calendar, ChatDotRound } from '@element-plus/icons-vue'

const route = useRoute()
const userStore = useUserStore()
const property = ref({})
const loading = ref(false)
const currentImage = ref('')
const showBookingDialog = ref(false)
const showMessageDialog = ref(false)
const bookingLoading = ref(false)
const msgLoading = ref(false)

const bookingForm = ref({ appointment_time: '', note: '' })
const messageForm = ref({ content: '' })
const bookingFormRef = ref(null)

const bookingRules = {
  appointment_time: [{ required: true, message: '请选择预约时间', trigger: 'change' }],
}

const statusType = computed(() => {
  const map = { vacant: 'success', rented: 'warning', maintenance: 'danger' }
  return map[property.value.status] || 'info'
})
const statusLabel = computed(() => {
  const map = { vacant: '空置', rented: '已出租', maintenance: '维修中' }
  return map[property.value.status] || property.value.status
})

// 判断是否有补充信息
const hasSupplementInfo = computed(() => {
  return property.value.build_year || 
         property.value.has_elevator !== null || 
         property.value.total_households || 
         property.value.property_management_type
})

// 格式化户型显示
function formatFloorPlan(property) {
  if (property.bedrooms || property.livingrooms || property.bathrooms) {
    const parts = []
    if (property.bedrooms) parts.push(`${property.bedrooms}室`)
    if (property.livingrooms) parts.push(`${property.livingrooms}厅`)
    if (property.bathrooms) parts.push(`${property.bathrooms}卫`)
    return parts.join('') || '-'
  }
  return property.floor_plan || '-'
}

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
      currentImage.value = 'https://via.placeholder.com/600x400?text=No+Image'
    }
  } catch (e) {
    ElMessage.error('加载房源详情失败')
  } finally {
    loading.value = false
  }
}

async function handleBooking() {
  const valid = await bookingFormRef.value.validate().catch(() => false)
  if (!valid) return
  bookingLoading.value = true
  try {
    await createBooking({
      property_id: parseInt(route.params.id),
      appointment_time: bookingForm.value.appointment_time.toISOString(),
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

async function handleSendMessage() {
  if (!messageForm.value.content) {
    ElMessage.warning('请输入消息内容')
    return
  }
  msgLoading.value = true
  try {
    await sendMessage({
      to_user_id: property.value.owner_id,
      property_id: parseInt(route.params.id),
      content: messageForm.value.content,
    })
    ElMessage.success('消息已发送')
    showMessageDialog.value = false
    messageForm.value = { content: '' }
  } catch (e) {
    ElMessage.error('发送消息失败')
  } finally {
    msgLoading.value = false
  }
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
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
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

/* 状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.status-left,
.status-right {
  display: flex;
  align-items: center;
}

.view-count {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
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
</style>
