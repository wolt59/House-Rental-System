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
              <div :class="['message-bubble', msg.from_user_id === currentUserId ? 'bubble-self' : 'bubble-peer', `bubble-${msg.message_type}`]">
                <!-- 文本消息 -->
                <div v-if="msg.message_type === 'text' || msg.message_type === 'system' || msg.message_type === 'notification'" class="bubble-content">
                  {{ msg.content }}
                </div>
                <!-- 图片消息 -->
                <div v-else-if="msg.message_type === 'image'" class="bubble-media">
                  <el-image
                    :src="absoluteUrl(msg.file_url)"
                    :preview-src-list="[absoluteUrl(msg.file_url)]"
                    :preview-teleported="true"
                    fit="cover"
                    class="bubble-image"
                    :initial-index="0"
                  />
                  <div v-if="msg.content" class="bubble-media-caption">{{ msg.content }}</div>
                </div>
                <!-- 音频消息 -->
                <div v-else-if="msg.message_type === 'audio'" class="bubble-media">
                  <audio :src="absoluteUrl(msg.file_url)" controls preload="metadata" class="bubble-audio"></audio>
                  <div v-if="msg.content" class="bubble-media-caption">{{ msg.content }}</div>
                </div>
                <!-- 视频消息 -->
                <div v-else-if="msg.message_type === 'video'" class="bubble-media">
                  <video :src="absoluteUrl(msg.file_url)" controls preload="metadata" class="bubble-video"></video>
                  <div v-if="msg.content" class="bubble-media-caption">{{ msg.content }}</div>
                </div>
                <!-- 文件消息 -->
                <div v-else-if="msg.message_type === 'file'" class="bubble-file">
                  <el-icon class="bubble-file-icon"><Document /></el-icon>
                  <div class="bubble-file-info">
                    <a :href="absoluteUrl(msg.file_url)" :download="msg.file_name || ''" class="bubble-file-name" target="_blank" rel="noopener">
                      {{ msg.file_name || '下载文件' }}
                    </a>
                    <div class="bubble-file-meta">{{ formatFileSize(msg.file_size) }}</div>
                  </div>
                  <el-icon class="bubble-file-download"><Download /></el-icon>
                </div>
                <!-- 兜底 -->
                <div v-else class="bubble-content">{{ msg.content || msg.message_type }}</div>
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

          <!-- 待发送的附件预览 -->
          <div v-if="pendingFile" class="pending-file-bar">
            <div class="pending-file-preview">
              <el-image
                v-if="pendingFile.message_type === 'image'"
                :src="pendingFile.preview"
                fit="cover"
                class="pending-thumb"
                :preview-src-list="[pendingFile.preview]"
                :preview-teleported="true"
              />
              <el-icon v-else class="pending-icon">
                <Document />
              </el-icon>
            </div>
            <div class="pending-file-info">
              <div class="pending-file-name">{{ pendingFile.name }}</div>
              <div class="pending-file-meta">
                {{ formatFileSize(pendingFile.size) }}
                <span v-if="pendingFile.message_type !== 'image'">· {{ fileTypeLabel(pendingFile.message_type) }}</span>
              </div>
              <el-progress
                v-if="uploadProgress > 0 && uploadProgress < 100"
                :percentage="uploadProgress"
                :stroke-width="3"
                class="pending-progress"
              />
            </div>
            <el-button
              v-if="!sending"
              link
              type="danger"
              :icon="CircleClose"
              @click="clearPendingFile"
              class="pending-remove"
            />
          </div>

          <div class="message-input-area">
            <div class="input-toolbar">
              <el-tooltip content="发送图片" placement="top">
                <el-button :icon="Picture" link @click="triggerImagePicker" :disabled="sending" class="tool-btn" />
              </el-tooltip>
              <el-tooltip content="发送文件" placement="top">
                <el-button :icon="Paperclip" link @click="triggerFilePicker" :disabled="sending" class="tool-btn" />
              </el-tooltip>
            </div>
            <div class="input-row">
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
                :disabled="!canSend"
                @click="handleSend"
                class="send-btn"
                round
              >
                发送
              </el-button>
            </div>
            <input
              ref="imageInputRef"
              type="file"
              accept="image/*"
              class="hidden-input"
              @change="onFileSelected"
            />
            <input
              ref="fileInputRef"
              type="file"
              class="hidden-input"
              @change="onFileSelected"
            />
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
import {
  Search, Loading, Picture, Paperclip, Document, Download, CircleClose,
} from '@element-plus/icons-vue'
import { useUserStore } from '../../store/user'
import {
  getConversations,
  getConversationMessages,
  sendMessage,
  markConversationRead,
  searchUsers,
  uploadChatFile,
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

// 文件上传相关
const imageInputRef = ref(null)
const fileInputRef = ref(null)
const pendingFile = ref(null) // { file, name, size, preview, message_type }
const uploadProgress = ref(0)
const lastPickerWasImage = ref(false)

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
const canSend = computed(() => Boolean((inputContent.value && inputContent.value.trim()) || pendingFile.value))

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

function formatFileSize(size) {
  if (size === null || size === undefined) return ''
  const n = Number(size)
  if (!Number.isFinite(n) || n <= 0) return ''
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  if (n < 1024 * 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(2)} MB`
  return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

function absoluteUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  return window.location.origin + url
}

function fileTypeLabel(type) {
  return { image: '图片', file: '文件', audio: '语音', video: '视频' }[type] || '附件'
}

function inferMessageType(file) {
  const mime = (file.type || '').toLowerCase()
  if (mime.startsWith('image/')) return 'image'
  if (mime.startsWith('audio/')) return 'audio'
  if (mime.startsWith('video/')) return 'video'
  return 'file'
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

function triggerImagePicker() {
  lastPickerWasImage.value = true
  if (imageInputRef.value) imageInputRef.value.value = ''
  imageInputRef.value?.click()
}

function triggerFilePicker() {
  lastPickerWasImage.value = false
  if (fileInputRef.value) fileInputRef.value.value = ''
  fileInputRef.value?.click()
}

function onFileSelected(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 20MB')
    return
  }
  const messageType = lastPickerWasImage.value ? 'image' : inferMessageType(file)
  const preview = messageType === 'image' ? URL.createObjectURL(file) : ''
  pendingFile.value = {
    file,
    name: file.name,
    size: file.size,
    preview,
    message_type: messageType,
  }
  uploadProgress.value = 0
}

function clearPendingFile() {
  if (pendingFile.value?.preview) {
    URL.revokeObjectURL(pendingFile.value.preview)
  }
  pendingFile.value = null
  uploadProgress.value = 0
}

function previewTextFor(pending, caption) {
  const t = pending.message_type
  if (t === 'file') return `[文件] ${pending.name}`
  if (caption) return `[${fileTypeLabel(t)}] ${caption}`
  return `[${fileTypeLabel(t)}]`
}

function updateConversationPreview(msg) {
  const conv = conversations.value.find(c => c.participant.id === activeConversationId.value)
  if (!conv) return
  const caption = msg.content || ''
  if (msg.message_type === 'text') {
    conv.last_message = caption.substring(0, 80)
  } else if (msg.message_type === 'file') {
    conv.last_message = `[文件] ${msg.file_name || ''}`.substring(0, 80)
  } else {
    conv.last_message = previewTextFor({ message_type: msg.message_type }, caption)
  }
  conv.last_message_time = msg.created_at || new Date().toISOString()
  conv.last_message_type = msg.message_type
  // 把最新会话置顶
  const idx = conversations.value.indexOf(conv)
  if (idx > 0) {
    conversations.value.splice(idx, 1)
    conversations.value.unshift(conv)
  }
}

async function handleSend(e) {
  if (e && e.shiftKey) return
  if (e) e.preventDefault()
  if (!activeConversationId.value || sending.value) return

  const caption = inputContent.value.trim()
  if (pendingFile.value) {
    await sendFileMessage(caption)
  } else {
    if (!caption) return
    await sendTextMessage(caption)
  }
}

async function sendTextMessage(content) {
  sending.value = true
  try {
    const msg = await sendMessage({
      to_user_id: activeConversationId.value,
      content,
      message_type: 'text',
    })
    messages.value.push(msg)
    inputContent.value = ''
    await nextTick()
    scrollToBottom()
    updateConversationPreview(msg)
  } catch (e) {
    ElMessage.error('发送消息失败')
  } finally {
    sending.value = false
  }
}

async function sendFileMessage(caption) {
  const pending = pendingFile.value
  if (!pending) return
  sending.value = true
  uploadProgress.value = 0
  let uploaded = null
  try {
    uploaded = await uploadChatFile(pending.file, (ev) => {
      if (ev.total) {
        uploadProgress.value = Math.round((ev.loaded / ev.total) * 100)
      }
    })
  } catch (e) {
    ElMessage.error('文件上传失败')
    sending.value = false
    return
  }

  try {
    const msg = await sendMessage({
      to_user_id: activeConversationId.value,
      content: caption,
      message_type: uploaded.message_type || pending.message_type,
      file_url: uploaded.url,
      file_name: uploaded.original_name || pending.name,
      file_size: uploaded.size,
      mime_type: uploaded.mime_type,
    })
    messages.value.push(msg)
    clearPendingFile()
    inputContent.value = ''
    await nextTick()
    scrollToBottom()
    updateConversationPreview(msg)
  } catch (e) {
    ElMessage.error('消息发送失败')
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
    // 避免重复
    if (!messages.value.find(m => m.id === msg.id)) {
      messages.value.push(msg)
      nextTick(() => scrollToBottom())
    }
    markConversationRead(msg.from_user_id).catch((e) => console.error(e))
    // 同步更新会话预览
    const conv = conversations.value.find(c => c.participant.id === msg.from_user_id)
    if (conv) updateConversationPreviewOnIncoming(conv, msg)
  } else {
    loadConversations()
  }
}

function updateConversationPreviewOnIncoming(conv, msg) {
  const caption = msg.content || ''
  if (msg.message_type === 'text') {
    conv.last_message = caption.substring(0, 80)
  } else if (msg.message_type === 'file') {
    conv.last_message = `[文件] ${msg.file_name || ''}`.substring(0, 80)
  } else {
    conv.last_message = previewTextFor({ message_type: msg.message_type }, caption)
  }
  conv.last_message_time = msg.created_at || new Date().toISOString()
  conv.last_message_type = msg.message_type
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
  if (pendingFile.value?.preview) {
    URL.revokeObjectURL(pendingFile.value.preview)
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

/* 媒体类消息：去掉 padding 占位以方便图像/文件显示 */
.bubble-image,
.bubble-audio,
.bubble-video,
.bubble-file {
  padding: 8px 12px;
}

.bubble-media {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bubble-image {
  max-width: 240px;
  max-height: 240px;
  border-radius: 8px;
  display: block;
  cursor: pointer;
}

.bubble-audio {
  width: 240px;
  outline: none;
}

.bubble-video {
  max-width: 320px;
  max-height: 240px;
  border-radius: 6px;
  background: #000;
}

.bubble-media-caption {
  font-size: 13px;
  word-break: break-word;
  white-space: pre-wrap;
}

.bubble-file {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 200px;
}

.bubble-file-icon {
  font-size: 32px;
  color: #409eff;
  flex-shrink: 0;
}

.bubble-self .bubble-file-icon {
  color: #fff;
}

.bubble-file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.bubble-file-name {
  font-size: 14px;
  color: inherit;
  text-decoration: none;
  word-break: break-all;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.bubble-file-name:hover {
  text-decoration: underline;
}

.bubble-file-meta {
  font-size: 12px;
  opacity: 0.7;
}

.bubble-file-download {
  font-size: 18px;
  opacity: 0.85;
  flex-shrink: 0;
}

.pending-file-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-top: 1px solid #e4e7ed;
  background: #fafbfc;
}

.pending-file-preview {
  width: 56px;
  height: 56px;
  border-radius: 6px;
  overflow: hidden;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pending-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.pending-icon {
  font-size: 28px;
  color: #909399;
}

.pending-file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pending-file-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  word-break: break-all;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.pending-file-meta {
  font-size: 12px;
  color: #909399;
}

.pending-progress {
  margin-top: 2px;
}

.pending-remove {
  flex-shrink: 0;
}

.message-input-area {
  padding: 8px 20px 12px;
  border-top: 1px solid #e4e7ed;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-toolbar {
  display: flex;
  gap: 4px;
}

.tool-btn {
  font-size: 18px;
  color: #606266;
}

.tool-btn:hover {
  color: #409eff;
}

.input-row {
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

.hidden-input {
  display: none;
}
</style>
