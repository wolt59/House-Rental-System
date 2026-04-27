<template>
  <div class="page-container">
    <div class="page-header"><h2>个人中心</h2></div>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <div style="text-align: center">
            <el-avatar :size="80" :src="user?.avatar_url" />
            <h3 style="margin-top: 12px">{{ user?.full_name || user?.username }}</h3>
            <el-tag :type="roleTagType" style="margin-top: 8px">{{ roleLabel }}</el-tag>
            <p style="color: #909399; font-size: 13px; margin-top: 8px">{{ user?.email }}</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="基本信息" name="info">
              <el-form :model="infoForm" label-width="80px" style="max-width: 500px">
                <el-form-item label="用户名">
                  <el-input :value="user?.username" disabled />
                </el-form-item>
                <el-form-item label="邮箱">
                  <el-input :value="user?.email" disabled />
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input v-model="infoForm.phone" />
                </el-form-item>
                <el-form-item label="真实姓名">
                  <el-input v-model="infoForm.full_name" />
                </el-form-item>
                <el-form-item label="身份证号">
                  <el-input v-model="infoForm.id_card_number" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="saving" @click="handleSaveInfo">保存修改</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
            <el-tab-pane label="修改密码" name="password">
              <el-form :model="pwdForm" label-width="100px" style="max-width: 500px">
                <el-form-item label="当前密码">
                  <el-input v-model="pwdForm.old_password" type="password" show-password />
                </el-form-item>
                <el-form-item label="新密码">
                  <el-input v-model="pwdForm.new_password" type="password" show-password />
                </el-form-item>
                <el-form-item label="确认新密码">
                  <el-input v-model="pwdForm.confirm_password" type="password" show-password />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="pwdSaving" @click="handleChangePwd">修改密码</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '../../store/user'
import { updateMe, changePassword } from '../../api/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const user = computed(() => userStore.user)
const activeTab = ref('info')
const saving = ref(false)
const pwdSaving = ref(false)

const roleLabel = computed(() => {
  const map = { admin: '管理员', landlord: '房东', tenant: '租客' }
  return map[user.value?.role] || ''
})
const roleTagType = computed(() => {
  const map = { admin: 'danger', landlord: 'warning', tenant: '' }
  return map[user.value?.role] || ''
})

const infoForm = reactive({
  phone: '',
  full_name: '',
  id_card_number: '',
})

const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

onMounted(() => {
  if (user.value) {
    infoForm.phone = user.value.phone || ''
    infoForm.full_name = user.value.full_name || ''
    infoForm.id_card_number = user.value.id_card_number || ''
  }
})

async function handleSaveInfo() {
  saving.value = true
  try {
    await updateMe(infoForm)
    await userStore.fetchUser()
    ElMessage.success('信息已更新')
  } catch (e) {} finally {
    saving.value = false
  }
}

async function handleChangePwd() {
  if (pwdForm.new_password !== pwdForm.confirm_password) {
    ElMessage.warning('两次密码不一致')
    return
  }
  if (pwdForm.new_password.length < 8) {
    ElMessage.warning('密码至少8位')
    return
  }
  pwdSaving.value = true
  try {
    await changePassword({ old_password: pwdForm.old_password, new_password: pwdForm.new_password })
    ElMessage.success('密码已修改')
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdForm.confirm_password = ''
  } catch (e) {} finally {
    pwdSaving.value = false
  }
}
</script>
