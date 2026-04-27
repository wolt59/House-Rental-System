<template>
  <div class="page-container" v-loading="loading">
    <el-page-header @back="$router.back()" :content="property.title || '房源详情'" />

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="14">
        <el-card>
          <div class="image-gallery">
            <div class="main-image">
              <img :src="currentImage" alt="" />
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
      </el-col>

      <el-col :span="10">
        <el-card>
          <h2 style="margin-bottom: 12px">{{ property.title }}</h2>
          <div class="price">¥{{ property.rent }}<span>/月</span></div>
          <el-descriptions :column="2" border size="small" style="margin-top: 16px">
            <el-descriptions-item label="地址">{{ property.address }}</el-descriptions-item>
            <el-descriptions-item label="区域">{{ property.region || '-' }}</el-descriptions-item>
            <el-descriptions-item label="户型">{{ property.floor_plan || '-' }}</el-descriptions-item>
            <el-descriptions-item label="面积">{{ property.area ? property.area + '㎡' : '-' }}</el-descriptions-item>
            <el-descriptions-item label="租金">¥{{ property.rent }}/月</el-descriptions-item>
            <el-descriptions-item label="押金">{{ property.deposit ? '¥' + property.deposit : '-' }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ property.property_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="装修">{{ property.decoration || '-' }}</el-descriptions-item>
            <el-descriptions-item label="朝向">{{ property.orientation || '-' }}</el-descriptions-item>
            <el-descriptions-item label="楼层">{{ property.floor_number || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusType" size="small">{{ statusLabel }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="浏览量">{{ property.view_count || 0 }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top: 16px" v-if="property.surrounding">
            <h4>周边环境</h4>
            <p style="color: #606266; font-size: 14px; line-height: 1.6">{{ property.surrounding }}</p>
          </div>
          <div style="margin-top: 16px" v-if="property.description">
            <h4>房源描述</h4>
            <p style="color: #606266; font-size: 14px; line-height: 1.6">{{ property.description }}</p>
          </div>
          <div style="margin-top: 20px" v-if="userStore.isLoggedIn && userStore.isTenant">
            <el-button type="primary" size="large" @click="showBookingDialog = true">预约看房</el-button>
            <el-button size="large" @click="showMessageDialog = true">联系房东</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showBookingDialog" title="预约看房" width="480px">
      <el-form :model="bookingForm" label-width="80px">
        <el-form-item label="预约时间">
          <el-date-picker v-model="bookingForm.appointment_time" type="datetime" placeholder="选择时间" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="bookingForm.note" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBookingDialog = false">取消</el-button>
        <el-button type="primary" :loading="bookingLoading" @click="handleBooking">确认预约</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showMessageDialog" title="联系房东" width="480px">
      <el-form :model="messageForm" label-width="80px">
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

const statusType = computed(() => {
  const map = { vacant: 'success', rented: 'warning', maintenance: 'danger' }
  return map[property.value.status] || 'info'
})
const statusLabel = computed(() => {
  const map = { vacant: '空置', rented: '已出租', maintenance: '维修中' }
  return map[property.value.status] || property.value.status
})

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
  } catch (e) {} finally {
    loading.value = false
  }
}

async function handleBooking() {
  if (!bookingForm.value.appointment_time) {
    ElMessage.warning('请选择预约时间')
    return
  }
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
  } catch (e) {} finally {
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
  } catch (e) {} finally {
    msgLoading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.image-gallery .main-image {
  height: 400px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
}
.image-gallery .main-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.thumb-list {
  display: flex;
  gap: 8px;
  overflow-x: auto;
}
.thumb {
  width: 80px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
  border: 2px solid transparent;
}
.thumb.active {
  border-color: #409eff;
}
.price {
  font-size: 28px;
  font-weight: bold;
  color: #f56c6c;
}
.price span {
  font-size: 14px;
  color: #909399;
  font-weight: normal;
}
</style>
