<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    width="1000px"
    :close-on-click-modal="false"
    @close="handleClose"
    class="sign-dialog"
    top="5vh"
  >
    <!-- 签署提示 -->
    <el-alert
      :title="alertMessage"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    />

    <!-- 合同内容区域 -->
    <el-card v-loading="loading" class="contract-card">
      <ContractDocument
        :contract="contract"
        :property-info="propertyInfo"
        :landlord-info="landlordInfo"
        :tenant-info="tenantInfo"
      />
    </el-card>

    <!-- 手写签名区域 -->
    <div class="signature-section">
      <h4>{{ userRole === 'landlord' ? '房东签名' : '租客签名' }}</h4>
      <SignaturePad
        ref="signaturePadRef"
        :title="userRole === 'landlord' ? '请在此处手写签名（房东）' : '请在此处手写签名（租客）'"
        :can-draw="!isSubmitting"
        @confirm="handleSignatureConfirm"
        @cancel="handleClose"
      />
    </div>

    <template #footer>
      <el-button @click="handleClose" :disabled="isSubmitting">取消</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import SignaturePad from '../components/SignaturePad.vue'
import ContractDocument from '../views/common/ContractDocument.vue'
import request from '../utils/request'

const props = defineProps({
  contract: {
    type: Object,
    required: true
  },
  propertyInfo: {
    type: Object,
    default: null
  },
  landlordInfo: {
    type: Object,
    default: null
  },
  tenantInfo: {
    type: Object,
    default: null
  },
  userRole: {
    type: String,
    required: true,
    validator: (value) => ['landlord', 'tenant'].includes(value)
  }
})

const emit = defineEmits(['success', 'close'])

const dialogVisible = ref(false)
const signaturePadRef = ref(null)
const isSubmitting = ref(false)
const loading = ref(false)

const title = computed(() => {
  return props.userRole === 'landlord' ? '房东签署合同' : '租客签署合同'
})

const alertMessage = computed(() => {
  if (props.userRole === 'landlord') {
    return '请仔细阅读上方完整合同内容。确认无误后，请在下方手写签名区域签署您的姓名。签署后合同内容将被锁定。'
  } else {
    return '请仔细阅读上方完整合同内容。确认无误后，请在下方手写签名区域签署您的姓名。签署后合同将立即生效。'
  }
})

function open() {
  loading.value = true
  dialogVisible.value = true
  // 等待对话框渲染后重新初始化Canvas
  nextTick(() => {
    loading.value = false
    if (signaturePadRef.value) {
      signaturePadRef.value.initCanvas()
    }
  })
}

function handleClose() {
  if (!isSubmitting.value) {
    dialogVisible.value = false
    emit('close')
  }
}

async function handleSignatureConfirm(signatureData) {
  if (isSubmitting.value) return
  
  try {
    isSubmitting.value = true
    
    // 调用签署API
    const endpoint = props.userRole === 'landlord' 
      ? `/api/v1/contracts/${props.contract.id}/sign/landlord`
      : `/api/v1/contracts/${props.contract.id}/sign/tenant`
    
    await request.put(endpoint, {
      signature_image: signatureData,
      ip_address: null,  // 不记录IP地址
      device_info: navigator.userAgent
    })
    
    ElMessage.success('签署成功！')
    dialogVisible.value = false
    emit('success')
  } catch (e) {
    console.error('签署失败:', e)
    ElMessage.error(e.response?.data?.detail || '签署失败，请稍后重试')
  } finally {
    isSubmitting.value = false
  }
}

defineExpose({
  open
})
</script>

<style scoped>
.sign-dialog :deep(.el-dialog__body) {
  padding: 20px;
}

.contract-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.contract-card :deep(.el-card__body) {
  padding: 20px;
}

.signature-section {
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.signature-section h4 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #333;
  font-weight: 600;
}

ul li {
  margin: 5px 0;
  font-size: 14px;
}
</style>
