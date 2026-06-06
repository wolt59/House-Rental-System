<template>
  <div class="chat-container">
    <div class="chat-header">
      <h2>聊天</h2>
    </div>

    <div class="chat-layout">
      <div class="conversation-panel" :style="{ width: convPanelWidth + 'px' }">
        <div class="conversation-search">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用户开始聊天..."
            :prefix-icon="Search"
            clearable
            @keyup.enter="handleSearchUsers"
            @clear="searchResults = []"
          />
          <div class="search-results" v-if="searchResults.length > 0">
            <div
              v-for="user in searchResults"
              :key="user.id"
              class="search-result-item"
              @click="selectNewConversation(user)"
            >
              <el-avatar :size="32">{{ (user.full_name || user.username).charAt(0) }}</el-avatar>
              <div class="search-result-info">
                <span class="search-result-name">{{ user.full_name || user.username }}</span>
                <span class="search-result-role">{{ roleLabel(user.role) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="conversation-list" v-loading="convLoading">
          <div
            v-for="conv in conversations"
            :key="conv.participant.id"
            :class="['conversation-item', { active: activeConversationId === conv.participant.id }]"
            @click="selectConversation(conv)"
          >
            <div class="conv-avatar">
              <el-badge :value="conv.unread_count" :hidden="conv.unread_count === 0" :max="99">
                <el-avatar :size="44">{{ conv.participant.full_name?.charAt(0) || conv.participant.username?.charAt(0) || '?' }}</el-avatar>
              </el-badge>
            </div>
            <div class="conv-content">
              <div class="conv-top">
                <span class="conv-name">{{ conv.participant.full_name || conv.participant.username }}</span>
                <span class="conv-time">{{ formatTime(conv.last_message_time) }}</span>
              </div>
              <div class="conv-preview">{{ conv.last_message }}</div>
            </div>
          </div>
          <el-empty v-if="!convLoading && conversations.length === 0" description="暂无会话" />
        </div>
      </div>
      <div class="drag-handle" @mousedown="startDrag" @dblclick="resetConvWidth"></div>

      <div class="message-panel">
        <div class="message-panel-empty" v-if="!activeConversationId">
          <el-empty description="选择一个会话开始聊天" :image-size="120" />
        </div>
        <template v-else>
          <div class="message-panel-header">
            <span class="message-peer-name">{{ activePeerName }}</span>
          </div>
          <div class="message-list" ref="messageListRef" @scroll="handleScroll">
            <div
              v-for="msg in messages"
              :key="msg.id"
              :class="['message-bubble-wrapper', msg.from_user_id === currentUserId ? 'message-self' : 'message-peer']"
            >
              <el-avatar v-if="msg.from_user_id !== currentUserId" :size="32" class="msg-avatar">
                {{ activePeerName?.charAt(0) || '?' }}
              </el-avatar>
              <div :class="['message-bubble', msg.from_user_id === currentUserId ? 'bubble-self' : 'bubble-peer']">
                <div class="bubble-content">{{ msg.content }}</div>
                <div class="bubble-time">{{ formatTime(msg.created_at) }}</div>
              </div>
              <el-avatar v-if="msg.from_user_id === currentUserId" :size="32" class="msg-avatar">
                {{ currentUserName?.charAt(0) || '我' }}
              </el-avatar>
            </div>
            <div v-if="loadingMore" class="loading-more">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>加载更多...</span>
            </div>
          </div>
          <div class="message-input-area">
            <el-input
              v-model="inputContent"
              type="textarea"
              :rows="3"
              placeholder="输入消息..."
              maxlength="5000"
              show-word-limit
              @keydown.enter.exact="handleSend"
              :disabled="sending"
            />
            <el-button
              type="primary"
              :loading="sending"
              :disabled="!inputContent.trim()"
              @click="handleSend"
              class="send-btn"
              round
            >
              发送
            </el-button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Loading } from '@element-plus/icons-vue'
import { useUserStore } from '../../store/user'
import {
  getConversations,
  getConversationMessages,
  sendMessage,
  markConversationRead,
  searchUsers,
  createWebSocket,
} from '../../api/message'

const route = useRoute()
const userStore = useUserStore()

const conversations = ref([])
const convLoading = ref(false)
const activeConversationId = ref(null)
const activePeerName = ref('')
const messages = ref([])
const inputContent = ref('')
const sending = ref(false)
const totalUnread = ref(0)
const messageListRef = ref(null)
const searchKeyword = ref('')
const searchResults = ref([])
const loadingMore = ref(false)
const hasMore = ref(true)
const currentPage = ref(0)
const PAGE_SIZE = 30

const convPanelWidth = ref(320)
const MIN_CONV_WIDTH = 240
const MAX_CONV_RATIO = 0.5
let dragging = false

function startDrag(e) {
  dragging = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  const startX = e.clientX
  const startW = convPanelWidth.value

  function onMouseMove(ev) {
    if (!dragging) return
    const delta = ev.clientX - startX
    const newW = Math.max(MIN_CONV_WIDTH, Math.min(window.innerWidth * MAX_CONV_RATIO, startW + delta))
    convPanelWidth.value = newW
  }

  function onMouseUp() {
    dragging = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

function resetConvWidth() {
  convPanelWidth.value = 320
}

const currentUserId = computed(() => userStore.user?.id)
const currentUserName = computed(() => userStore.user?.full_name || userStore.user?.username)

let ws = null
let wsReconnectTimer = null

function roleLabel(role) {
  const map = { admin: '管理员', landlord: '房东', tenant: '租客' }
  return map[role] || role
}

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

async function loadConversations() {
  convLoading.value = true
  try {
    const res = await getConversations()
    conversations.value = res.conversations || []
    totalUnread.value = res.total_unread || 0
  } catch (e) {
    ElMessage.error('加载会话列表失败')
  } finally {
    convLoading.value = false
  }
}

async function loadMessages(peerUserId, appendBefore = false) {
  try {
    const res = await getConversationMessages(peerUserId, {
      skip: appendBefore ? currentPage.value * PAGE_SIZE : 0,
      limit: PAGE_SIZE,
    })
    if (appendBefore) {
      messages.value = [...res, ...messages.value]
    } else {
      messages.value = res || []
    }
    hasMore.value = (res && res.length >= PAGE_SIZE)
    if (appendBefore) {
      currentPage.value++
    }
    if (!appendBefore) {
      await nextTick()
      scrollToBottom()
    }
  } catch (e) {
    ElMessage.error('加载消息失败')
  }
}

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

async function handleScroll() {
  const el = messageListRef.value
  if (!el || loadingMore.value || !hasMore.value) return
  if (el.scrollTop <= 50) {
    loadingMore.value = true
    const prevScrollHeight = el.scrollHeight
    await loadMessages(activeConversationId.value, true)
    await nextTick()
    el.scrollTop = el.scrollHeight - prevScrollHeight
    loadingMore.value = false
  }
}

async function selectConversation(conv) {
  if (activeConversationId.value === conv.participant.id) return
  activeConversationId.value = conv.participant.id
  activePeerName.value = conv.participant.full_name || conv.participant.username
  currentPage.value = 0
  hasMore.value = true
  await loadMessages(conv.participant.id, false)
  if (conv.unread_count > 0) {
    try {
      await markConversationRead(conv.participant.id)
      totalUnread.value = Math.max(0, totalUnread.value - conv.unread_count)
      conv.unread_count = 0
      window.dispatchEvent(new CustomEvent('unread-changed'))
    } catch (e) {
      console.error('markConversationRead failed:', e)
    }
  }
}

async function selectNewConversation(user) {
  searchKeyword.value = ''
  searchResults.value = []
  const existing = conversations.value.find(c => c.participant.id === user.id)
  if (existing) {
    await selectConversation(existing)
  } else {
    activeConversationId.value = user.id
    activePeerName.value = user.full_name || user.username
    currentPage.value = 0
    hasMore.value = false
    messages.value = []
    conversations.value.unshift({
      participant: {
        id: user.id,
        username: user.username,
        full_name: user.full_name,
        avatar_url: user.avatar_url,
      },
      last_message: '开始新的对话...',
      last_message_time: new Date().toISOString(),
      last_message_type: 'text',
      unread_count: 0,
      property_id: null,
    })
  }
}

async function handleSearchUsers() {
  const kw = searchKeyword.value.trim()
  if (!kw || kw.length < 1) {
    searchResults.value = []
    return
  }
  try {
    const res = await searchUsers(kw, 10)
    searchResults.value = res || []
  } catch (e) {
    searchResults.value = []
  }
}

async function handleSend(e) {
  if (e && e.shiftKey) return
  if (e) e.preventDefault()
  const content = inputContent.value.trim()
  if (!content || !activeConversationId.value) return
  sending.value = true
  try {
    const msg = await sendMessage({
      to_user_id: activeConversationId.value,
      content: content,
    })
    messages.value.push(msg)
    inputContent.value = ''
    await nextTick()
    scrollToBottom()
    const conv = conversations.value.find(c => c.participant.id === activeConversationId.value)
    if (conv) {
      conv.last_message = content.substring(0, 80)
      conv.last_message_time = msg.created_at || new Date().toISOString()
      conv.last_message_type = 'text'
    }
  } catch (e) {
    ElMessage.error('发送消息失败')
  } finally {
    sending.value = false
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
          handleIncomingMessage(data)
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

function handleIncomingMessage(data) {
  const msg = data.message
  if (msg.message_type === 'system' || msg.message_type === 'notification') {
    return
  }
  totalUnread.value = data.unread_count || (totalUnread.value + 1)
  window.dispatchEvent(new CustomEvent('unread-changed', { detail: { count: totalUnread.value } }))
  if (activeConversationId.value === msg.from_user_id) {
    messages.value.push(msg)
    nextTick(() => scrollToBottom())
    markConversationRead(msg.from_user_id).catch((e) => console.error(e))
  } else {
    loadConversations()
  }
}

onMounted(async () => {
  await loadConversations()
  connectWebSocket()

  const queryPeerId = route.query?.with
  if (queryPeerId) {
    const peerId = parseInt(queryPeerId)
    if (!isNaN(peerId)) {
      const existing = conversations.value.find(c => c.participant.id === peerId)
      if (existing) {
        await selectConversation(existing)
      } else {
        activeConversationId.value = peerId
        activePeerName.value = `用户#${peerId}`
        currentPage.value = 0
        hasMore.value = false
        messages.value = []
        conversations.value.unshift({
          participant: { id: peerId, username: `用户#${peerId}`, full_name: null, avatar_url: null },
          last_message: '',
          last_message_time: new Date().toISOString(),
          last_message_type: 'text',
          unread_count: 0,
          property_id: null,
        })
      }
    }
  }
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
.chat-container {
  height: calc(100vh - var(--header-height));
  display: flex;
  flex-direction: column;
  background: #fff;
}

.chat-header {
  padding: 16px 24px 0;
}

.chat-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.chat-layout {
  flex: 1;
  display: flex;
  height: 100%;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  margin: 0 24px 24px;
  min-height: 0;
}

.conversation-panel {
  width: 320px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  background: #fafafa;
}

.conversation-search {
  padding: 12px;
  position: relative;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 12px;
  right: 12px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 10;
  max-height: 240px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.search-result-item:hover {
  background: #f0f5ff;
}

.search-result-info {
  display: flex;
  flex-direction: column;
}

.search-result-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.search-result-role {
  font-size: 12px;
  color: #909399;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f0f0f0;
}

.conversation-item:hover {
  background: #f0f5ff;
}

.conversation-item.active {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
  padding-left: 13px;
}

.conv-avatar {
  flex-shrink: 0;
}

.conv-content {
  flex: 1;
  min-width: 0;
}

.conv-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.conv-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-time {
  font-size: 11px;
  color: #909399;
  white-space: nowrap;
  flex-shrink: 0;
  margin-left: 8px;
}

.conv-preview {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.drag-handle {
  width: 5px;
  cursor: col-resize;
  background: transparent;
  flex-shrink: 0;
  transition: background 0.15s;
  position: relative;
  z-index: 1;
}

.drag-handle:hover {
  background: #409eff;
}

.drag-handle::after {
  content: '';
  position: absolute;
  left: -4px;
  right: -4px;
  top: 0;
  bottom: 0;
}

.message-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.message-panel-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-panel-header {
  padding: 12px 20px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
}

.message-peer-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  background: #f5f7fa;
  min-height: 0;
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  color: #909399;
  font-size: 13px;
}

.message-bubble-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 16px;
}

.message-bubble-wrapper.message-self {
  flex-direction: row;
  justify-content: flex-end;
}

.msg-avatar {
  flex-shrink: 0;
  margin-top: 4px;
}

.message-bubble {
  max-width: 60%;
  padding: 10px 14px;
  border-radius: 12px;
  position: relative;
}

.bubble-self {
  background: linear-gradient(135deg, #409eff, #66b1ff);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.bubble-peer {
  background: #fff;
  color: #303133;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.bubble-content {
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.bubble-time {
  font-size: 11px;
  margin-top: 4px;
  opacity: 0.7;
  text-align: right;
}

.bubble-peer .bubble-time {
  color: #909399;
}

.message-input-area {
  padding: 12px 20px;
  border-top: 1px solid #e4e7ed;
  background: #fff;
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.message-input-area :deep(.el-textarea__inner) {
  resize: none;
}

.send-btn {
  flex-shrink: 0;
  height: 36px;
}
</style>