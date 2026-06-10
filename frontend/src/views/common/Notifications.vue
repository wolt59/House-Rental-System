<template>
  <div class="notif-container">
    <div class="notif-header">
      <h2>通知中心</h2>
    </div>
    <div class="notif-toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索通知内容..."
        :prefix-icon="Search"
        clearable
        class="search-input"
        @input="handleSearch"
      />
      <el-select v-model="filterType" placeholder="通知类型" clearable class="filter-select" @change="handleFilterChange">
        <el-option label="全部" value="" />
        <el-option label="未读" value="unread" />
        <el-option label="已读" value="read" />
      </el-select>
      <el-button v-if="hasUnread" type="primary" text @click="markAllRead">
        全部已读
      </el-button>
    </div>
    <div class="notif-body" v-loading="loading">
      <div class="notification-list" v-if="displayNotifications.length > 0">
        <div
          v-for="msg in displayNotifications"
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
          <el-tag v-if="!msg.is_read" size="small" type="danger" class="notif-tag">未读</el-tag>
          <div class="notif-actions" @click.stop>
            <el-button
              v-if="msg.link"
              type="primary"
              size="small"
              text
              @click="handleAction(msg)"
            >
              去处理
            </el-button>
          </div>
        </div>
      </div>
      <el-empty v-if="!loading && displayNotifications.length === 0" description="暂无通知" />
    </div>
    <div class="pagination-wrap" v-if="totalNotifs > pageSize">
      <el-pagination background layout="prev, pager, next" :total="totalNotifs" :page-size="pageSize" v-model:current-page="currentPage" @current-change="onPageChange" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Bell, Search } from '@element-plus/icons-vue'
import { useUserStore } from '../../store/user'
import {
  getReceivedMessages,
  markMessageRead,
  createWebSocket,
} from '../../api/message'

const router = useRouter()
const userStore = useUserStore()

const notifications = ref([])
const loading = ref(false)
const searchKeyword = ref('')
const filterType = ref('')
const pageSize = ref(15)
const currentPage = ref(1)
const totalNotifs = ref(0)

let ws = null
let wsReconnectTimer = null

const hasUnread = computed(() => notifications.value.some(n => !n.is_read))

const filteredNotifications = computed(() => {
  let result = notifications.value

  if (filterType.value === 'unread') {
    result = result.filter(n => !n.is_read)
  } else if (filterType.value === 'read') {
    result = result.filter(n => n.is_read)
  }

  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    result = result.filter(n => n.content && n.content.toLowerCase().includes(kw))
  }

  return result
})

const displayNotifications = computed(() => {
  const list = filteredNotifications.value
  totalNotifs.value = list.length
  const start = (currentPage.value - 1) * pageSize.value
  return list.slice(start, start + pageSize.value)
})

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
      skip: 0,
      limit: 500,
      type: 'system,notification',
    })
    notifications.value = (res && res.items) || []
  } catch (e) {
    ElMessage.error('加载通知失败')
  } finally {
    loading.value = false
  }
}

function notifyBadgeRefresh() {
  window.dispatchEvent(new CustomEvent('unread-changed'))
}

async function markAsRead(msg) {
  if (msg.is_read) return
  try {
    await markMessageRead(msg.id)
    msg.is_read = true
    notifyBadgeRefresh()
  } catch (e) {
    console.error('markMessageRead failed:', e)
  }
}

async function markAllRead() {
  const unreadList = notifications.value.filter(n => !n.is_read)
  for (const msg of unreadList) {
    await markAsRead(msg)
  }
  notifyBadgeRefresh()
  ElMessage.success('已全部标记为已读')
}

function handleAction(msg) {
  if (!msg.link) return
  if (!msg.is_read) {
    markMessageRead(msg.id).then(() => {
      msg.is_read = true
      notifyBadgeRefresh()
    }).catch(() => {})
  }
  router.push(msg.link)
}

function handleSearch() {
  currentPage.value = 1
}

function handleFilterChange() {
  currentPage.value = 1
}

function onPageChange() {}

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

.notif-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
}

.search-input {
  width: 280px;
}

.filter-select {
  width: 120px;
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
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.15s;
  position: relative;
}

.notification-item:hover {
  background: #f5f7fa;
}

.notification-item:hover .notif-actions {
  opacity: 1;
  visibility: visible;
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

.notif-tag {
  flex-shrink: 0;
}

.notif-actions {
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s, visibility 0.2s;
  flex-shrink: 0;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}


</style>
