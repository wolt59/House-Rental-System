<template>
  <div class="page-container">
    <div class="page-header">
      <h2>编辑合同</h2>
      <el-button @click="goBack">返回</el-button>
    </div>

    <el-alert
      v-if="contract?.status === 'draft'"
      title="提示"
      type="info"
      description="您可以编辑合同中的关键信息，编辑完成后点击保存草稿。双方签署后合同将生效。"
      show-icon
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-alert
      v-else-if="contract?.status === 'part_signed' && !contract?.signed_by_landlord"
      title="提示"
      type="info"
      description="合同处于部分签署状态（租客已签署，房东待签署）。您可以在签署前调整合同内容。"
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
        :can-edit="true"
        :can-sign="canSign"
        :can-export-pdf="false"
        :show-actions="true"
        @field-change="handleFieldChange"
        @save-draft="handleSaveDraft"
        @sign="handleSign"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ContractDocument from '../common/ContractDocument.vue'
import { getContract, updateContract } from '../../api/contract'
import request from '../../utils/request'

const route = useRoute()
const router = useRouter()

const contract = ref(null)
const propertyInfo = ref(null)
const landlordInfo = ref(null)
const tenantInfo = ref(null)
const loading = ref(false)

// 是否可以签署（草稿和部分签署且房东未签署时可以签署）
const canSign = computed(() => {
  if (!contract.value) return false
  return contract.value.status === 'draft' || 
         (contract.value.status === 'part_signed' && !contract.value.signed_by_landlord)
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
    
    // 检查合同状态
    if (contract.value.status !== 'draft' && !(contract.value.status === 'part_signed' && !contract.value.signed_by_landlord)) {
      ElMessage.warning('只能编辑草稿状态或部分签署状态（房东未签署）的合同')
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

// 处理字段变更
async function handleFieldChange({ field, value }) {
  try {
    // 日期字段需要特殊处理，转换为后端期望的格式
    const updateData = { [field]: value }
    
    // 如果是日期字段，转换为ISO字符串格式
    if ((field === 'start_date' || field === 'end_date' || field === 'check_in_time') && value) {
      updateData[field] = new Date(value).toISOString()
    }
    
    await updateContract(contract.value.id, updateData)
    // 更新本地数据
    contract.value[field] = value
  } catch (e) {
    console.error('保存字段失败:', e)
    console.error('保存字段失败 - 错误详情:', e.response?.data)
    
    // 提取并显示详细的验证错误信息
    let errorMessage = '保存字段失败'
    
    if (e.response?.data?.detail) {
      const detail = e.response.data.detail
      
      // 如果是数组格式的错误（Pydantic验证错误）
      if (Array.isArray(detail)) {
        const errors = detail.map(err => {
          const field = err.loc?.join('.') || '未知字段'
          const msg = err.msg || '验证失败'
          return `${field}: ${msg}`
        }).join('; ')
        errorMessage = `验证失败: ${errors}`
      } 
      else if (typeof detail === 'string') {
        errorMessage = detail
      }
      else if (typeof detail === 'object') {
        errorMessage = detail.message || detail.error || JSON.stringify(detail)
      }
    }
    
    ElMessage.error({
      message: errorMessage,
      duration: 5000,
      showClose: true
    })
  }
}

// 处理签署 - 跳转到签署页面
function handleSign() {
  router.push(`/landlord/contract/${route.params.id}/sign`)
}

// 保存草稿
async function handleSaveDraft() {
  try {
    console.log('保存草稿 - 合同数据:', contract.value)
    console.log('保存草稿 - 合同ID:', contract.value?.id)
    console.log('保存草稿 - 合同状态:', contract.value?.status)
    
    // 只保存需要更新的字段，避免发送不必要的数据
    // 过滤掉null和无效值，只发送有实际意义的字段
    const updateData = {}
    
    if (contract.value.monthly_rent !== null && contract.value.monthly_rent !== undefined && contract.value.monthly_rent > 0) {
      updateData.monthly_rent = contract.value.monthly_rent
    }
    if (contract.value.deposit !== null && contract.value.deposit !== undefined) {
      updateData.deposit = contract.value.deposit
    }
    if (contract.value.payment_method) {
      updateData.payment_method = contract.value.payment_method
    }
    if (contract.value.payment_day !== null && contract.value.payment_day !== undefined && contract.value.payment_day >= 1) {
      updateData.payment_day = contract.value.payment_day
    }
    if (contract.value.renewal_notice_days !== null && contract.value.renewal_notice_days !== undefined && contract.value.renewal_notice_days >= 1) {
      updateData.renewal_notice_days = contract.value.renewal_notice_days
    }
    if (contract.value.early_termination_days !== null && contract.value.early_termination_days !== undefined && contract.value.early_termination_days >= 1) {
      updateData.early_termination_days = contract.value.early_termination_days
    }
    if (contract.value.allow_pets !== null && contract.value.allow_pets !== undefined) {
      updateData.allow_pets = contract.value.allow_pets
    }
    if (contract.value.additional_terms !== null && contract.value.additional_terms !== undefined) {
      updateData.additional_terms = contract.value.additional_terms
    }
    if (contract.value.property_fee_bearer) {
      updateData.property_fee_bearer = contract.value.property_fee_bearer
    }
    if (contract.value.utility_fee_bearer) {
      updateData.utility_fee_bearer = contract.value.utility_fee_bearer
    }
    if (contract.value.other_fee_bearer) {
      updateData.other_fee_bearer = contract.value.other_fee_bearer
    }
    
    console.log('保存草稿 - 更新数据:', updateData)
    console.log('保存草稿 - 更新数据字段数:', Object.keys(updateData).length)
    
    // 如果没有要更新的字段，直接返回
    if (Object.keys(updateData).length === 0) {
      ElMessage.warning('没有需要保存的更改')
      return
    }
    
    await updateContract(contract.value.id, updateData)
    ElMessage.success('合同草稿已保存')
    // 重新加载数据以确保同步
    await loadContract()
  } catch (e) {
    console.error('保存草稿失败:', e)
    console.error('保存草稿失败 - 错误详情:', e.response?.data)
    
    // 提取并显示详细的验证错误信息
    let errorMessage = '保存失败'
    
    if (e.response?.data?.detail) {
      const detail = e.response.data.detail
      
      // 如果是数组格式的错误（Pydantic验证错误）
      if (Array.isArray(detail)) {
        const errors = detail.map(err => {
          // 提取字段名和错误信息
          const field = err.loc?.join('.') || '未知字段'
          const msg = err.msg || '验证失败'
          return `${field}: ${msg}`
        }).join('; ')
        errorMessage = `验证失败: ${errors}`
      } 
      // 如果是字符串格式的错误
      else if (typeof detail === 'string') {
        errorMessage = detail
      }
      // 如果是对象格式的错误
      else if (typeof detail === 'object') {
        errorMessage = detail.message || detail.error || JSON.stringify(detail)
      }
    }
    
    // 显示错误提示
    ElMessage.error({
      message: errorMessage,
      duration: 5000, // 显示5秒
      showClose: true
    })
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
