<template>
  <div class="register-page">
    <div class="register-bg">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>
    <div class="register-card">
      <div class="card-header">
        <div class="logo-icon">H</div>
        <h2>创建账号</h2>
        <p class="subtitle">注册成为租客或房东</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" size="large">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item prop="username">
              <el-input v-model="form.username" prefix-icon="User" placeholder="用户名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item prop="role">
              <el-select v-model="form.role" placeholder="角色" style="width: 100%">
                <el-option label="租客" value="tenant" />
                <el-option label="房东" value="landlord" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item prop="email">
          <el-input v-model="form.email" prefix-icon="Message" placeholder="邮箱" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item prop="phone">
              <el-input v-model="form.phone" prefix-icon="Phone" placeholder="手机号（选填）" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item prop="full_name">
              <el-input v-model="form.full_name" prefix-icon="UserFilled" placeholder="真实姓名（选填）" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item prop="password">
          <el-input v-model="form.password" prefix-icon="Lock" type="password" placeholder="密码（至少8位）" show-password />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input v-model="form.confirmPassword" prefix-icon="Lock" type="password" placeholder="确认密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="register-btn" @click="handleRegister">注 册</el-button>
        </el-form-item>
      </el-form>
      <div class="footer-link">
        已有账号？<router-link to="/login">立即登录</router-link>
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

const form = reactive({
  username: '', email: '', phone: '', full_name: '',
  password: '', confirmPassword: '', role: 'tenant',
})

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) callback(new Error('两次密码不一致'))
  else callback()
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 80, message: '用户名3-80字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

async function handleRegister() {
  await formRef.value.validate()
  loading.value = true
  try {
    const { confirmPassword, ...data } = form
    await userStore.register(data)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  position: relative;
  overflow: hidden;
}

.register-bg {
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
  left: -100px;
  animation: float 8s ease-in-out infinite;
}

.shape-2 {
  width: 400px;
  height: 400px;
  background: #a78bfa;
  bottom: -100px;
  right: -100px;
  animation: float 10s ease-in-out infinite reverse;
}

.shape-3 {
  width: 300px;
  height: 300px;
  background: var(--primary);
  top: 40%;
  left: 70%;
  animation: float 12s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.register-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 20px;
  padding: 40px 36px;
  width: 520px;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
  animation: slideUp 0.5s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

.card-header { text-align: center; margin-bottom: 28px; }

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
  margin-bottom: 12px;
}

.card-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.subtitle {
  color: var(--text-muted);
  font-size: 14px;
}

.register-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  border-radius: 10px;
}

.footer-link {
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
  margin-top: 4px;
}

.footer-link a {
  color: var(--primary);
  font-weight: 500;
}
</style>
