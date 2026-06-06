<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <el-button @click="$router.back()" :icon="ArrowLeft">返回</el-button>
        <h2 style="margin: 16px 0 0 0">{{ isEdit ? '编辑房源' : '发布房源' }}</h2>
      </div>
    </div>

    <!-- 状态提示 -->
    <el-alert v-if="isEdit && currentEditProperty" :title="getEditRestrictionTip(currentEditProperty)" type="warning" :closable="false" style="margin-bottom: 16px" />

    <el-form :model="form" label-width="140px" class="property-form">
      <!-- 第一类：必填信息 -->
      <div class="form-section">
        <h3 class="section-title"><span class="required-mark">*</span> 第一类：必填信息（业务核心数据）</h3>
        
        <!-- 1. 位置地址类 -->
        <div class="subsection">
          <h4 class="subsection-title">📍 位置地址</h4>
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="所属城市" required>
                <el-input v-model="form.city" placeholder="如：北京" :disabled="isFieldDisabled('city')" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="行政区/区县" required>
                <el-input v-model="form.region" placeholder="如：朝阳区" :disabled="isFieldDisabled('region')" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="小区名称" required>
                <el-input v-model="form.community_name" placeholder="如：阳光花园" :disabled="isFieldDisabled('community_name')" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="24">
              <el-form-item label="详细门牌号" required>
                <el-input v-model="form.address" placeholder="如：建国路88号5号楼3单元1201室" :disabled="isFieldDisabled('address')" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="24">
              <el-form-item label="房源标题" required>
                <el-input v-model="form.title" placeholder="如：阳光花园精装两居室" :disabled="isFieldDisabled('title')" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 2. 房屋物理属性类 -->
        <div class="subsection">
          <h4 class="subsection-title"> 房屋物理属性</h4>
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="房源类型" required>
                <el-select v-model="form.rental_type" placeholder="请选择" style="width: 100%" :disabled="isFieldDisabled('rental_type')">
                  <el-option label="整租" value="整租" />
                  <el-option label="合租" value="合租" />
                  <el-option label="公寓" value="公寓" />
                  <el-option label="商铺" value="商铺" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="户型" class="floor-plan-form-item">
                <div class="floor-plan-editor">
                  <el-select v-model="form.bedrooms" placeholder="室" :disabled="isFieldDisabled('floor_plan')" @change="updateFloorPlan" style="flex:1;min-width:60px">
                    <el-option v-for="n in 6" :key="n" :label="n + '室'" :value="n" />
                  </el-select>
                  <el-select v-model="form.livingrooms" placeholder="厅" :disabled="isFieldDisabled('floor_plan')" @change="updateFloorPlan" style="flex:1;min-width:60px">
                    <el-option v-for="n in 3" :key="n" :label="n + '厅'" :value="n" />
                  </el-select>
                  <el-select v-model="form.bathrooms" placeholder="卫" :disabled="isFieldDisabled('floor_plan')" @change="updateFloorPlan" style="flex:1;min-width:60px">
                    <el-option v-for="n in 4" :key="n" :label="n + '卫'" :value="n" />
                  </el-select>
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="建筑面积(㎡)">
                <el-input-number v-model="form.building_area" :min="0" :precision="2" style="width: 100%" :disabled="isFieldDisabled('building_area')" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="所在楼层">
                <el-input v-model="form.floor_number" placeholder="如：5" :disabled="isFieldDisabled('floor_number')" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="总楼层">
                <el-input v-model="form.total_floors" placeholder="如：18" :disabled="isFieldDisabled('total_floors')" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="房屋朝向">
                <el-select v-model="form.orientation" placeholder="请选择" style="width: 100%" :disabled="isFieldDisabled('orientation')">
                  <el-option label="南" value="南" />
                  <el-option label="南北" value="南北" />
                  <el-option label="东南" value="东南" />
                  <el-option label="西南" value="西南" />
                  <el-option label="东" value="东" />
                  <el-option label="西" value="西" />
                  <el-option label="北" value="北" />
                  <el-option label="东北" value="东北" />
                  <el-option label="西北" value="西北" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="装修程度">
                <el-select v-model="form.decoration" placeholder="请选择" style="width: 100%" :disabled="isFieldDisabled('decoration')">
                  <el-option label="毛坯" value="毛坯" />
                  <el-option label="简装" value="简装" />
                  <el-option label="精装" value="精装" />
                  <el-option label="豪装" value="豪装" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 3. 租赁价格与押金类 -->
        <div class="subsection">
          <h4 class="subsection-title">💰 租赁价格与押金</h4>
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="每月租金(元)" required>
                <el-input-number v-model="form.rent" :min="0" :precision="2" style="width: 100%" :disabled="isFieldDisabled('rent')" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="押金金额(元)">
                <el-input-number v-model="form.deposit" :min="0" :precision="2" style="width: 100%" :disabled="isFieldDisabled('deposit')" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="付款方式">
                <el-select v-model="form.payment_method" placeholder="请选择" style="width: 100%" :disabled="isFieldDisabled('payment_method')">
                  <el-option label="押一付一" value="押一付一" />
                  <el-option label="押一付三" value="押一付三" />
                  <el-option label="半年付" value="半年付" />
                  <el-option label="年付" value="年付" />
                  <el-option label="面议" value="面议" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 4. 租期与入住规则类 -->
        <div class="subsection">
          <h4 class="subsection-title">📅 租期与入住规则</h4>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="最短租期(月)">
                <el-input-number v-model="form.min_lease_term" :min="1" style="width: 100%" :disabled="isFieldDisabled('min_lease_term')" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最早可入住时间">
                <el-date-picker v-model="form.earliest_move_in_date" type="date" placeholder="选择日期" style="width: 100%" :disabled="isFieldDisabled('earliest_move_in_date')" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 5. 费用权责划分 -->
        <div class="subsection">
          <h4 class="subsection-title">💳 费用权责划分</h4>
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="物业费承担方">
                <el-select v-model="form.property_fee_bearer" placeholder="请选择" style="width: 100%" :disabled="isFieldDisabled('property_fee_bearer')">
                  <el-option label="房东" value="房东" />
                  <el-option label="租客" value="租客" />
                  <el-option label="协商" value="协商" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="水电燃气费">
                <el-select v-model="form.utility_fee_bearer" placeholder="请选择" style="width: 100%" :disabled="isFieldDisabled('utility_fee_bearer')">
                  <el-option label="房东" value="房东" />
                  <el-option label="租客" value="租客" />
                  <el-option label="协商" value="协商" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="其他费用">
                <el-select v-model="form.other_fee_bearer" placeholder="请选择" style="width: 100%" :disabled="isFieldDisabled('other_fee_bearer')">
                  <el-option label="房东" value="房东" />
                  <el-option label="租客" value="租客" />
                  <el-option label="协商" value="协商" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 6. 房屋使用限制 -->
        <div class="subsection">
          <h4 class="subsection-title">🐾 房屋使用限制</h4>
          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="是否允许宠物">
                <el-switch v-model="form.allow_pets" :active-value="1" :inactive-value="0" :disabled="isFieldDisabled('allow_pets')" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 7. 基础展示项 -->
        <div class="subsection">
          <h4 class="subsection-title">📝 房源描述</h4>
          <el-form-item label="详细描述">
            <el-input v-model="form.description" type="textarea" :rows="4" placeholder="详细描述房屋情况、周边设施、交通等" :disabled="isFieldDisabled('description')" />
          </el-form-item>
        </div>
      </div>

      <!-- 第二类：选填信息 -->
      <div class="form-section optional-section">
        <h3 class="section-title">第二类：选填信息（丰富房源介绍）</h3>
        
        <!-- 1. 房屋补充属性 -->
        <div class="subsection">
          <h4 class="subsection-title">🏢 房屋补充信息</h4>
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="建筑年代">
                <el-input-number v-model="form.build_year" :min="1900" :max="2100" style="width: 100%" :disabled="isFieldDisabled('build_year')" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="电梯配置">
                <el-switch v-model="form.has_elevator" :active-value="1" :inactive-value="0" :disabled="isFieldDisabled('has_elevator')" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="总户数">
                <el-input-number v-model="form.total_households" :min="0" style="width: 100%" :disabled="isFieldDisabled('total_households')" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="物业类型">
                <el-input v-model="form.property_management_type" placeholder="如：万科物业" :disabled="isFieldDisabled('property_management_type')" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 2. 室内配套设施 -->
        <div class="subsection">
          <h4 class="subsection-title">🛋️ 室内配套设施</h4>
          <el-form-item label="设施清单">
            <el-input v-model="form.facilities" type="textarea" :rows="2" placeholder="例如：空调、冰箱、洗衣机、热水器、WiFi等" :disabled="isFieldDisabled('facilities')" />
          </el-form-item>
        </div>

        <!-- 3. 周边配套描述 -->
        <div class="subsection">
          <h4 class="subsection-title">🏙️ 周边环境</h4>
          <el-form-item label="周边设施">
            <el-input v-model="form.surrounding" type="textarea" :rows="2" placeholder="例如：近地铁、超市、学校、医院等" :disabled="isFieldDisabled('surrounding')" />
          </el-form-item>
        </div>

        <!-- 4. 看房时间规则 -->
        <div class="subsection">
          <h4 class="subsection-title"> 看房时间</h4>
          <el-form-item label="看房时间段">
            <el-input v-model="form.viewing_time_rules" type="textarea" :rows="2" placeholder="例如：工作日晚上7-9点，周末全天" :disabled="isFieldDisabled('viewing_time_rules')" />
          </el-form-item>
        </div>

        <!-- 5. 图文内容 -->
        <div class="subsection">
          <h4 class="subsection-title">🎥 视频与位置</h4>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="视频链接">
                <el-input v-model="form.video_url" placeholder="视频链接（可选）" :disabled="isFieldDisabled('video_url')" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="纬度">
                <el-input-number v-model="form.latitude" :precision="6" style="width: 100%" :disabled="isFieldDisabled('latitude')" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="经度">
                <el-input-number v-model="form.longitude" :precision="6" style="width: 100%" :disabled="isFieldDisabled('longitude')" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 6. 特色标签 -->
        <div class="subsection">
          <h4 class="subsection-title">🏷️ 特色标签</h4>
          <el-form-item label="标签">
            <el-input v-model="form.tags" placeholder="多个标签用逗号分隔，如：近地铁,拎包入住,采光好,学区房" :disabled="isFieldDisabled('tags')" />
          </el-form-item>
        </div>

        <!-- 7. 个人补充备注 -->
        <div class="subsection">
          <h4 class="subsection-title">💬 房东备注</h4>
          <el-form-item label="补充说明">
            <el-input v-model="form.landlord_notes" type="textarea" :rows="3" placeholder="额外说明、特殊要求等" :disabled="isFieldDisabled('landlord_notes')" />
          </el-form-item>
        </div>
      </div>

      <!-- 提交按钮 -->
      <div class="form-actions">
        <el-button @click="$router.back()">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">{{ isEdit ? '保存修改' : '发布房源' }}</el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getProperty, createProperty, updateProperty } from '../../api/property'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const propertyId = route.params.id ? parseInt(route.params.id) : null
