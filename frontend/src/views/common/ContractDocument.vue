<template>
  <div class="contract-document" ref="documentRef">
    <!-- 合同标题 -->
    <div class="contract-header">
      <h1 class="contract-title">房屋租赁合同</h1>
      <div class="contract-no">合同编号：{{ contract.contract_no }}</div>
    </div>

    <!-- 合同基本信息 -->
    <div class="contract-section">
      <h2 class="section-title">第一条 合同双方</h2>
      <div class="section-content">
        <p><strong>出租方（甲方）：</strong>{{ landlordInfo?.full_name || landlordInfo?.username || '_______________' }}</p>
        <p><strong>身份证号码：</strong>{{ landlordInfo?.id_card_number || '_______________' }}</p>
        <p><strong>联系电话：</strong>{{ landlordInfo?.phone || '_______________' }}</p>
        <br/>
        <p><strong>承租方（乙方）：</strong>{{ tenantInfo?.full_name || tenantInfo?.username || '_______________' }}</p>
        <p><strong>身份证号码：</strong>{{ tenantInfo?.id_card_number || '_______________' }}</p>
        <p><strong>联系电话：</strong>{{ tenantInfo?.phone || '_______________' }}</p>
      </div>
    </div>

    <!-- 房屋基本信息 -->
    <div class="contract-section">
      <h2 class="section-title">第二条 租赁房屋</h2>
      <div class="section-content">
        <p>甲方将位于 <strong>{{ propertyInfo?.address || '_______________' }}</strong> 的房屋出租给乙方使用。</p>
        <p>房屋建筑面积：<strong>{{ propertyInfo?.area || propertyInfo?.building_area || '_____' }} 平方米</strong></p>
        <p>房屋户型：<strong>{{ propertyInfo?.floor_plan || '_______________' }}</strong></p>
        <p>房屋用途：<strong>居住</strong></p>
      </div>
    </div>

    <!-- 租赁期限 -->
    <div class="contract-section">
      <h2 class="section-title">第三条 租赁期限</h2>
      <div class="section-content">
        <p>租赁期共 <strong>{{ leaseMonths }} 个月</strong>，自 <strong>{{ formatDate(contract.start_date) }}</strong> 起至 <strong>{{ formatDate(contract.end_date) }}</strong> 止。</p>
        <p>租赁期满，甲方有权收回该房屋，乙方应如期交还。乙方如要求续租，则必须在租赁期满前 <strong class="editable-field" v-if="canEdit && isEditable('renewal_notice_days')">
          <el-input-number 
            v-model="editableFields.renewal_notice_days" 
            :min="1" 
            :max="90"
            controls-position="right"
            @change="handleFieldChange('renewal_notice_days', $event)"
          />
        </strong><span v-else>{{ contract.renewal_notice_days || 30 }} 日内</span>书面通知甲方，经甲方同意后，重新签订租赁合同。</p>
      </div>
    </div>

    <!-- 租金及支付方式 -->
    <div class="contract-section">
      <h2 class="section-title">第四条 租金及支付方式</h2>
      <div class="section-content">
        <p>该房屋每月租金为人民币 <strong class="editable-field" v-if="canEdit && isEditable('monthly_rent')">
          <el-input-number 
            v-model="editableFields.monthly_rent" 
            :min="0" 
            :precision="2"
            controls-position="right"
            @change="handleFieldChange('monthly_rent', $event)"
          />
        </strong><span v-else>¥{{ contract.monthly_rent || '_____' }}/月</span></p>
        
        <p>租金支付方式：<strong class="editable-field payment-method-field" v-if="canEdit && isEditable('payment_method')">
          <el-select v-model="editableFields.payment_method" @change="handleFieldChange('payment_method', $event)" style="width: 150px">
            <el-option label="押一付三" value="押一付三" />
            <el-option label="押一付一" value="押一付一" />
            <el-option label="押二付二" value="押二付二" />
            <el-option label="半年付" value="半年付" />
            <el-option label="年付" value="年付" />
          </el-select>
        </strong><span v-else>{{ contract.payment_method || '_______________' }}</span></p>
        
        <p>押金金额：<strong class="editable-field" v-if="canEdit && isEditable('deposit')">
          <el-input-number 
            v-model="editableFields.deposit" 
            :min="0" 
            :precision="2"
            controls-position="right"
            @change="handleFieldChange('deposit', $event)"
          />
        </strong><span v-else>¥{{ contract.deposit || '_____' }}</span></p>
        
        <p>每期租金支付日期：每月 <strong class="editable-field" v-if="canEdit && isEditable('payment_day')">
          <el-input-number 
            v-model="editableFields.payment_day" 
            :min="1" 
            :max="31"
            controls-position="right"
            @change="handleFieldChange('payment_day', $event)"
          />
        </strong><span v-else>{{ contract.payment_day || '__' }} 日</span>前支付下一期租金。</p>
      </div>
    </div>

    <!-- 其他费用 -->
    <div class="contract-section">
      <h2 class="section-title">第五条 其他费用</h2>
      <div class="section-content">
        <p>租赁期间，下列费用的承担方式为：</p>
        <ul>
          <li>物业管理费由 <strong class="editable-field fee-bearer-field" v-if="canEdit && isEditable('property_fee_bearer')">
            <el-select v-model="editableFields.property_fee_bearer" @change="handleFieldChange('property_fee_bearer', $event)" style="width: 150px">
              <el-option label="甲方（房东）" value="landlord" />
              <el-option label="乙方（租客）" value="tenant" />
            </el-select>
          </strong><span v-else>{{ getFeeBearerText('property_fee_bearer') }}</span> 承担</li>
          <li>水费、电费、燃气费由 <strong class="editable-field fee-bearer-field" v-if="canEdit && isEditable('utility_fee_bearer')">
            <el-select v-model="editableFields.utility_fee_bearer" @change="handleFieldChange('utility_fee_bearer', $event)" style="width: 150px">
              <el-option label="甲方（房东）" value="landlord" />
              <el-option label="乙方（租客）" value="tenant" />
            </el-select>
          </strong><span v-else>{{ getFeeBearerText('utility_fee_bearer') }}</span> 承担</li>
          <li>网络费、电视费由 <strong class="editable-field fee-bearer-field" v-if="canEdit && isEditable('other_fee_bearer')">
            <el-select v-model="editableFields.other_fee_bearer" @change="handleFieldChange('other_fee_bearer', $event)" style="width: 150px">
              <el-option label="甲方（房东）" value="landlord" />
              <el-option label="乙方（租客）" value="tenant" />
            </el-select>
          </strong><span v-else>{{ getFeeBearerText('other_fee_bearer') }}</span> 承担</li>
        </ul>
      </div>
    </div>

    <!-- 房屋使用要求 -->
    <div class="contract-section">
      <h2 class="section-title">第六条 房屋使用要求</h2>
      <div class="section-content">
        <p>乙方应合理使用其所承租的房屋及其附属设施。如因使用不当造成房屋及设施损坏的，乙方应立即负责修复或经济赔偿。</p>
        <p>乙方不得改变房屋的内部结构、装修或设置对房屋结构有影响的设备。未经甲方同意，乙方不得转租、转借承租房屋。</p>
        <p>是否允许养宠物：<strong class="editable-field" v-if="canEdit && isEditable('allow_pets')">
          <el-switch 
            v-model="editableFields.allow_pets" 
            :active-value="1" 
            :inactive-value="0"
            active-text="是"
            inactive-text="否"
            @change="handleFieldChange('allow_pets', $event)"
          />
        </strong><span v-else>{{ contract.allow_pets ? '是' : '否' }}</span></p>
      </div>
    </div>

    <!-- 合同变更和终止 -->
    <div class="contract-section">
      <h2 class="section-title">第七条 合同变更和终止</h2>
      <div class="section-content">
        <p>租赁期间，任何一方提出终止合同，需提前 <strong class="editable-field" v-if="canEdit && isEditable('early_termination_days')">
          <el-input-number 
            v-model="editableFields.early_termination_days" 
            :min="1" 
            :max="90"
            controls-position="right"
            @change="handleFieldChange('early_termination_days', $event)"
          />
        </strong><span v-else>{{ contract.early_termination_days || '__' }}</span> 日书面通知对方，经双方协商后签订终止合同书。</p>
        <p>不可抗力原因导致该房屋毁损和造成损失的，双方互不承担责任。</p>
      </div>
    </div>

    <!-- 补充约定 -->
    <div class="contract-section" v-if="contract.additional_terms || canEdit">
      <h2 class="section-title">第八条 补充约定</h2>
      <div class="section-content">
        <div v-if="canEdit && isEditable('additional_terms')">
          <el-input
            v-model="editableFields.additional_terms"
            type="textarea"
            :rows="4"
            placeholder="请输入补充约定内容"
            maxlength="2000"
            show-word-limit
            @blur="handleFieldChange('additional_terms', editableFields.additional_terms)"
          />
        </div>
        <div v-else>
          <p style="white-space: pre-wrap;">{{ contract.additional_terms || '无' }}</p>
        </div>
      </div>
    </div>

    <!-- 签署区域 -->
    <div class="contract-section signature-section">
      <h2 class="section-title">第九条 合同签署</h2>
      <div class="signature-grid">
        <div class="signature-box">
          <p><strong>甲方（出租方）签字：</strong></p>
          <div class="signature-area">
            <img v-if="contract.landlord_signature_image" :src="contract.landlord_signature_image" alt="房东签名" class="signature-image" />
            <div v-else class="signature-placeholder">待签署</div>
          </div>
          <p v-if="contract.landlord_signed_at">签署时间：{{ formatDateTime(contract.landlord_signed_at) }}</p>
          <p v-if="contract.landlord_sign_ip">签署IP：{{ contract.landlord_sign_ip }}</p>
        </div>
        <div class="signature-box">
          <p><strong>乙方（承租方）签字：</strong></p>
          <div class="signature-area">
            <img v-if="contract.tenant_signature_image" :src="contract.tenant_signature_image" alt="租客签名" class="signature-image" />
            <div v-else class="signature-placeholder">待签署</div>
          </div>
          <p v-if="contract.tenant_signed_at">签署时间：{{ formatDateTime(contract.tenant_signed_at) }}</p>
          <p v-if="contract.tenant_sign_ip">签署IP：{{ contract.tenant_sign_ip }}</p>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="contract-actions" v-if="showActions">
      <el-button v-if="canSign" type="primary" size="large" @click="$emit('sign')">
        签署合同
      </el-button>
      <el-button v-if="canEdit" size="large" @click="$emit('save-draft')">
        保存草稿
      </el-button>
      <el-button v-if="canExportPDF" size="large" @click="$emit('download-pdf')">
        下载PDF
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import dayjs from 'dayjs'

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
  canEdit: {
    type: Boolean,
    default: false
  },
  canSign: {
    type: Boolean,
    default: false
  },
  canExportPDF: {
    type: Boolean,
    default: false
  },
  showActions: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['sign', 'save-draft', 'download-pdf', 'field-change'])

