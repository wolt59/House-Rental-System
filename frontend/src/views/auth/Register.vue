<template>
  <div class="register-page">
    <div class="register-card">
      <h2>🏠 用户注册</h2>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" prefix-icon="User" placeholder="用户名（3-80字符）" />
        </el-form-item>
        <el-form-item prop="email">
          <el-input v-model="form.email" prefix-icon="Message" placeholder="邮箱" />
        </el-form-item>
        <el-form-item prop="phone">
          <el-input v-model="form.phone" prefix-icon="Phone" placeholder="手机号（选填）" />
        </el-form-item>
        <el-form-item prop="full_name">
          <el-input v-model="form.full_name" prefix-icon="UserFilled" placeholder="真实姓名（选填）" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" prefix-icon="Lock" type="password" placeholder="密码（至少8位）" show-password />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input v-model="form.confirmPassword" prefix-icon="Lock" type="password" placeholder="确认密码" show-password />
        </el-form-item>
        <el-form-item prop="role">
          <el-select v-model="form.role" placeholder="选择角色" style="width: 100%">
            <el-option label="租客" value="tenant" />
            <el-option label="房东" value="landlord" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleRegister">注 册</el-button>
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
  username: '',
  email: '',
  phone: '',
  full_name: '',
  password: '',
  confirmPassword: '',
  role: 'tenant',
})

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次密码不一致'))
  } else {
    callback()
  }
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.register-card {
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  width: 460px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}
.register-card h2 {
  text-align: center;
  color: #303133;
  margin-bottom: 24px;
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
