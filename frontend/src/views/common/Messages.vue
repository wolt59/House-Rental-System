<template>
  <div class="page-container">
    <div class="page-header"><h2>消息中心</h2></div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="收到的消息" name="received">
        <el-table :data="receivedMessages" stripe v-loading="loading">
          <el-table-column label="发送人" width="120">
            <template #default="{ row }">用户{{ row.from_user_id }}</template>
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
      </el-tab-pane>
      <el-tab-pane label="发送的消息" name="sent">
        <el-table :data="sentMessages" stripe v-loading="loading">
          <el-table-column label="接收人" width="120">
            <template #default="{ row }">用户{{ row.to_user_id }}</template>
          </el-table-column>
          <el-table-column prop="content" label="内容" />
          <el-table-column label="时间" width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-card style="margin-top: 20px">
      <h4>发送消息</h4>
      <el-form :model="sendForm" label-width="80px" style="margin-top: 12px">
        <el-form-item label="接收人ID">
          <el-input v-model.number="sendForm.to_user_id" placeholder="输入用户ID" style="width: 200px" />
        </el-form-item>
        <el-form-item label="内容">
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

const activeTab = ref('received')
const receivedMessages = ref([])
const sentMessages = ref([])
const loading = ref(false)
const sending = ref(false)
const sendForm = reactive({ to_user_id: '', content: '' })

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    const [rRes, sRes] = await Promise.all([
      getReceivedMessages({ limit: 50 }),
      getSentMessages({ limit: 50 }),
    ])
    receivedMessages.value = Array.isArray(rRes) ? rRes : []
    sentMessages.value = Array.isArray(sRes) ? sRes : []
  } catch (e) {} finally {
    loading.value = false
  }
}

async function handleMarkRead(msg) {
  try {
    await markMessageRead(msg.id)
    msg.is_read = true
    ElMessage.success('已标为已读')
  } catch (e) {}
}

async function handleSend() {
  if (!sendForm.to_user_id || !sendForm.content) {
    ElMessage.warning('请填写完整')
    return
  }
  sending.value = true
  try {
    await sendMessage({ to_user_id: sendForm.to_user_id, content: sendForm.content })
    ElMessage.success('消息已发送')
    sendForm.to_user_id = ''
    sendForm.content = ''
    loadData()
  } catch (e) {} finally {
    sending.value = false
  }
}

onMounted(loadData)
</script>