const isEdit = !!propertyId

const submitting = ref(false)
const currentEditProperty = ref(null)

const defaultForm = { 
  title: '', address: '', region: '', city: '', community_name: '',
  rental_type: '', floor_plan: '',
  bedrooms: null, livingrooms: null, bathrooms: null,
  building_area: null,
  rent: null, deposit: null, payment_method: '',
  decoration: '', orientation: '', floor_number: '', total_floors: null,
  min_lease_term: null, earliest_move_in_date: '',
  property_fee_bearer: '', utility_fee_bearer: '', other_fee_bearer: '',
  allow_pets: 0,
  description: '',
  build_year: null, has_elevator: null, total_households: null, property_management_type: '',
  facilities: '', surrounding: '', viewing_time_rules: '',
  video_url: '', latitude: null, longitude: null,
  tags: '', landlord_notes: ''
}

const form = reactive({ ...defaultForm })

// 核心字段定义（与后端一致，修改需重新审核）
const CORE_FIELDS = ['address', 'floor_plan', 'area', 'rent', 'deposit', 'floor_number', 'total_floors']

// 从 floor_plan 字符串解析室厅卫数量
function parseFloorPlan(floorPlan) {
  if (!floorPlan) return null
  const match = floorPlan.match(/(\d+)\s*室\s*(\d+)\s*厅\s*(\d+)\s*卫/)
  if (match) {
    return {
      bedrooms: parseInt(match[1]),
      livingrooms: parseInt(match[2]),
      bathrooms: parseInt(match[3]),
    }
  }
  return null
}

