<template>
  <div class="page-container">
    <div class="page-header"><h2>消息中心</h2></div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="收到的消息" name="received">
        <el-table :data="receivedMessages" stripe v-loading="loading">
          <el-table-column label="发送人" width="120">
            <template #default="{ row }">{{ userNames[row.from_user_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column prop="content" label="内容" />
          <el-table-column label="时间" width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.is_read ? 'info' : 'danger'">{{ row.is_read ? '已读' : '未读' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button v-if="!row.is_read" type="primary" size="small" @click="handleMarkRead(row)">标为已读</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && receivedMessages.length === 0" description="暂无收到的消息" />
          <div class="pagination-wrap" v-if="totalReceived >= pageSize">
            <el-pagination background layout="prev, pager, next" :total="totalReceived" :page-size="pageSize" v-model:current-page="currentPageReceived" @current-change="loadData" />
          </div>
      </el-tab-pane>
      <el-tab-pane label="发送的消息" name="sent">
        <el-table :data="sentMessages" stripe v-loading="loading">
          <el-table-column label="接收人" width="120">
            <template #default="{ row }">{{ userNames[row.to_user_id] || '加载中...' }}</template>
          </el-table-column>
          <el-table-column prop="content" label="内容" />
          <el-table-column label="时间" width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && sentMessages.length === 0" description="暂无发送的消息" />
          <div class="pagination-wrap" v-if="totalSent >= pageSize">
            <el-pagination background layout="prev, pager, next" :total="totalSent" :page-size="pageSize" v-model:current-page="currentPageSent" @current-change="loadData" />
          </div>
      </el-tab-pane>
    </el-tabs>

    <el-card style="margin-top: 20px">
      <h4>发送消息</h4>
      <el-form ref="sendFormRef" :model="sendForm" label-width="80px" style="margin-top: 12px" :rules="sendRules">
        <el-form-item label="接收人ID" prop="to_user_id">
          <el-input v-model.number="sendForm.to_user_id" placeholder="输入用户ID" style="width: 200px" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="sendForm.content" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="sending" @click="handleSend">发送</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getReceivedMessages, getSentMessages, sendMessage, markMessageRead } from '../../api/message'
import { ElMessage } from 'element-plus'
import { useNameResolver } from '../../composables/useNameResolver'

const activeTab = ref('received')
const receivedMessages = ref([])
const sentMessages = ref([])
const loading = ref(false)
const sending = ref(false)
const totalReceived = ref(0)
const totalSent = ref(0)
const pageSize = ref(10)
const currentPageReceived = ref(1)
const currentPageSent = ref(1)
const sendForm = reactive({ to_user_id: '', content: '' })
const sendFormRef = ref(null)
const sendRules = {
  to_user_id: [{ required: true, message: '请输入接收人ID', trigger: 'blur' }],
  content: [{ required: true, message: '请输入消息内容', trigger: 'blur' }],
}
const { resolveItems, userNames } = useNameResolver()

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    const [rRes, sRes] = await Promise.all([
      getReceivedMessages({ skip: (currentPageReceived.value - 1) * pageSize.value, limit: pageSize.value }),
      getSentMessages({ skip: (currentPageSent.value - 1) * pageSize.value, limit: pageSize.value }),
    ])
    receivedMessages.value = Array.isArray(rRes) ? rRes : []
    sentMessages.value = Array.isArray(sRes) ? sRes : []
    if (receivedMessages.value.length) await resolveItems(receivedMessages.value, ['from_user_id'])
    if (sentMessages.value.length) await resolveItems(sentMessages.value, ['to_user_id'])
    totalReceived.value = Array.isArray(rRes) ? rRes.length : 0
    totalSent.value = Array.isArray(sRes) ? sRes.length : 0
  } catch (e) {
    ElMessage.error('加载消息列表失败')
  } finally {
    loading.value = false
  }
}

async function handleMarkRead(msg) {
  try {
    await markMessageRead(msg.id)
    msg.is_read = true
    window.dispatchEvent(new CustomEvent('unread-changed'))
    ElMessage.success('已标为已读')
  } catch (e) {
    ElMessage.error('标记已读失败')
  }
}

async function handleSend() {
  const valid = await sendFormRef.value.validate().catch(() => false)
  if (!valid) return
  sending.value = true
  try {
    await sendMessage({ to_user_id: sendForm.to_user_id, content: sendForm.content })
    ElMessage.success('消息已发送')
    sendForm.to_user_id = ''
    sendForm.content = ''
    loadData()
  } catch (e) {
    ElMessage.error('发送消息失败')
  } finally {
    sending.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
</style>
