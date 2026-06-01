<template>
  <div class="page-container">
    <div class="page-header">
      <h2>合同详情</h2>
      <el-button @click="goBack">返回</el-button>
    </div>

    <el-alert
      v-if="contract?.status === 'draft'"
      title="提示"
      type="info"
      description="此合同为草稿状态，房东仍在编辑中。合同签署前房东可能会修改部分内容。"
      show-icon
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-alert
      v-else-if="contract?.status === 'pending_sign' || (contract?.status === 'part_signed' && !contract?.signed_by_tenant)"
      title="待您签署"
      type="warning"
      description="请仔细查看合同内容，确认无误后点击下方签署按钮。签署后合同内容将被锁定。"
      show-icon
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-alert
      v-else-if="contract?.status === 'active'"
      title="合同已生效"
      type="success"
      description="合同已双方签署并生效，双方需按照合同约定履行义务。"
      show-icon
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-card v-loading="loading">
      <ContractDocument
        v-if="contract"
        :contract="contract"
        :property-info="propertyInfo"
        :landlord-info="landlordInfo"
        :tenant-info="tenantInfo"
        :can-edit="false"
        :can-sign="canSign"
        :can-export-pdf="canExportPDF"
        :show-actions="true"
        @sign="handleSign"
        @download-pdf="handleDownloadPDF"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
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

// 是否可以签署
const canSign = computed(() => {
  if (!contract.value) return false
  // 租客只能在房东已签署且租客未签署的情况下签署
  return !contract.value.signed_by_tenant && 
         contract.value.signed_by_landlord &&
         (contract.value.status === 'part_signed' || contract.value.status === 'pending_tenant_sign')
})

// 是否可以导出PDF（只有签署后的合同才能导出）
const canExportPDF = computed(() => {
  if (!contract.value) return false
  return contract.value.status === 'active' || 
         contract.value.status === 'part_signed' ||
         contract.value.status === 'terminated'
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
    
    // 检查权限（租客只能查看自己的合同）
    // 后端API已经做了权限检查，这里只需要处理加载失败的情况

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

// 处理签署 - 跳转到签署页面
function handleSign() {
  router.push(`/tenant/contract/${route.params.id}/sign`)
}

// 下载PDF
function handleDownloadPDF() {
  ElMessage.info('PDF导出功能开发中...')
  // TODO: 实现PDF导出功能
}

// 返回
function goBack() {
  router.push('/tenant/contracts')
}

onMounted(() => {
  loadContract()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

/* 优化 el-card 内部间距 */
:deep(.el-card__body) {
  padding: 20px;
}
</style>