const documentRef = ref(null)

// 可编辑字段列表
const editableFieldsList = [
  'monthly_rent',
  'deposit',
  'payment_method',
  'payment_day',
  'early_termination_days',
  'additional_terms',
  'renewal_notice_days',
  'property_fee_bearer',
  'utility_fee_bearer',
  'other_fee_bearer',
  'allow_pets'
]

// 可编辑字段的本地副本
const editableFields = ref({
  monthly_rent: 0,
  deposit: 0,
  payment_method: '',
  payment_day: 1,
  early_termination_days: 30,
  additional_terms: '',
  renewal_notice_days: 30,
  property_fee_bearer: '',
  utility_fee_bearer: '',
  other_fee_bearer: '',
  allow_pets: 0
})

// 监听合同数据变化，更新本地字段
watch(() => props.contract, (newVal) => {
  if (newVal) {
    editableFields.value = {
      monthly_rent: newVal.monthly_rent || 0,
      deposit: newVal.deposit || 0,
      payment_method: newVal.payment_method || '',
      payment_day: newVal.payment_day || 1,
      early_termination_days: newVal.early_termination_days || 30,
      additional_terms: newVal.additional_terms || '',
      renewal_notice_days: newVal.renewal_notice_days || 30,
      property_fee_bearer: newVal.property_fee_bearer || '',
      utility_fee_bearer: newVal.utility_fee_bearer || '',
      other_fee_bearer: newVal.other_fee_bearer || '',
      allow_pets: newVal.allow_pets || 0
    }
  }
}, { deep: true, immediate: true })

