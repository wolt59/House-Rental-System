<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ pageTitle }}</h2>
      <el-button @click="goBack">返回</el-button>
    </div>

    <!-- 提示信息 -->
    <el-alert
      v-if="isEditableState"
      title="提示"
      type="info"
      :description="alertDescription"
      show-icon
      :closable="false"
      style="margin-bottom: 20px"
    />
    <el-alert
      v-else-if="isSigning"
      title="签署提示"
      type="warning"
      description="请仔细阅读合同内容。确认无误后，请在下方手写签名区域签署您的姓名。"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    />

    <!-- 合同内容区域（编辑模式 + 签署模式共用） -->
    <el-card v-loading="loading" class="contract-card" v-if="contract">
      <ContractDocument
        ref="documentRef"
        :contract="contract"
        :property-info="propertyInfo"
        :landlord-info="landlordInfo"
        :tenant-info="tenantInfo"
        :can-edit="isEditableState"
        :can-sign="false"
        :can-export-pdf="false"
        :show-actions="false"
        @field-change="handleFieldChange"
      />
    </el-card>

    <!-- 操作按钮（底部固定栏） -->
    <div class="bottom-actions" v-if="contract">
      <template v-if="isEditableState && !isSigning">
        <el-button type="primary" size="large" @click="handleSaveDraft">
          <el-icon style="margin-right:4px"><Document /></el-icon>保存草稿
        </el-button>
        <el-button type="success" size="large" @click="startSigning">
          <el-icon style="margin-right:4px"><EditPen /></el-icon>发起签署
        </el-button>
      </template>
      <template v-if="isSigning">
        <el-button size="large" @click="cancelSigning">取消签署</el-button>
      </template>
    </div>

    <!-- 签署区域 -->
    <div class="signature-section" v-if="isSigning && contract">
      <h3>房东签署</h3>
      <SignaturePad
        ref="signaturePadRef"
        title="请在此处手写签名（房东）"
        :can-draw="!submitting"
        @confirm="handleSignatureConfirm"
        @cancel="cancelSigning"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, EditPen } from '@element-plus/icons-vue'
import SignaturePad from '../../components/SignaturePad.vue'
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
const documentRef = ref(null)
const signaturePadRef = ref(null)
const submitting = ref(false)
const isSigning = ref(false)

const pageTitle = computed(() => {
  if (isSigning.value) return '签署合同'
  if (contract.value?.status === 'draft') return '编辑合同草稿'
  return '编辑合同'
})

const alertDescription = computed(() => {
  if (contract.value?.status === 'draft') {
    return '您可以在下方编辑合同中的关键信息，编辑完成后点击"保存草稿"或"发起签署"。双方签署后合同将生效。'
  }
  return '合同已部分签署，您可以在签署前调整合同内容，然后通过下方签署区域完成签署。'
})

// 合同是否可以编辑（只有草稿状态可编辑）
const isEditableState = computed(() => {
  if (!contract.value) return false
  return contract.value.status === 'draft'
})

// 启动签署模式（从URL参数或手动触发）
const shouldStartSigning = computed(() => route.query.mode === 'sign')

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
    contract.value = await getContract(contractId)

    // 检查合同状态
    if (!isEditableState.value) {
      ElMessage.warning('只能编辑草稿状态或部分签署状态（房东未签署）的合同')
      goBack()
      return
    }

    // 并行加载关联信息
    const promises = []
    if (contract.value.property_id) {
      promises.push(
        request.get(`/api/v1/properties/${contract.value.property_id}`)
          .then(r => { propertyInfo.value = r })
          .catch(e => console.error('加载房源信息失败', e))
      )
    }
    if (contract.value.landlord_id) {
      promises.push(
        request.get(`/api/v1/users/${contract.value.landlord_id}`)
          .then(r => { landlordInfo.value = r })
          .catch(e => console.error('加载房东信息失败', e))
      )
    }
    if (contract.value.tenant_id) {
      promises.push(
        request.get(`/api/v1/users/${contract.value.tenant_id}`)
          .then(r => { tenantInfo.value = r })
          .catch(e => console.error('加载租客信息失败', e))
      )
    }
    await Promise.all(promises)

    // 如果URL带了 mode=sign，直接进入签署模式
    if (shouldStartSigning.value) {
      startSigning()
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载合同失败')
    goBack()
  } finally {
    loading.value = false
  }
}