// 根据室厅卫数量生成 floor_plan 字符串
function updateFloorPlan() {
  const parts = []
  if (form.bedrooms != null) parts.push(form.bedrooms + '室')
  if (form.livingrooms != null) parts.push(form.livingrooms + '厅')
  if (form.bathrooms != null) parts.push(form.bathrooms + '卫')
  form.floor_plan = parts.join('')
}

// 加载房源数据（编辑模式）
onMounted(async () => {
  if (isEdit && propertyId) {
    try {
      const property = await getProperty(propertyId)
      currentEditProperty.value = property
      Object.keys(defaultForm).forEach((k) => { form[k] = property[k] ?? defaultForm[k] })
      // 如果 API 未返回独立字段，从 floor_plan 解析
      if ((form.bedrooms == null || form.livingrooms == null || form.bathrooms == null) && form.floor_plan) {
        const parsed = parseFloorPlan(form.floor_plan)
        if (parsed) {
          form.bedrooms = parsed.bedrooms
          form.livingrooms = parsed.livingrooms
          form.bathrooms = parsed.bathrooms
        }
      }
    } catch (e) {
      ElMessage.error('加载房源数据失败')
    }
  }
})

// 判断字段是否禁用
function isFieldDisabled(field) {
  if (!isEdit || !currentEditProperty.value) return false
  
  const reviewStatus = currentEditProperty.value.review_status
  const status = currentEditProperty.value.status
  
  if (status === 'rented' || status === 'maintenance') {
    return field !== 'description'
  }
  
  if (reviewStatus === 'pending' || reviewStatus === 'reviewing') {
    return field !== 'description' && field !== 'video_url' && field !== 'facilities' && field !== 'surrounding'
  }
  
  if (reviewStatus === 'draft' || reviewStatus === 'rejected') {
    return false
  }
  
  return false
}