// 计算租期月数
const leaseMonths = computed(() => {
  if (!props.contract.start_date || !props.contract.end_date) return 0
  const start = dayjs(props.contract.start_date)
  const end = dayjs(props.contract.end_date)
  return end.diff(start, 'month')
})

// 判断字段是否可编辑
function isEditable(fieldName) {
  // DRAFT状态可编辑
  if (props.contract.status === 'draft') {
    return editableFieldsList.includes(fieldName)
  }
  // PART_SIGNED状态，如果房东还没签署，也可以编辑（允许在签署前调整）
  if (props.contract.status === 'part_signed' && !props.contract.signed_by_landlord) {
    return editableFieldsList.includes(fieldName)
  }
  // 其他状态不可编辑
  return false
}

// 处理字段变更
function handleFieldChange(fieldName, value) {
  emit('field-change', { field: fieldName, value })
}

// 获取费用承担方文本
function getFeeBearerText(fieldName) {
  const bearerMap = {
    property_fee_bearer: {
      landlord: '甲方（房东）',
      tenant: '乙方（租客）'
    },
    utility_fee_bearer: {
      landlord: '甲方（房东）',
      tenant: '乙方（租客）'
    },
    other_fee_bearer: {
      landlord: '甲方（房东）',
      tenant: '乙方（租客）'
    }
  }
  
  const value = props.contract[fieldName]
  if (!value) return '_______________'
  
  const map = bearerMap[fieldName]
  return map[value] || value
}