// 处理字段变更（失焦时自动保存单个字段）
async function handleFieldChange({ field, value }) {
  try {
    const updateData = { [field]: value }

    // 日期字段需要特殊处理
    if ((field === 'start_date' || field === 'end_date' || field === 'check_in_time') && value) {
      updateData[field] = new Date(value).toISOString()
    }

    await updateContract(contract.value.id, updateData)
    contract.value[field] = value
  } catch (e) {
    console.error('保存字段失败:', e)

    let errorMessage = '保存字段失败'
    if (e.response?.data?.detail) {
      const detail = e.response.data.detail
      if (Array.isArray(detail)) {
        const errors = detail.map(err => {
          const field = err.loc?.join('.') || '未知字段'
          const msg = err.msg || '验证失败'
          return `${field}: ${msg}`
        }).join('; ')
        errorMessage = `验证失败: ${errors}`
      } else if (typeof detail === 'string') {
        errorMessage = detail
      } else if (typeof detail === 'object') {
        errorMessage = detail.message || detail.error || JSON.stringify(detail)
      }
    }

    ElMessage.error({ message: errorMessage, duration: 5000, showClose: true })
  }
}

// 保存草稿 —— 读取 ContractDocument 中的 editableFields，确保所有展示值都持久化
async function handleSaveDraft() {
  try {
    // 从子组件获取当前所有可编辑字段的值（包括用户未手动修改但已显示默认值的字段）
    const docEl = documentRef.value
    const currentFields = docEl?.editableFields ? { ...docEl.editableFields } : {}
    const c = contract.value

    const updateData = {}

    // 基础租金字段
    if (currentFields.monthly_rent != null && currentFields.monthly_rent > 0) {
      updateData.monthly_rent = currentFields.monthly_rent
    }
    if (currentFields.deposit != null) {
      updateData.deposit = currentFields.deposit
    }
    if (currentFields.payment_method) {
      updateData.payment_method = currentFields.payment_method
    }
    // 关键修复：收集 editableFields 中的值而非 contract.value 中的值
    // 因为 contract.value 中可能为 null（数据库默认NULL），但 UI 展示了默认值
    if (currentFields.payment_day != null && currentFields.payment_day >= 1) {
      updateData.payment_day = currentFields.payment_day
    } else if (c.payment_day != null && c.payment_day >= 1) {
      updateData.payment_day = c.payment_day
    }
    if (currentFields.early_termination_days != null && currentFields.early_termination_days >= 1) {
      updateData.early_termination_days = currentFields.early_termination_days
    } else if (c.early_termination_days != null && c.early_termination_days >= 1) {
      updateData.early_termination_days = c.early_termination_days
    }
    if (currentFields.renewal_notice_days != null && currentFields.renewal_notice_days >= 1) {
      updateData.renewal_notice_days = currentFields.renewal_notice_days
    } else if (c.renewal_notice_days != null && c.renewal_notice_days >= 1) {
      updateData.renewal_notice_days = c.renewal_notice_days
    }
    if (currentFields.allow_pets != null) {
      updateData.allow_pets = currentFields.allow_pets
    } else if (c.allow_pets != null) {
      updateData.allow_pets = c.allow_pets
    }
    if (currentFields.additional_terms != null) {
      updateData.additional_terms = currentFields.additional_terms
    } else if (c.additional_terms != null) {
      updateData.additional_terms = c.additional_terms
    }
    if (currentFields.property_fee_bearer) {
      updateData.property_fee_bearer = currentFields.property_fee_bearer
    } else if (c.property_fee_bearer) {
      updateData.property_fee_bearer = c.property_fee_bearer
    }
    if (currentFields.utility_fee_bearer) {
      updateData.utility_fee_bearer = currentFields.utility_fee_bearer
    } else if (c.utility_fee_bearer) {
      updateData.utility_fee_bearer = c.utility_fee_bearer
    }
    if (currentFields.other_fee_bearer) {
      updateData.other_fee_bearer = currentFields.other_fee_bearer
    } else if (c.other_fee_bearer) {
      updateData.other_fee_bearer = c.other_fee_bearer
    }

    if (Object.keys(updateData).length === 0) {
      ElMessage.warning('没有需要保存的更改')
      return
    }

    await updateContract(c.id, updateData)
    ElMessage.success('合同草稿已保存')

    // 更新本地数据
    Object.keys(updateData).forEach(key => {
      contract.value[key] = currentFields[key] ?? updateData[key]
    })

    // 重新加载
    await loadContract()
  } catch (e) {
    console.error('保存草稿失败:', e)
    let errorMessage = '保存失败'
    if (e.response?.data?.detail) {
      const detail = e.response.data.detail
      if (Array.isArray(detail)) {
        const errors = detail.map(err => {
          const field = err.loc?.join('.') || '未知字段'
          const msg = err.msg || '验证失败'
          return `${field}: ${msg}`
        }).join('; ')
        errorMessage = `验证失败: ${errors}`
      } else if (typeof detail === 'string') {
        errorMessage = detail
      } else if (typeof detail === 'object') {
        errorMessage = detail.message || detail.error || JSON.stringify(detail)
      }
    }
    ElMessage.error({ message: errorMessage, duration: 5000, showClose: true })
  }
}

