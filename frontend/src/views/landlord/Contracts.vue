<template>
  <div class="page-container">
    <div class="page-header">
      <h2>合同管理</h2>
    </div>
    
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <!-- 全部合同 -->
      <el-tab-pane name="all">
        <template #label>
          <span>全部合同 ({{ contracts.length }})</span>
        </template>
        
        <el-table :data="contracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="租客" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="月租金" width="100" align="right">
            <template #default="{ row }">¥{{ row.monthly_rent }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="320" align="center">
            <template #default="{ row }">
              <el-button v-if="canSign(row)" type="primary" size="small" @click="handleSign(row)">签约</el-button>
              <el-button v-if="canWithdraw(row)" type="warning" size="small" @click="handleWithdraw(row)">撤回</el-button>
              <el-button v-if="canCancel(row)" type="info" size="small" @click="handleCancel(row)">取消</el-button>
              <el-button v-if="canReject(row)" type="danger" size="small" @click="handleReject(row)">拒绝</el-button>
              <el-button v-if="row.status === 'active'" type="danger" size="small" @click="handleTerminate(row)">终止</el-button>
              <el-button size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && contracts.length === 0" description="暂无数据" />

        <div class="pagination-wrap" v-if="total >= pageSize">
          <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
        </div>
      </el-tab-pane>

      <!-- 草稿合同 -->
      <el-tab-pane name="draft">
        <template #label>
          <span>草稿 ({{ draftContracts.length }})</span>
        </template>
        
        <el-table :data="draftContracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="租客" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="月租金" width="100" align="right">
            <template #default="{ row }">¥{{ row.monthly_rent }}</template>
          </el-table-column>
          <el-table-column label="操作" min-width="280" align="center">
            <template #default="{ row }">
              <el-button type="success" size="small" @click="handleSubmitDraft(row)">发起签署</el-button>
              <el-button type="primary" size="small" @click="editContract(row)">编辑</el-button>
              <el-button size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && draftContracts.length === 0" description="暂无草稿" />
      </el-tab-pane>

      <!-- 待对方签署 -->
      <el-tab-pane name="pending_sign">
        <template #label>
          <span>待对方签署 ({{ pendingSignContracts.length }})</span>
        </template>
        
        <el-table :data="pendingSignContracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="租客" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="房东签署" width="90" align="center">
            <template #default="{ row }">{{ row.signed_by_landlord ? '✓' : '✗' }}</template>
          </el-table-column>
          <el-table-column label="租客签署" width="90" align="center">
            <template #default="{ row }">{{ row.signed_by_tenant ? '✓' : '' }}</template>
          </el-table-column>
          <el-table-column label="操作" min-width="200" align="center">
            <template #default="{ row }">
              <el-button v-if="canSign(row)" type="primary" size="small" @click="handleSign(row)">签约</el-button>
              <el-button v-if="canWithdraw(row)" type="warning" size="small" @click="handleWithdraw(row)">撤回</el-button>
              <el-button size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && pendingSignContracts.length === 0" description="暂无待对方签署的合同" />
      </el-tab-pane>

      <!-- 生效中 -->
      <el-tab-pane name="active">
        <template #label>
          <span>生效中 ({{ activeContracts.length }})</span>
        </template>
        
        <el-table :data="activeContracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="租客" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="租期" min-width="220">
            <template #default="{ row }">{{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}</template>
          </el-table-column>
          <el-table-column label="月租金" width="100" align="right">
            <template #default="{ row }">¥{{ row.monthly_rent }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160" align="center">
            <template #default="{ row }">
              <el-button type="danger" size="small" @click="handleTerminate(row)">终止</el-button>
              <el-button size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && activeContracts.length === 0" description="暂无生效合同" />
      </el-tab-pane>

      <!-- 即将到期 -->
      <el-tab-pane name="expiring">
        <template #label>
          <span>即将到期 ({{ expiringContracts.length }})</span>
        </template>
        
        <el-table :data="expiringContracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="租客" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="到期日期" min-width="150">
            <template #default="{ row }">{{ formatDate(row.end_date) }}</template>
          </el-table-column>
          <el-table-column label="剩余天数" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getDaysRemainingType(row)">{{ getDaysRemaining(row) }}天</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && expiringContracts.length === 0" description="暂无即将到期的合同" />
      </el-tab-pane>

      <!-- 已结束（包含已到期和已终止） -->
      <el-tab-pane name="expired">
        <template #label>
          <span>已结束 ({{ expiredContracts.length }})</span>
        </template>
        
        <el-table :data="expiredContracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="租客" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="结束日期" min-width="150">
            <template #default="{ row }">{{ formatDate(row.end_date) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && expiredContracts.length === 0" description="暂无已结束的合同" />
      </el-tab-pane>

      <!-- 合约申请 -->
      <el-tab-pane name="applications">
        <template #label>
          <span>
            合约申请
            <el-badge v-if="pendingApplicationsCount > 0" :value="pendingApplicationsCount" style="margin-left: 8px" />
          </span>
        </template>
        
        <el-table :data="applications" stripe v-loading="applicationsLoading">
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ applicationPropertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="租客" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ applicationUserNames[row.tenant_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="申请时间" width="160">
            <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="applicationStatusType(row.status)" size="small">{{ applicationStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <el-tooltip v-if="row.additional_notes" :content="row.additional_notes" placement="top">
                <span>{{ row.additional_notes }}</span>
              </el-tooltip>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="200" align="center" fixed="right">
            <template #default="{ row }">
              <el-button 
                v-if="row.status === 'apply_pending'" 
                type="success" 
                size="small" 
                @click="handleApproveApplication(row)"
              >
                同意
              </el-button>
              <el-button 
                v-if="row.status === 'apply_pending'" 
                type="danger" 
                size="small" 
                @click="handleRejectApplication(row)"
              >
                拒绝
              </el-button>
              <el-button size="small" @click="viewApplicationDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!applicationsLoading && applications.length === 0" description="暂无申请" />
        <div class="pagination-wrap" v-if="applicationsTotal >= applicationsPageSize">
          <el-pagination 
            background 
            layout="prev, pager, next" 
            :total="applicationsTotal" 
            :page-size="applicationsPageSize" 
            v-model:current-page="applicationsCurrentPage" 
            @current-change="loadApplications" 
          />
        </div>
      </el-tab-pane>

      <!-- 解约协商中 -->
      <el-tab-pane name="terminate_negotiating">
        <template #label>
          <span>
            解约协商中 ({{ negotiatingContracts.length }})
          </span>
        </template>
        
        <el-table :data="negotiatingContracts" stripe v-loading="loading">
          <el-table-column prop="contract_no" label="合同编号" min-width="180" show-overflow-tooltip />
          <el-table-column label="房源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ propertyNames[row.property_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="租客" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">{{ userNames[row.tenant_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column label="月租金" width="100" align="right">
            <template #default="{ row }">¥{{ row.monthly_rent }}</template>
          </el-table-column>
          <el-table-column label="状态" width="120" align="center">
            <template #default="{ row }">
              <el-tag type="warning" size="small">解约协商中</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="280" align="center">
            <template #default="{ row }">
              <el-button type="success" size="small" @click="handleApproveTermination(row)">同意解约</el-button>
              <el-button type="danger" size="small" @click="handleRejectTermination(row)">拒绝解约</el-button>
              <el-button size="small" @click="viewDetail(row)">查看详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && negotiatingContracts.length === 0" description="暂无解约协商中的合同" />
      </el-tab-pane>
    </el-tabs>



    <el-dialog v-model="detailVisible" title="合同详情" width="700px">
      <el-descriptions :column="2" border v-if="currentContract">
        <el-descriptions-item label="合同编号">{{ currentContract.contract_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(currentContract.status)" size="small">{{ statusLabel(currentContract.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="月租金">¥{{ currentContract.monthly_rent }}</el-descriptions-item>
        <el-descriptions-item label="押金">{{ currentContract.deposit ? '¥' + currentContract.deposit : '-' }}</el-descriptions-item>
        <el-descriptions-item label="开始日期">{{ formatDate(currentContract.start_date) }}</el-descriptions-item>
        <el-descriptions-item label="结束日期">{{ formatDate(currentContract.end_date) }}</el-descriptions-item>
        <el-descriptions-item label="缴费日">{{ currentContract.payment_day || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ currentContract.remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房东签约">{{ currentContract.signed_by_landlord ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="租客签约">{{ currentContract.signed_by_tenant ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item v-if="currentContract.landlord_signed_at" label="房东签约时间" :span="2">
          {{ formatDateTime(currentContract.landlord_signed_at) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentContract.tenant_signed_at" label="租客签约时间" :span="2">
          {{ formatDateTime(currentContract.tenant_signed_at) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentContract.terminate_reason" label="终止原因" :span="2">
          {{ currentContract.terminate_reason }}
        </el-descriptions-item>
        <el-descriptions-item label="合同条款" :span="2">{{ currentContract.terms || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="terminationRequestVisible" title="发起解约申请" width="600px">
      <el-alert
        title="提示"
        type="info"
        description="发起解约申请后，需要等待对方同意才能正式终止合同。"
        show-icon
        :closable="false"
        style="margin-bottom: 20px"
      />
      <el-form :model="terminateForm" label-width="120px">
        <el-form-item label="解约原因" required>
          <el-input 
            v-model="terminateForm.reason" 
            type="textarea" 
            :rows="3" 
            placeholder="请详细说明解约原因" 
          />
        </el-form-item>
        <el-form-item label="期望解约日期" required>
          <el-date-picker 
            v-model="terminateForm.expected_termination_date" 
            type="date" 
            style="width: 100%"
            placeholder="选择期望的解约日期"
          />
        </el-form-item>
        <el-form-item label="违约金金额">
          <el-input-number 
            v-model="terminateForm.penalty_amount" 
            :min="0" 
            :precision="2"
            style="width: 100%"
            placeholder="如有违约金，请输入金额"
          />
        </el-form-item>
        <el-form-item label="押金处理说明">
          <el-input 
            v-model="terminateForm.deposit_handling" 
            type="textarea" 
            :rows="2" 
            placeholder="说明押金的处理方式（退还/扣除等）"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input 
            v-model="terminateForm.additional_notes" 
            type="textarea" 
            :rows="2" 
            placeholder="其他补充说明（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="terminationRequestVisible = false">取消</el-button>
        <el-button type="primary" :loading="terminating" @click="confirmTerminate">发起申请</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="rejectVisible" title="拒绝合同" width="500px">
      <el-form :model="rejectForm" label-width="80px">
        <el-form-item label="拒绝原因">
          <el-input v-model="rejectForm.reason" type="textarea" :rows="3" placeholder="请输入拒绝原因（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :loading="rejecting" @click="confirmReject">确认拒绝</el-button>
      </template>
    </el-dialog>

    <!-- 拒绝申请对话框 -->
    <el-dialog v-model="rejectApplicationVisible" title="拒绝申请" width="500px">
      <el-form :model="rejectApplicationForm" label-width="80px">
        <el-form-item label="拒绝原因">
          <el-input v-model="rejectApplicationForm.reason" type="textarea" :rows="3" placeholder="请输入拒绝原因（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectApplicationVisible = false">取消</el-button>
        <el-button type="danger" :loading="rejectingApplication" @click="confirmRejectApplication">确认拒绝</el-button>
      </template>
    </el-dialog>

    <!-- 申请详情对话框 -->
    <el-dialog v-model="applicationDetailVisible" title="申请详情" width="700px">
      <el-descriptions :column="2" border v-if="currentApplication">
        <el-descriptions-item label="房源">{{ applicationPropertyNames[currentApplication.property_id] || '加载中...' }}</el-descriptions-item>
        <el-descriptions-item label="租客">{{ applicationUserNames[currentApplication.tenant_id] || '加载中...' }}</el-descriptions-item>
        <el-descriptions-item label="开始日期">{{ formatDate(currentApplication.start_date) }}</el-descriptions-item>
        <el-descriptions-item label="结束日期">{{ formatDate(currentApplication.end_date) }}</el-descriptions-item>
        <el-descriptions-item label="付款方式">{{ paymentMethodLabel(currentApplication.payment_method) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="applicationStatusType(currentApplication.status)" size="small">{{ applicationStatusLabel(currentApplication.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="申请时间" :span="2">{{ formatDateTime(currentApplication.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ currentApplication.additional_notes || '-' }}</el-descriptions-item>
        <el-descriptions-item v-if="currentApplication.landlord_response" label="房东回复" :span="2">
          {{ currentApplication.landlord_response }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentApplication.responded_at" label="回复时间" :span="2">
          {{ formatDateTime(currentApplication.responded_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 同意解约对话框 -->
    <el-dialog v-model="approveTerminationVisible" title="同意解约申请" width="500px">
      <el-alert
        title="提示"
        type="warning"
        description="同意解约后，合同将正式终止，请谨慎操作。"
        show-icon
        :closable="false"
        style="margin-bottom: 20px"
      />
      <el-form :model="approveTerminationForm" label-width="100px">
        <el-form-item label="处理意见">
          <el-input 
            v-model="approveTerminationForm.opinion" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入处理意见（可选）" 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approveTerminationVisible = false">取消</el-button>
        <el-button type="success" :loading="approvingTermination" @click="confirmApproveTermination">确认同意</el-button>
      </template>
    </el-dialog>

    <!-- 拒绝解约对话框 -->
    <el-dialog v-model="rejectTerminationVisible" title="拒绝解约申请" width="500px">
      <el-form :model="rejectTerminationForm" label-width="80px">
        <el-form-item label="拒绝原因" required>
          <el-input 
            v-model="rejectTerminationForm.reason" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入拒绝原因" 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectTerminationVisible = false">取消</el-button>
        <el-button type="danger" :loading="rejectingTermination" @click="confirmRejectTermination">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  getContracts,
  signContractLandlord,
  withdrawSignatureLandlord,
  cancelContract,
  rejectContract,
} from '../../api/contract'
import { getApplications, approveApplication, rejectApplication } from '../../api/contract_application'
import { 
  createTerminationRequest, 
  getTerminationRequests,
  approveTerminationRequest,
  rejectTerminationRequest 
} from '../../api/contract_termination'
import request from '../../utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'

const router = useRouter()
const { resolveItems, userNames, propertyNames } = useNameResolver()

// Tab切换
const activeTab = ref('all')

// 合同相关
const contracts = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const detailVisible = ref(false)
const terminateVisible = ref(false)
const terminationRequestVisible = ref(false)
const rejectVisible = ref(false)
const terminating = ref(false)
const rejecting = ref(false)
const submitting = ref(false)
const currentContract = ref(null)
const terminateForm = reactive({ 
  reason: '',
  expected_termination_date: '',
  penalty_amount: null,
  deposit_handling: '',
  additional_notes: ''
})
const rejectForm = reactive({ reason: '' })
const landlordInfo = ref(null)
const tenantInfo = ref(null)

// 合同分类计算属性
const draftContracts = computed(() => contracts.value.filter(c => c.status === 'draft'))
const pendingSignContracts = computed(() => contracts.value.filter(c => 
  c.status === 'pending_sign' || 
  c.status === 'part_signed' ||
  (!c.signed_by_landlord && c.status !== 'active' && c.status !== 'draft')
))
const activeContracts = computed(() => {
  const now = new Date()
  return contracts.value.filter(c => {
    if (c.status !== 'active') return false
    const endDate = new Date(c.end_date)
    // 只包含未过期的合同
    return endDate >= now
  })
})
const expiringContracts = computed(() => {
  const now = new Date()
  const thirtyDaysLater = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000)
  return contracts.value.filter(c => {
    if (c.status !== 'active') return false
    const endDate = new Date(c.end_date)
    return endDate > now && endDate <= thirtyDaysLater
  })
})
const expiredContracts = computed(() => {
  const now = new Date()
  return contracts.value.filter(c => {
    // 状态为expired的合同（已到期）
    if (c.status === 'expired') return true
    // 状态为terminated的合同（已终止）
    if (c.status === 'terminated') return true
    // 状态为active但已结束日期的合同
    if (c.status === 'active') {
      const endDate = new Date(c.end_date)
      return endDate < now
    }
    return false
  })
})

// 解约协商中的合同
const negotiatingContracts = computed(() => 
  contracts.value.filter(c => c.status === 'terminate_negotiating')
)

// 申请相关
const applications = ref([])
const applicationsLoading = ref(false)
const applicationsTotal = ref(0)
const applicationsPageSize = ref(10)
const applicationsCurrentPage = ref(1)
const pendingApplicationsCount = ref(0)
const applicationUserNames = reactive({})
const applicationPropertyNames = reactive({})
const rejectApplicationVisible = ref(false)
const applicationDetailVisible = ref(false)
const rejectingApplication = ref(false)
const currentApplication = ref(null)
const rejectApplicationForm = reactive({ reason: '' })

// 解约申请处理相关
const approveTerminationVisible = ref(false)
const rejectTerminationVisible = ref(false)
const approvingTermination = ref(false)
const rejectingTermination = ref(false)
const currentTerminationContract = ref(null)
const approveTerminationForm = reactive({ opinion: '' })
const rejectTerminationForm = reactive({ reason: '' })

// 使用枚举常量管理状态
const statusMap = {
  draft: '草稿',
  pending_sign: '待签约',
  pending_tenant_sign: '待租客签约',
  pending_landlord_sign: '待房东签约',
  active: '生效中',
  terminated: '已终止',
  cancelled: '已取消',
  rejected: '已拒绝',
  expired: '已过期',
  terminate_negotiating: '解约协商中',
}
const statusTypeMap = {
  draft: 'info',
  pending_sign: 'warning',
  pending_tenant_sign: 'warning',
  pending_landlord_sign: 'info',
  active: 'success',
  terminated: 'danger',
  cancelled: 'info',
  rejected: 'danger',
  expired: 'info',
  terminate_negotiating: 'warning',
}

// 申请状态映射
const applicationStatusMap = {
  apply_pending: '待处理',
  apply_approved: '已同意',
  apply_rejected: '已拒绝',
  apply_cancelled: '已取消',
  contract_generated: '已生成合同',
}
const applicationStatusTypeMap = {
  apply_pending: 'warning',
  apply_approved: 'success',
  apply_rejected: 'danger',
  apply_cancelled: 'info',
  contract_generated: 'success',
}

// 付款方式映射
const paymentMethodMap = {
  monthly: '月付',
  quarterly: '季付',
  semi_annual: '半年付',
  annual: '年付',
}

function statusLabel(s) {
  return statusMap[s] || s
}
function statusType(s) {
  return statusTypeMap[s] || 'info'
}
function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('zh-CN') : ''
}
function formatDateTime(d) {
  return d ? new Date(d).toLocaleString('zh-CN') : ''
}
function applicationStatusLabel(s) {
  return applicationStatusMap[s] || s
}
function applicationStatusType(s) {
  return applicationStatusTypeMap[s] || 'info'
}
function paymentMethodLabel(method) {
  return paymentMethodMap[method] || method
}

// 计算合同剩余天数
function getDaysRemaining(row) {
  if (!row.end_date) return 0
  const now = new Date()
  const endDate = new Date(row.end_date)
  const diffTime = endDate - now
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays > 0 ? diffDays : 0
}

// 根据剩余天数获取标签类型
function getDaysRemainingType(row) {
  const days = getDaysRemaining(row)
  if (days <= 7) return 'danger'
  if (days <= 15) return 'warning'
  return 'success'
}

// 判断是否可以签约
function canSign(row) {
  // 房东可以在待签署、部分签署或待房东签署状态下进行签署（房东尚未签署）
  return !row.signed_by_landlord && 
         (row.status === 'pending_sign' || row.status === 'part_signed' || row.status === 'pending_landlord_sign')
}

// 判断是否可以撤回签署
function canWithdraw(row) {
  // 只有当房东已签署且合同未生效时才能撤回
  // 允许撤回的状态：PART_SIGNED（部分签署）
  // 不允许撤回：ACTIVE（已生效）、TERMINATED（已终止）、CANCELLED（已取消）、EXPIRED（已过期）
  return row.signed_by_landlord && 
         (row.status === 'part_signed' || row.status === 'pending_sign')
}

// 判断是否可以取消
function canCancel(row) {
  // 只有草稿或待签约状态可以取消
  const cancellableStatuses = ['draft', 'pending_sign']
  return cancellableStatuses.includes(row.status)
}

// 判断是否可以拒绝
function canReject(row) {
  const rejectableStatuses = ['draft', 'pending_sign', 'part_signed']
  return rejectableStatuses.includes(row.status)
}

// Tab切换处理
function handleTabChange(tab) {
  if (['all', 'draft', 'pending_sign', 'active', 'expiring', 'expired'].includes(tab)) {
    loadData()
  } else if (tab === 'applications') {
    loadApplications()
  }
}

async function loadData() {
  loading.value = true
  try {
    const res = await getContracts({ skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value })
    contracts.value = Array.isArray(res) ? res : []
    await resolveItems(contracts.value, ['tenant_id', 'property_id'])
    total.value = Array.isArray(res) ? res.length : 0
  } catch (e) {
    ElMessage.error('加载合同列表失败')
  } finally {
    loading.value = false
  }
}

async function loadApplications() {
  applicationsLoading.value = true
  try {
    const res = await getApplications({ 
      skip: (applicationsCurrentPage.value - 1) * applicationsPageSize.value, 
      limit: applicationsPageSize.value 
    })
    applications.value = Array.isArray(res) ? res : []
    
    // 调试：打印第一条数据看看有哪些字段
    if (applications.value.length > 0) {
      console.log('申请数据示例:', applications.value[0])
    }
    
    // 计算待处理数量
    pendingApplicationsCount.value = applications.value.filter(app => app.status === 'apply_pending').length
    
    // 解析用户名和房源名
    for (const app of applications.value) {
      // 解析用户名
      if (!applicationUserNames[app.tenant_id]) {
        try {
          const userRes = await request.get(`/api/v1/users/${app.tenant_id}`)
          applicationUserNames[app.tenant_id] = userRes.nickname || userRes.username
        } catch (e) {
          console.error('获取用户信息失败:', e)
          applicationUserNames[app.tenant_id] = `用户${app.tenant_id}`
        }
      }
      
      // 解析房源名
      if (app.property_id && !applicationPropertyNames[app.property_id]) {
        try {
          const propRes = await request.get(`/api/v1/properties/${app.property_id}`)
          applicationPropertyNames[app.property_id] = propRes.title
        } catch (e) {
          console.error('获取房源信息失败，property_id:', app.property_id, e)
          applicationPropertyNames[app.property_id] = `房源${app.property_id}`
        }
      } else if (!app.property_id) {
        console.warn('申请缺少property_id:', app)
        applicationPropertyNames['missing'] = '房源信息缺失'
      }
    }
    
    applicationsTotal.value = Array.isArray(res) ? res.length : 0
  } catch (e) {
    console.error('加载申请列表失败:', e)
    ElMessage.error('加载申请列表失败: ' + (e.response?.data?.detail || e.message))
    applications.value = []
    applicationsTotal.value = 0
  } finally {
    applicationsLoading.value = false
  }
}



async function handleSign(row) {
  // 跳转到签署页面
  router.push(`/landlord/contract/${row.id}/sign`)
}

async function handleSubmitDraft(row) {
  // 直接跳转到签署页面
  router.push(`/landlord/contract/${row.id}/sign`)
}



async function handleWithdraw(row) {
  try {
    await ElMessageBox.confirm('确定撤回签署？撤回后需要重新签署合同。', '确认撤回', { type: 'warning' })
  } catch {
    return
  }
  try {
    await withdrawSignatureLandlord(row.id)
    ElMessage.success('已撤回签署')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '撤回签署失败')
  }
}

async function handleReject(row) {
  currentContract.value = row
  rejectForm.reason = ''
  rejectVisible.value = true
}

async function confirmReject() {
  rejecting.value = true
  try {
    await rejectContract(currentContract.value.id, { reason: rejectForm.reason })
    ElMessage.success('已拒绝合同')
    rejectVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '拒绝合同失败')
  } finally {
    rejecting.value = false
  }
}

async function handleTerminate(row) {
  currentContract.value = row
  // 重置表单
  terminateForm.reason = ''
  terminateForm.expected_termination_date = new Date().toISOString().split('T')[0]
  terminateForm.penalty_amount = null
  terminateForm.deposit_handling = ''
  terminateForm.additional_notes = ''
  terminationRequestVisible.value = true
}

async function confirmTerminate() {
  if (!terminateForm.reason) {
    ElMessage.warning('请输入解约原因')
    return
  }
  if (!terminateForm.expected_termination_date) {
    ElMessage.warning('请选择期望解约日期')
    return
  }
  
  terminating.value = true
  try {
    await createTerminationRequest({
      contract_id: currentContract.value.id,
      termination_reason: terminateForm.reason,
      expected_termination_date: new Date(terminateForm.expected_termination_date).toISOString(),
      penalty_amount: terminateForm.penalty_amount,
      deposit_handling: terminateForm.deposit_handling,
      additional_notes: terminateForm.additional_notes
    })
    ElMessage.success('已发起解约申请，等待对方确认')
    terminationRequestVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '发起解约申请失败')
  } finally {
    terminating.value = false
  }
}

function viewDetail(row) {
  router.push(`/landlord/contract/${row.id}`)
}

function editContract(row) {
  router.push(`/landlord/contract/${row.id}/edit`)
}


function handleSignSuccess() {
  signDialogVisible.value = false
  loadData()
}

async function handleApproveApplication(row) {
  try {
    await ElMessageBox.confirm('同意此申请后将自动生成合同草稿，是否继续？', '确认同意', { type: 'warning' })
  } catch {
    return
  }
  try {
    // 后端期望 ContractApplicationResponse 对象，包含 approved 和 response 字段
    const result = await approveApplication(row.id, { 
      approved: true,
      response: '' 
    })
    ElMessage.success('已同意申请，合同草稿已生成')
    
    // 获取生成的合同ID并跳转到编辑页面
    if (result.contract_id) {
      router.push(`/landlord/contract/${result.contract_id}/edit`)
    } else {
      loadApplications()
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '处理申请失败')
  }
}

async function handleRejectApplication(row) {
  currentApplication.value = row
  rejectApplicationForm.reason = ''
  rejectApplicationVisible.value = true
}

async function confirmRejectApplication() {
  rejectingApplication.value = true
  try {
    await rejectApplication(currentApplication.value.id, { reason: rejectApplicationForm.reason })
    ElMessage.success('已拒绝申请')
    rejectApplicationVisible.value = false
    loadApplications()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '拒绝申请失败')
  } finally {
    rejectingApplication.value = false
  }
}

function viewApplicationDetail(row) {
  currentApplication.value = row
  applicationDetailVisible.value = true
}

// 处理同意解约申请
async function handleApproveTermination(row) {
  currentTerminationContract.value = row
  approveTerminationForm.opinion = ''
  approveTerminationVisible.value = true
}

async function confirmApproveTermination() {
  approvingTermination.value = true
  try {
    // 首先需要获取该合同对应的解约申请ID
    const requests = await getTerminationRequests({ contract_id: currentTerminationContract.value.id })
    
    if (!requests || requests.length === 0) {
      ElMessage.error('未找到解约申请记录')
      return
    }
    
    const terminationRequest = requests[0]
    
    // 调用同意接口
    await approveTerminationRequest(terminationRequest.id, { 
      opinion: approveTerminationForm.opinion 
    })
    
    ElMessage.success('已同意解约申请，合同已终止')
    approveTerminationVisible.value = false
    loadData()
  } catch (e) {
    console.error('同意解约失败:', e)
    ElMessage.error(e.response?.data?.detail || '同意解约失败')
  } finally {
    approvingTermination.value = false
  }
}

// 处理拒绝解约申请
async function handleRejectTermination(row) {
  currentTerminationContract.value = row
  rejectTerminationForm.reason = ''
  rejectTerminationVisible.value = true
}

async function confirmRejectTermination() {
  if (!rejectTerminationForm.reason) {
    ElMessage.warning('请输入拒绝原因')
    return
  }
  
  rejectingTermination.value = true
  try {
    // 首先需要获取该合同对应的解约申请ID
    const requests = await getTerminationRequests({ contract_id: currentTerminationContract.value.id })
    
    if (!requests || requests.length === 0) {
      ElMessage.error('未找到解约申请记录')
      return
    }
    
    const terminationRequest = requests[0]
    
    // 调用拒绝接口
    await rejectTerminationRequest(terminationRequest.id, rejectTerminationForm.reason)
    
    ElMessage.success('已拒绝解约申请')
    rejectTerminationVisible.value = false
    loadData()
  } catch (e) {
    console.error('拒绝解约失败:', e)
    ElMessage.error(e.response?.data?.detail || '拒绝解约失败')
  } finally {
    rejectingTermination.value = false
  }
}

onMounted(() => {
  loadData()
  loadApplications()
})
</script>

<style scoped>
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

/* 让表格占满容器宽度 */
:deep(.el-table) {
  width: 100% !important;
}

:deep(.el-table__inner-wrapper) {
  width: 100% !important;
}
</style>