// 格式化日期（仅日期部分）
function formatDate(date) {
  if (!date) return '____年__月__日'
  return dayjs(date).format('YYYY年MM月DD日')
}

// 格式化日期时间
function formatDateTime(datetime) {
  if (!datetime) return ''
  return dayjs(datetime).format('YYYY-MM-DD HH:mm:ss')
}

// 打印合同
function printContract() {
  window.print()
}

// 暴露方法供父组件调用
defineExpose({
  documentRef
})
</script>

<style scoped>
.contract-document {
  max-width: 900px;
  margin: 0 auto;
  padding: 30px 40px;
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  font-family: "SimSun", "宋体", serif;
  line-height: 1.6;
  color: #333;
}

/* 合同头部 */
.contract-header {
  text-align: center;
  margin-bottom: 30px;
  border-bottom: 3px double #333;
  padding-bottom: 15px;
}

.contract-title {
  font-size: 28px;
  font-weight: bold;
  margin: 0 0 8px 0;
  letter-spacing: 4px;
}

.contract-no {
  font-size: 14px;
  color: #666;
}

/* 章节样式 */
.contract-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #000;
}

.section-content {
  padding-left: 20px;
  text-align: justify;
}

.section-content p {
  margin: 6px 0;
  text-indent: 2em;
  line-height: 1.6;
  word-break: break-word;
  overflow-wrap: break-word;
}

.section-content ul {
  margin: 8px 0;
  padding-left: 40px;
}

.section-content li {
  margin: 4px 0;
  line-height: 1.6;
  word-break: break-word;
  overflow-wrap: break-word;
}

/* 可编辑字段样式 */
.editable-field {
  display: inline-block;
  min-width: 80px;
  max-width: 200px;
  border-bottom: 1px dashed #409eff;
  transition: all 0.3s;
  vertical-align: middle;
}

.editable-field:hover {
  background-color: #f0f9ff;
}

/* 可编辑字段内的表单控件样式 */
.editable-field :deep(.el-input-number),
.editable-field :deep(.el-select),
.editable-field :deep(.el-switch) {
  width: auto;
  min-width: 60px;
}

.editable-field :deep(.el-input__inner),
.editable-field :deep(.el-select__input) {
  padding: 2px 8px;
  font-size: 14px;
}

.editable-field :deep(.el-input-number__decrease),
.editable-field :deep(.el-input-number__increase) {
  width: 20px;
}

/* textarea 样式优化 */
.section-content :deep(.el-textarea__inner) {
  padding: 8px 12px;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
}

/* 签署区域 */
.signature-section {
  margin-top: 40px;
  page-break-inside: avoid;
}

.signature-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  margin-top: 15px;
}

.signature-box {
  border: 1px solid #ddd;
  padding: 15px;
  background: #fafafa;
}

.signature-area {
  height: 100px;
  border: 2px dashed #ccc;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 15px 0;
  background: white;
}

.signature-image {
  max-width: 100%;
  max-height: 80px;
  object-fit: contain;
}

.signature-placeholder {
  color: #999;
  font-style: italic;
}

/* 操作按钮 */
.contract-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 20px;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: center;
  gap: 15px;
  z-index: 100;
}

/* 打印样式 */
@media print {
  .contract-actions {
    display: none;
  }
  
  .contract-document {
    box-shadow: none;
    padding: 0;
  }
  
  .editable-field {
    border-bottom: none;
  }
  
  .contract-section {
    page-break-inside: avoid;
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .contract-document {
    padding: 15px 20px;
    max-width: 100%;
  }
  
  .signature-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .contract-actions {
    flex-wrap: wrap;
  }
  
  .section-content {
    padding-left: 10px;
  }
}

/* 费用承担字段样式优化 */
.fee-bearer-field {
  display: inline-block;
  min-width: 150px;
}

.fee-bearer-field :deep(.el-select) {
  width: 150px !important;
}

/* 付款方式字段样式优化 */
.payment-method-field {
  display: inline-block;
  min-width: 150px;
}

.payment-method-field :deep(.el-select) {
  width: 150px !important;
}

/* 可编辑字段通用样式 */
.editable-field {
  display: inline-block;
  vertical-align: middle;
}

.editable-field :deep(.el-input-number) {
  width: 120px;
}

.editable-field :deep(.el-select) {
  width: 120px;
}
</style>
