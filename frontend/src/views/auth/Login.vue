<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>
    <div class="login-card">
      <div class="card-header">
        <div class="logo-icon">H</div>
        <h2>智能房屋租赁系统</h2>
        <p class="subtitle">欢迎回来，请登录您的账号</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" prefix-icon="User" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" prefix-icon="Lock" type="password" placeholder="请输入密码" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">登 录</el-button>
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
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.08;
}

.shape-1 {
  width: 600px;
  height: 600px;
  background: var(--primary);
  top: -200px;
  right: -100px;
  animation: float 8s ease-in-out infinite;
}

.shape-2 {
  width: 400px;
  height: 400px;
  background: #a78bfa;
  bottom: -100px;
  left: -100px;
  animation: float 10s ease-in-out infinite reverse;
}

.shape-3 {
  width: 300px;
  height: 300px;
  background: var(--primary);
  top: 50%;
  left: 60%;
  animation: float 12s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.login-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 20px;
  padding: 48px 40px 36px;
  width: 420px;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
  animation: slideUp 0.5s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

.card-header { text-align: center; margin-bottom: 32px; }

.card-header .logo-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, var(--primary), #a78bfa);
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-size: 28px;
  margin-bottom: 16px;
}

.card-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.subtitle {
  color: var(--text-muted);
  font-size: 14px;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  border-radius: 10px;
}

.footer-link {
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
  margin-top: 8px;
}

.footer-link a {
  color: var(--primary);
  font-weight: 500;
}
</style>
