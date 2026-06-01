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
      description="此合同为草稿状态，您可以继续编辑或发送给租客签署。"
      show-icon
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-alert
      v-else-if="contract?.status === 'pending_sign' || (contract?.status === 'part_signed' && !contract?.signed_by_landlord)"
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
        ref="contractDocRef"
        v-if="contract"
        :contract="contract"
        :property-info="propertyInfo"
        :landlord-info="landlordInfo"
        :tenant-info="tenantInfo"
        :can-edit="canEdit"
        :can-sign="canSign"
        :can-export-pdf="canExportPDF"
        :show-actions="true"
        @sign="handleSign"
        @save-draft="handleSaveDraft"
        @download-pdf="handleDownloadPDF"
        @field-change="handleFieldChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElLoading } from 'element-plus'
import ContractDocument from '../common/ContractDocument.vue'
import { getContract, updateContract } from '../../api/contract'
import request from '../../utils/request'

const route = useRoute()
const router = useRouter()

const contractDocRef = ref(null)
const contract = ref(null)
const propertyInfo = ref(null)
const landlordInfo = ref(null)
const tenantInfo = ref(null)
const loading = ref(false)

// 是否可以编辑（只有草稿状态可以编辑）
const canEdit = computed(() => {
  if (!contract.value) return false
  return contract.value.status === 'draft'
})

// 是否可以签署
const canSign = computed(() => {
  if (!contract.value) return false
  // 只有未签署的合同才能签署，且必须是待签署或部分签署状态
  return !contract.value.signed_by_landlord && 
         (contract.value.status === 'pending_sign' || contract.value.status === 'part_signed')
})

// 是否可以导出PDF（只有签署后的合同才能导出）
const canExportPDF = computed(() => {
  if (!contract.value) return false
  return ['active', 'part_signed', 'terminated', 'expired'].includes(contract.value.status)
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
    
    // 检查权限（房东只能查看自己的合同）
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

  if (route.query.export === 'pdf') {
    await nextTick()
    if (canExportPDF.value) {
      await handleDownloadPDF()
    }
  }
}

// 处理签署 - 跳转到签署页面
function handleSign() {
  router.push(`/landlord/contract/${route.params.id}/sign`)
}

// 保存草稿
async function handleSaveDraft() {
  try {
    await updateContract(contract.value.id, contract.value)
    ElMessage.success('草稿已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存草稿失败')
  }
}

// 导出 PDF
async function handleDownloadPDF() {
  if (!contractDocRef.value) {
    ElMessage.warning('合同内容加载中，请稍后再试')
    return
  }

  const loadingInstance = ElLoading.service({
    lock: true,
    text: '正在生成 PDF...',
    background: 'rgba(255, 255, 255, 0.7)',
  })
  try {
    await contractDocRef.value.exportToPdf()
    ElMessage.success('PDF 已下载')
  } catch (e) {
    console.error('PDF 导出失败:', e)
    ElMessage.error('PDF 导出失败，请稍后重试')
  } finally {
    loadingInstance.close()
  }
}

// 处理字段变更
async function handleFieldChange({ field, value }) {
  if (!contract.value) return
  
  // 更新本地合同数据
  contract.value[field] = value
  
  // 如果是草稿状态，自动保存
  if (contract.value.status === 'draft') {
    try {
      await updateContract(contract.value.id, { [field]: value })
      ElMessage.success('字段已更新')
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '更新字段失败')
      // 恢复原值
      loadContract()
    }
  }
}

// 返回
function goBack() {
  router.push('/landlord/contracts')
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
