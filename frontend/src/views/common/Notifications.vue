<template>
  <div class="notif-container">
    <div class="notif-header">
      <h2>通知中心</h2>
    </div>
    <div class="notif-body" v-loading="loading">
      <div class="notification-list" v-if="notifications.length > 0">
        <div
          v-for="msg in notifications"
          :key="msg.id"
          :class="['notification-item', { unread: !msg.is_read }]"
          @click="markAsRead(msg)"
        >
          <div class="notif-icon">
            <el-icon :size="20"><Bell /></el-icon>
          </div>
          <div class="notif-content">
            <div class="notif-text">{{ msg.content }}</div>
            <div class="notif-time">{{ formatTime(msg.created_at) }}</div>
          </div>
          <el-tag v-if="!msg.is_read" size="small" type="danger">未读</el-tag>
        </div>
      </div>
      <el-empty v-if="!loading && notifications.length === 0" description="暂无通知" />
      <div class="pagination-wrap" v-if="total > pageSize">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="total"
          :page-size="pageSize"
          v-model:current-page="currentPage"
          @current-change="loadNotifications"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Bell } from '@element-plus/icons-vue'
import { useUserStore } from '../../store/user'
import {
  getReceivedMessages,
  markMessageRead,
  createWebSocket,
} from '../../api/message'

const userStore = useUserStore()

const notifications = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = 10
const total = ref(0)

let ws = null
let wsReconnectTimer = null

function formatTime(d) {
  if (!d) return ''
  const date = new Date(d)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const msgDay = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  if (msgDay.getTime() === today.getTime()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  const yesterday = new Date(today.getTime() - 86400000)
  if (msgDay.getTime() === yesterday.getTime()) {
    return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }) + ' ' +
    date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

async function loadNotifications() {
  loading.value = true
  try {
    const res = await getReceivedMessages({
      skip: (currentPage.value - 1) * pageSize,
      limit: pageSize,
    })
    const all = Array.isArray(res) ? res : []
    notifications.value = all.filter(
      m => m.message_type === 'system' || m.message_type === 'notification'
    )
    total.value = all.filter(
      m => m.message_type === 'system' || m.message_type === 'notification'
    ).length
  } catch (e) {
    ElMessage.error('加载通知失败')
  } finally {
    loading.value = false
  }
}

async function markAsRead(msg) {
  if (msg.is_read) return
  try {
    await markMessageRead(msg.id)
    msg.is_read = true
  } catch (e) {
    console.error('markMessageRead failed:', e)
  }
}

function connectWebSocket() {
  const token = sessionStorage.getItem('token')
  if (!token) return
  try {
    ws = createWebSocket(token)
    ws.onopen = () => {
      console.log('[WS] Connected')
    }
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'new_message') {
          const msg = data.message
          if (msg.message_type === 'system' || msg.message_type === 'notification') {
            loadNotifications()
            window.dispatchEvent(new CustomEvent('unread-changed', { detail: { count: data.unread_count } }))
          }
        }
      } catch (e) {
        console.error('[WS] Parse error:', e)
      }
    }
    ws.onclose = (e) => {
      console.log('[WS] Disconnected:', e.code, e.reason)
      if (wsReconnectTimer) clearTimeout(wsReconnectTimer)
      wsReconnectTimer = setTimeout(connectWebSocket, 3000)
    }
    ws.onerror = (e) => {
      console.error('[WS] Error:', e)
    }
  } catch (e) {
    console.error('[WS] Connection failed:', e)
  }
}

onMounted(() => {
  loadNotifications()
  connectWebSocket()
})

onBeforeUnmount(() => {
  if (wsReconnectTimer) clearTimeout(wsReconnectTimer)
  if (ws) {
    ws.onclose = null
    ws.close()
    ws = null
  }
})
</script>

<style scoped>
.notif-container {
  height: calc(100vh - var(--header-height));
  display: flex;
  flex-direction: column;
  background: #fff;
}

.notif-header {
  padding: 16px 24px 0;
}

.notif-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.notif-body {
  flex: 1;
  margin: 0 24px 24px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.notification-list {
  flex: 1;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.15s;
}

.notification-item:hover {
  background: #f5f7fa;
}

.notification-item.unread {
  background: #f0f9ff;
}

.notif-icon {
  color: #e6a23c;
  flex-shrink: 0;
  margin-top: 2px;
}

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-text {
  font-size: 14px;
  color: #303133;
  line-height: 1.5;
  margin-bottom: 4px;
}

.notif-time {
  font-size: 12px;
  color: #909399;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}
</style>