// 获取编辑限制提示
function getEditRestrictionTip(property) {
  const reviewStatus = property.review_status
  const status = property.status
  
  if (status === 'rented' || status === 'maintenance') {
    return '已出租/维修中的房源仅允许修改描述信息'
  }
  
  if (reviewStatus === 'pending' || reviewStatus === 'reviewing') {
    return '审核中的房源仅允许修改描述、视频、设施和周边环境信息'
  }
  
  if (reviewStatus === 'approved' && (status === 'published' || status === 'unpublished')) {
    return '已审核通过的房源，核心字段（地址/户型/面积/租金/押金/楼层）可修改，但修改后会自动转为"待审核"状态'
  }
  
  if (reviewStatus === 'draft' && (status === 'unpublished')) {
    return '房源已被管理员下架，请修改后重新提交审核'
  }
  
  return ''
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (!form.title?.trim() || !form.address?.trim() || form.rent === null || form.rent === '') {
      ElMessage.warning('请填写：房源标题、地址、月租金')
      return
    }

    const data = {}
    Object.entries(form).forEach(([k, v]) => {
      if (v === '' || v === null || v === undefined) return
      data[k] = v
    })

    // 数字字段做类型转换
    const numberFields = ['building_area', 'rent', 'deposit', 'total_floors', 'min_lease_term', 'build_year', 'total_households']
    numberFields.forEach(field => {
      if (field in data && data[field] !== null) {
        data[field] = parseFloat(data[field])
      }
    })
    
    // 日期字段格式化为 YYYY-MM-DD 格式
    if ('earliest_move_in_date' in data && data['earliest_move_in_date']) {
      const date = new Date(data['earliest_move_in_date'])
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      data['earliest_move_in_date'] = `${year}-${month}-${day}`
    }
    
    if (isEdit) {
      const hasCoreFieldChanges = CORE_FIELDS.some(field => 
        data[field] !== undefined && data[field] !== currentEditProperty.value[field]
      )
      
      if (hasCoreFieldChanges && currentEditProperty.value.review_status === 'approved') {
        try {
          await ElMessageBox.confirm(
            '您修改了房源的核心字段（地址/户型/面积/租金/押金/楼层），保存后房源将自动转为"待审核"状态，需要管理员重新审核。确认继续？',
            '提示',
            { type: 'warning', confirmButtonText: '确认保存', cancelButtonText: '取消' }
          )
        } catch {
          submitting.value = false
          return
        }
      }
      
      await updateProperty(propertyId, data)
      ElMessage.success('更新成功')
    } else {
      await createProperty(data)
      ElMessage.success('发布成功')
    }
    
    // 返回房源管理页面
    setTimeout(() => {
      router.push('/landlord/properties')
    }, 500)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.property-form {
  max-width: 1200px;
  margin: 0 auto;
}

.form-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.optional-section {
  background: #fff;
  border: 1px dashed #d9d9d9;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
}

.required-mark {
  color: #f56c6c;
  margin-right: 4px;
}

.subsection {
  margin-bottom: 20px;
  padding: 16px;
  background: #fff;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.subsection:last-child {
  margin-bottom: 0;
}

.subsection-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.form-actions {
  margin-top: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}

.floor-plan-editor {
  display: flex;
  gap: 6px;
  width: 100%;
}

.floor-plan-editor :deep(.el-select) {
  flex: 1;
  min-width: 60px;
}
</style>
