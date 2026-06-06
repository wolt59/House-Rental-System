<template>
  <el-container class="main-layout">
    <el-header class="header">
      <div class="header-left">
        <div class="logo" @click="$router.push('/')">
          <div class="logo-icon">H</div>
          <span class="logo-text">智能房屋租赁</span>
        </div>
      </div>
      <div class="header-right">
        <template v-if="userStore.isLoggedIn">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="36" :src="userStore.user?.avatar_url" class="user-avatar" />
              <span class="username">{{ userStore.user?.full_name || userStore.user?.username }}</span>
              <el-tag size="small" :type="roleTagType" effect="dark" round>{{ roleLabel }}</el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile"><el-icon><User /></el-icon>个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided><el-icon><SwitchButton /></el-icon>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button type="primary" round @click="$router.push('/login')">登录</el-button>
          <el-button round @click="$router.push('/register')">注册</el-button>
        </template>
      </div>
    </el-header>
    <el-container>
      <el-aside :width="sidebarWidth" class="aside" v-if="userStore.isLoggedIn">
        <div class="sidebar-inner">
          <el-menu :default-active="$route.path" router class="aside-menu" :collapse="false">
            <!-- 管理员 -->
            <template v-if="userStore.isAdmin">
              <div class="menu-group-label">系统管理</div>
              <el-menu-item index="/admin/dashboard">
                <el-icon><DataAnalysis /></el-icon><span>数据面板</span>
              </el-menu-item>
              <el-menu-item index="/admin/users">
                <el-icon><UserFilled /></el-icon><span>用户管理</span>
              </el-menu-item>
              <el-menu-item index="/admin/properties">
                <el-icon><OfficeBuilding /></el-icon><span>房源管理</span>
              </el-menu-item>
              <el-menu-item index="/admin/audit-logs">
                <el-icon><Notebook /></el-icon><span>审计日志</span>
              </el-menu-item>
              <el-menu-item index="/admin/news">
                <el-icon><Document /></el-icon><span>新闻审核</span>
              </el-menu-item>
              <el-menu-item index="/admin/contracts">
                <el-icon><DocumentChecked /></el-icon><span>合同总览</span>
              </el-menu-item>
              <el-menu-item index="/admin/bookings">
                <el-icon><Calendar /></el-icon><span>预约总览</span>
              </el-menu-item>
              <el-menu-item index="/admin/maintenance">
                <el-icon><Tools /></el-icon><span>维修总览</span>
              </el-menu-item>
              <el-menu-item index="/admin/complaints">
                <el-icon><WarningFilled /></el-icon><span>投诉总览</span>
              </el-menu-item>
              <el-menu-item index="/admin/payments">
                <el-icon><Money /></el-icon><span>账单管理</span>
              </el-menu-item>
              <el-menu-item index="/admin/messages">
                <el-icon><ChatDotRound /></el-icon>
                <span>消息中心</span>
                <el-badge :value="chatUnread" :hidden="chatUnread === 0" :max="99" class="menu-badge" />
              </el-menu-item>
              <el-menu-item index="/admin/notifications">
                <el-icon><Bell /></el-icon>
                <span>通知中心</span>
                <el-badge :value="notifUnread" :hidden="notifUnread === 0" :max="99" class="menu-badge" />
              </el-menu-item>
            </template>

            <!-- 租客/房东 -->
            <template v-else>
              <div class="menu-group-label">导航</div>
              <el-menu-item index="/">
                <el-icon><HomeFilled /></el-icon><span>首页</span>
              </el-menu-item>
              <el-menu-item index="/properties">
                <el-icon><OfficeBuilding /></el-icon><span>房源列表</span>
              </el-menu-item>
              <el-menu-item index="/search">
                <el-icon><Search /></el-icon><span>智能搜索</span>
              </el-menu-item>
              <el-menu-item index="/news">
                <el-icon><Document /></el-icon><span>新闻资讯</span>
              </el-menu-item>
              <el-menu-item index="/messages">
                <el-icon><ChatDotRound /></el-icon>
                <span>消息中心</span>
                <el-badge :value="chatUnread" :hidden="chatUnread === 0" :max="99" class="menu-badge" />
              </el-menu-item>
              <el-menu-item index="/notifications">
                <el-icon><Bell /></el-icon>
                <span>通知中心</span>
                <el-badge :value="notifUnread" :hidden="notifUnread === 0" :max="99" class="menu-badge" />
              </el-menu-item>

              <template v-if="userStore.isTenant">
                <div class="menu-group-label">租客功能</div>
                <el-menu-item index="/tenant/bookings">
                  <el-icon><Calendar /></el-icon><span>预约看房</span>
                </el-menu-item>
                <el-menu-item index="/tenant/contracts">
                  <el-icon><DocumentChecked /></el-icon><span>我的合同</span>
                </el-menu-item>
                <el-menu-item index="/tenant/payments">
                  <el-icon><Money /></el-icon><span>我的账单</span>
                </el-menu-item>
                <el-menu-item index="/tenant/maintenance">
                  <el-icon><Tools /></el-icon><span>维修申请</span>
                </el-menu-item>
                <el-menu-item index="/tenant/complaints">
                  <el-icon><WarningFilled /></el-icon><span>投诉提交</span>
                </el-menu-item>
              </template>

              <template v-if="userStore.isLandlord">
                <div class="menu-group-label">房东功能</div>
                <el-menu-item index="/landlord/dashboard">
                  <el-icon><DataAnalysis /></el-icon><span>数据面板</span>
                </el-menu-item>
                <el-menu-item index="/landlord/properties">
                  <el-icon><OfficeBuilding /></el-icon><span>房源管理</span>
                </el-menu-item>
                <el-menu-item index="/landlord/bookings">
                  <el-icon><Calendar /></el-icon><span>预约管理</span>
                </el-menu-item>
                <el-menu-item index="/landlord/contracts">
                  <el-icon><DocumentChecked /></el-icon><span>合同管理</span>
                </el-menu-item>
                <el-menu-item index="/landlord/payments">
                  <el-icon><Money /></el-icon><span>收款管理</span>
                </el-menu-item>
                <el-menu-item index="/landlord/maintenance">
                  <el-icon><Tools /></el-icon><span>维修管理</span>
                </el-menu-item>
                <el-menu-item index="/landlord/complaints">
                  <el-icon><WarningFilled /></el-icon><span>投诉管理</span>
                </el-menu-item>
                <el-menu-item index="/landlord/news">
                  <el-icon><Document /></el-icon><span>新闻管理</span>
                </el-menu-item>
              </template>
            </template>
          </el-menu>
        </div>
      </el-aside>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import { getUnreadCount } from '../api/message'
