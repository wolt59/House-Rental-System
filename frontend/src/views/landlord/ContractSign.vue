<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ userRole === 'landlord' ? '房东签署合同' : '租客签署合同' }}</h2>
      <el-button @click="goBack">返回</el-button>
    </div>

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
        v-if="contract"
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
        @cancel="goBack"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import SignaturePad from '../../components/SignaturePad.vue'
import ContractDocument from '../common/ContractDocument.vue'
import { getContract } from '../../api/contract'
import request from '../../utils/request'

const route = useRoute()
const router = useRouter()

const contract = ref(null)
const propertyInfo = ref(null)
const landlordInfo = ref(null)
const tenantInfo = ref(null)
const loading = ref(false)
const signaturePadRef = ref(null)
const isSubmitting = ref(false)

const userRole = computed(() => {
  return route.path.includes('/landlord/') ? 'landlord' : 'tenant'
})

const alertMessage = computed(() => {
  if (userRole.value === 'landlord') {
    return '请仔细阅读上方完整合同内容。确认无误后，请在下方手写签名区域签署您的姓名。签署后合同内容将被锁定。'
  } else {
    return '请仔细阅读上方完整合同内容。确认无误后，请在下方手写签名区域签署您的姓名。签署后合同将立即生效。'
  }
})

// 加载合同数据
async function loadContract() {
  const contractId = route.params.id
  if (!contractId) {
    ElMessage.error('合同ID不存在')
    goBack()
    return
  }

  loading.value = true
  try {
    // 获取合同详情
    contract.value = await getContract(contractId)
    
    // 检查权限和状态
    if (userRole.value === 'landlord' && contract.value.signed_by_landlord) {
      ElMessage.warning('您已经签署过此合同')
      goBack()
      return
    }
    if (userRole.value === 'tenant' && contract.value.signed_by_tenant) {
      ElMessage.warning('您已经签署过此合同')
      goBack()
      return
    }

    // 获取房源信息
    if (contract.value.property_id) {
      try {
        propertyInfo.value = await request.get(`/api/v1/properties/${contract.value.property_id}`)
      } catch (e) {
        console.error('加载房源信息失败', e)
      }
    }

    // 获取房东信息
    if (contract.value.landlord_id) {
      try {
        landlordInfo.value = await request.get(`/api/v1/users/${contract.value.landlord_id}`)
      } catch (e) {
        console.error('加载房东信息失败', e)
      }
    }

    // 获取租客信息
    if (contract.value.tenant_id) {
      try {
        tenantInfo.value = await request.get(`/api/v1/users/${contract.value.tenant_id}`)
      } catch (e) {
        console.error('加载租客信息失败', e)
      }
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载合同失败')
    goBack()
  } finally {
    loading.value = false
  }
}

// 处理签名确认
async function handleSignatureConfirm(signatureData) {
  if (isSubmitting.value) return
  
  try {
    isSubmitting.value = true
    
    // 调用签署API
    const endpoint = userRole.value === 'landlord' 
      ? `/api/v1/contracts/${contract.value.id}/sign/landlord`
      : `/api/v1/contracts/${contract.value.id}/sign/tenant`
    
    await request.put(endpoint, {
      signature_image: signatureData,
      ip_address: null,
      device_info: navigator.userAgent
    })
    
    ElMessage.success('签署成功！')
    // 跳转到合同详情页
    if (userRole.value === 'landlord') {
      router.push(`/landlord/contract/${contract.value.id}`)
    } else {
      router.push(`/tenant/contract/${contract.value.id}`)
    }
  } catch (e) {
    console.error('签署失败:', e)
    ElMessage.error(e.response?.data?.detail || '签署失败，请稍后重试')
  } finally {
    isSubmitting.value = false
  }
}

// 返回上一页
function goBack() {
  if (userRole.value === 'landlord') {
    router.push(`/landlord/contract/${route.params.id}`)
  } else {
    router.push(`/tenant/contract/${route.params.id}`)
  }
}

onMounted(() => {
  loadContract()
  // 等待DOM渲染后初始化Canvas
  nextTick(() => {
    if (signaturePadRef.value) {
      signaturePadRef.value.initCanvas()
    }
  })
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
  font-size: 24px;
  color: #333;
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
</style>
