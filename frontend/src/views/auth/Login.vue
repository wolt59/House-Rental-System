<template>
  <div class="login-page">
    <div class="login-card">
      <h2>🏠 智能房屋租赁系统</h2>
      <p class="subtitle">欢迎登录</p>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" prefix-icon="User" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" prefix-icon="Lock" type="password" placeholder="请输入密码" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleLogin">登 录</el-button>
        </el-form-item>
      </el-form>
      <div class="footer-link">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../store/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    await userStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    const role = userStore.userRole
    if (role === 'admin') router.push('/admin/dashboard')
    else if (role === 'landlord') router.push('/landlord/properties')
    else router.push('/')
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}
.login-card h2 {
  text-align: center;
  color: #303133;
  margin-bottom: 8px;
}
.subtitle {
  text-align: center;
  color: #909399;
  margin-bottom: 30px;
}
.footer-link {
  text-align: center;
  color: #909399;
  font-size: 14px;
}
.footer-link a {
  color: #409eff;
  text-decoration: none;
}
</style>