import {
  HomeFilled, OfficeBuilding, Search, Document, ChatDotRound,
  User, SwitchButton, DataAnalysis, UserFilled, Notebook,
  Calendar, DocumentChecked, Money, Tools, WarningFilled, Bell,
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const sidebarWidth = '220px'
const chatUnread = ref(0)
const notifUnread = ref(0)

let unreadTimer = null

async function fetchUnreadCount() {
  if (!userStore.isLoggedIn) return
  try {
    const [chatRes, notifRes] = await Promise.all([
      getUnreadCount('chat'),
      getUnreadCount('notification'),
    ])
    chatUnread.value = chatRes.total_unread || 0
    notifUnread.value = notifRes.total_unread || 0
  } catch (e) {
    // silent
  }
}

onMounted(() => {
  fetchUnreadCount()
  unreadTimer = setInterval(fetchUnreadCount, 30000)
  window.addEventListener('unread-changed', fetchUnreadCount)
})

onBeforeUnmount(() => {
  if (unreadTimer) clearInterval(unreadTimer)
  window.removeEventListener('unread-changed', fetchUnreadCount)
})

const roleLabel = computed(() => {
  const map = { admin: '管理员', landlord: '房东', tenant: '租客' }
  return map[userStore.userRole] || ''
})

const roleTagType = computed(() => {
  const map = { admin: 'danger', landlord: 'warning', tenant: 'primary' }
  return map[userStore.userRole] || 'info'
})

function handleCommand(cmd) {
  if (cmd === 'profile') router.push('/profile')
  else if (cmd === 'logout') userStore.logout(router)
}
</script>

<style scoped>
.main-layout { height: 100vh; }

/* ===== Header ===== */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  padding: 0 24px;
  height: var(--header-height);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 100;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--primary), #a78bfa);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-size: 18px;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
}

.header-right { display: flex; align-items: center; gap: 12px; }

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 12px 4px 4px;
  border-radius: 50px;
  background: rgba(255, 255, 255, 0.1);
  transition: background 0.2s;
}

.user-info:hover { background: rgba(255, 255, 255, 0.18); }

.user-avatar { border: 2px solid rgba(255, 255, 255, 0.3); }

.username { font-size: 14px; color: #fff; font-weight: 500; }

/* ===== Sidebar ===== */
.aside {
  background: #fff;
  border-right: 1px solid var(--border);
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 0.2s;
}

.sidebar-inner { padding: 8px 0; min-height: calc(100vh - var(--header-height)); }

.aside-menu {
  border-right: none;
  --el-menu-item-height: 44px;
}

.aside-menu .el-menu-item {
  margin: 2px 8px;
  border-radius: 8px;
  transition: all 0.2s;
}

.aside-menu .el-menu-item.is-active {
  background: var(--primary-bg) !important;
  color: var(--primary) !important;
  font-weight: 600;
}

.aside-menu .el-menu-item.is-active::before {
  display: none;
}

.aside-menu .el-menu-item:hover {
  background: #f1f5f9;
}

.menu-group-label {
  padding: 16px 16px 6px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.menu-badge {
  margin-left: auto;
}

.menu-badge :deep(.el-badge__content) {
  position: static;
  transform: none;
}

/* ===== Main Content ===== */
.main-content {
  background: var(--bg-page);
  min-height: calc(100vh - var(--header-height));
  overflow-y: auto;
  padding: 0;
}
</style>
