<template>
  <div class="page-container">
    <div class="page-header">
      <h2>发起合约申请</h2>
      <el-button @click="$router.back()">返回</el-button>
    </div>

    <el-card v-loading="loading">
      <el-alert
        title="温馨提示"
        type="info"
        description="您正在为已完成的看房记录发起合约申请，请填写期望的租赁信息。房东同意后系统将自动生成合同草稿。"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <!-- 房源信息展示 -->
      <el-descriptions title="房源信息" :column="2" border style="margin-bottom: 30px">
        <el-descriptions-item label="房源标题">{{ propertyInfo?.title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房源地址">{{ propertyInfo?.address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="租金">{{ propertyInfo?.rent ? `¥${propertyInfo.rent}/月` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="押金">{{ propertyInfo?.deposit ? `¥${propertyInfo.deposit}` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="面积">{{ propertyInfo?.area ? `${propertyInfo.area}㎡` : '-' }}</el-descriptions-item>
        <el-descriptions-item label="户型">{{ propertyInfo?.floor_plan || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 合约申请表单 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="140px"
        style="max-width: 800px"
      >
        <el-form-item label="租赁开始日期" prop="start_date">
          <el-date-picker
            v-model="form.start_date"
            type="date"
            placeholder="选择开始日期"
            style="width: 100%"
            :disabled-date="disabledStartDate"
          />
        </el-form-item>

        <el-form-item label="租赁结束日期" prop="end_date">
          <el-date-picker
            v-model="form.end_date"
            type="date"
            placeholder="选择结束日期"
            style="width: 100%"
            :disabled-date="disabledEndDate"
          />
        </el-form-item>

        <el-form-item label="租期时长">
          <el-tag size="large">{{ leaseDuration }} 个月</el-tag>
        </el-form-item>

        <el-form-item label="付款方式" prop="payment_method">
          <el-select v-model="form.payment_method" placeholder="请选择付款方式" style="width: 100%">
            <el-option label="押一付三" value="押一付三" />
            <el-option label="押一付一" value="押一付一" />
            <el-option label="押二付二" value="押二付二" />
            <el-option label="半年付" value="半年付" />
            <el-option label="年付" value="年付" />
          </el-select>
        </el-form-item>

        <el-form-item label="补充说明" prop="additional_notes">
          <el-input
            v-model="form.additional_notes"
            type="textarea"
            :rows="4"
            placeholder="如有特殊需求或说明，请在此填写（选填）"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" @click="handleSubmit" :loading="submitting">
            提交申请
          </el-button>
          <el-button size="large" @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../../utils/request'
import dayjs from 'dayjs'

const router = useRouter()
const route = useRoute()

const formRef = ref(null)
const loading = ref(false)
const submitting = ref(false)
const propertyInfo = ref(null)

const form = ref({
  booking_id: parseInt(route.query.booking_id),
  start_date: '',
  end_date: '',
  payment_method: '',
  additional_notes: ''
})

const rules = {
  start_date: [
    { required: true, message: '请选择租赁开始日期', trigger: 'change' }
  ],
  end_date: [
    { required: true, message: '请选择租赁结束日期', trigger: 'change' }
  ],
  payment_method: [
    { required: true, message: '请选择付款方式', trigger: 'change' }
  ]
}

// 计算租期时长（月）
const leaseDuration = computed(() => {
  if (!form.value.start_date || !form.value.end_date) return 0
  const start = dayjs(form.value.start_date)
  const end = dayjs(form.value.end_date)
  return end.diff(start, 'month')
})

// 禁用开始日期（不能早于今天）
const disabledStartDate = (date) => {
  return date.getTime() < Date.now() - 86400000 // 不能选择今天之前的日期
}

// 禁用结束日期（不能早于开始日期）
const disabledEndDate = (date) => {
  if (!form.value.start_date) return true
  const startDate = new Date(form.value.start_date)
  return date.getTime() <= startDate.getTime()
}

// 加载房源信息
async function loadPropertyInfo() {
  if (!route.query.property_id) return
  
  try {
    loading.value = true
    const res = await request.get(`/api/v1/properties/${route.query.property_id}`)
    propertyInfo.value = res
  } catch (e) {
    ElMessage.error('加载房源信息失败')
  } finally {
    loading.value = false
  }
}

// 提交表单
async function handleSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  try {
    submitting.value = true
    
    // 验证租期至少1个月
    if (leaseDuration.value < 1) {
      ElMessage.warning('租期至少为1个月')
      return
    }

    await request.post('/api/v1/contract-applications/', {
      booking_id: form.value.booking_id,
      start_date: new Date(form.value.start_date).toISOString(),
      end_date: new Date(form.value.end_date).toISOString(),
      payment_method: form.value.payment_method,
      additional_notes: form.value.additional_notes
    })

    ElMessage.success('合约申请提交成功，请等待房东处理')
    setTimeout(() => {
      router.push('/tenant/bookings')
    }, 1500)
  } catch (e) {
    const msg = e.response?.data?.detail || '提交失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  if (!form.value.booking_id) {
    ElMessage.error('缺少必要的参数')
    router.back()
    return
  }
  loadPropertyInfo()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}
</style>