// 获取当前可编辑字段的值（从子组件读取，兼容初始为空的情况）
function getCurrentFields() {
  const docEl = documentRef.value
  const c = contract.value
  const currentFields = docEl?.editableFields ? { ...docEl.editableFields } : {}

  return {
    monthly_rent: currentFields.monthly_rent ?? c?.monthly_rent ?? 0,
    deposit: currentFields.deposit ?? c?.deposit ?? 0,
    payment_method: currentFields.payment_method || c?.payment_method || '',
    payment_day: currentFields.payment_day ?? c?.payment_day ?? 1,
    early_termination_days: currentFields.early_termination_days ?? c?.early_termination_days ?? 30,
    renewal_notice_days: currentFields.renewal_notice_days ?? c?.renewal_notice_days ?? 30,
    property_fee_bearer: currentFields.property_fee_bearer || c?.property_fee_bearer || '',
    utility_fee_bearer: currentFields.utility_fee_bearer || c?.utility_fee_bearer || '',
    other_fee_bearer: currentFields.other_fee_bearer || c?.other_fee_bearer || '',
    allow_pets: currentFields.allow_pets ?? c?.allow_pets ?? 0,
  }
}

// 校验签署前必填字段
function validateBeforeSign() {
  const f = getCurrentFields()
  const errors = []

  if (!f.monthly_rent || f.monthly_rent <= 0) errors.push('月租金（¥）不能为空')
  if (f.payment_method.trim() === '') errors.push('付款方式未选择')
  if (!f.payment_day || f.payment_day < 1) errors.push('租金支付日期未填写')
  if (!f.early_termination_days || f.early_termination_days < 1) errors.push('提前解约通知天数未填写')
  if (!f.renewal_notice_days || f.renewal_notice_days < 1) errors.push('续租提醒天数未填写')
  if (!f.property_fee_bearer) errors.push('物业管理费承担方未选择')
  if (!f.utility_fee_bearer) errors.push('水电燃气费承担方未选择')
  if (!f.other_fee_bearer) errors.push('网络/电视费承担方未选择')

  return errors
}

// 进入签署模式
function startSigning() {
  if (!contract.value) return
  const s = contract.value.status
  // 只有草稿状态可以发起签署
  if (s !== 'draft') {
    ElMessage.warning('只有草稿状态的合同可以签署')
    return
  }
  if (contract.value.signed_by_landlord) {
    ElMessage.warning('您已经签署过此合同')
    return
  }

  // 字段校验
  const errors = validateBeforeSign()
  if (errors.length > 0) {
    ElMessageBox.alert(
      '以下字段尚未填写完整，请补充后再签署：<br/><br/>' + errors.map((e, i) => `${i + 1}. ${e}`).join('<br/>'),
      '请完善合同信息',
      { dangerouslyUseHTMLString: true, confirmButtonText: '去修改', type: 'warning' }
    )
    return
  }

  isSigning.value = true

  nextTick(() => {
    if (signaturePadRef.value) {
      signaturePadRef.value.initCanvas()
    }
  })
}

function cancelSigning() {
  isSigning.value = false
}

// 处理签名确认
async function handleSignatureConfirm(signatureData) {
  if (submitting.value) return

  try {
    submitting.value = true
    await request.put(`/api/v1/contracts/${contract.value.id}/sign/landlord`, {
      signature_image: signatureData,
      ip_address: null,
      device_info: navigator.userAgent,
    })
    ElMessage.success('签署成功！')
    // 跳转到合同详情页
    router.push(`/landlord/contract/${contract.value.id}`)
  } catch (e) {
    console.error('签署失败:', e)
    ElMessage.error(e.response?.data?.detail || '签署失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

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
.page-header h2 {
  margin: 0;
}

.contract-card {
  margin-bottom: 20px;
  border-radius: 8px;
}
.contract-card :deep(.el-card__body) {
  padding: 20px;
}

/* 底部操作栏 */
.bottom-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 20px 0 40px;
}

/* 签署区域 */
.signature-section {
  margin-bottom: 20px;
  padding: 24px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}
.signature-section h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
  font-weight: 600;
  text-align: center;
}
</style>
