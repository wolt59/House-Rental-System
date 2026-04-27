<template>
  <el-container class="main-layout">
    <el-header class="header">
      <div class="header-left">
        <h1 class="logo" @click="$router.push('/')">🏠 智能房屋租赁系统</h1>
      </div>
      <div class="header-right">
        <template v-if="userStore.isLoggedIn">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :src="userStore.user?.avatar_url" />
              <span class="username">{{ userStore.user?.full_name || userStore.user?.username }}</span>
              <el-tag size="small" :type="roleTagType">{{ roleLabel }}</el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button type="primary" @click="$router.push('/login')">登录</el-button>
          <el-button @click="$router.push('/register')">注册</el-button>
        </template>
      </div>
    </el-header>
    <el-container>
      <el-aside width="220px" class="aside" v-if="userStore.isLoggedIn">
        <el-menu :default-active="$route.path" router class="aside-menu">
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/properties">
            <el-icon><OfficeBuilding /></el-icon>
            <span>房源列表</span>
          </el-menu-item>
          <el-menu-item index="/search">
            <el-icon><Search /></el-icon>
            <span>智能搜索</span>
          </el-menu-item>
          <el-menu-item index="/news">
            <el-icon><Document /></el-icon>
            <span>新闻资讯</span>
          </el-menu-item>
          <el-menu-item index="/messages">
            <el-icon><ChatDotRound /></el-icon>
            <span>消息中心</span>
          </el-menu-item>

          <el-divider v-if="userStore.isTenant || userStore.isAdmin" />

          <template v-if="userStore.isTenant || userStore.isAdmin">
            <el-sub-menu index="tenant-menu">
              <template #title>
                <el-icon><User /></el-icon>
                <span>租客功能</span>
              </template>
              <el-menu-item index="/tenant/bookings">预约看房</el-menu-item>
              <el-menu-item index="/tenant/contracts">我的合同</el-menu-item>
              <el-menu-item index="/tenant/payments">租金支付</el-menu-item>
              <el-menu-item index="/tenant/maintenance">维修申请</el-menu-item>
              <el-menu-item index="/tenant/complaints">投诉管理</el-menu-item>
            </el-sub-menu>
          </template>

          <template v-if="userStore.isLandlord || userStore.isAdmin">
            <el-sub-menu index="landlord-menu">
              <template #title>
                <el-icon><House /></el-icon>
                <span>房东功能</span>
              </template>
              <el-menu-item index="/landlord/properties">房源管理</el-menu-item>
              <el-menu-item index="/landlord/bookings">预约管理</el-menu-item>
              <el-menu-item index="/landlord/contracts">合同管理</el-menu-item>
              <el-menu-item index="/landlord/payments">收款管理</el-menu-item>
              <el-menu-item index="/landlord/news">新闻管理</el-menu-item>
            </el-sub-menu>
          </template>

          <template v-if="userStore.isAdmin">
            <el-divider />
            <el-sub-menu index="admin-menu">
              <template #title>
                <el-icon><Setting /></el-icon>
                <span>系统管理</span>
              </template>
              <el-menu-item index="/admin/dashboard">数据统计</el-menu-item>
              <el-menu-item index="/admin/users">用户管理</el-menu-item>
              <el-menu-item index="/admin/properties">房源审核</el-menu-item>
              <el-menu-item index="/admin/audit-logs">审计日志</el-menu-item>
            </el-sub-menu>
          </template>
        </el-menu>
      </el-aside>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import { HomeFilled, OfficeBuilding, Search, Document, ChatDotRound, User, House, Setting } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const roleLabel = computed(() => {
  const map = { admin: '管理员', landlord: '房东', tenant: '租客' }
  return map[userStore.userRole] || ''
})

const roleTagType = computed(() => {
  const map = { admin: 'danger', landlord: 'warning', tenant: '' }
  return map[userStore.userRole] || ''
})

function handleCommand(cmd) {
  if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  height: 60px;
}
.logo {
  cursor: pointer;
  font-size: 20px;
  color: #409eff;
  margin: 0;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.username {
  font-size: 14px;
}
.aside {
  background: #fff;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
}
.aside-menu {
  border-right: none;
}
.main-content {
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
  overflow-y: auto;
}
</style>
