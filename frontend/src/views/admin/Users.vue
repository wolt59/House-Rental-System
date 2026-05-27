<template>
  <div class="page-container">
    <div class="page-header"><h2>用户管理</h2></div>
    <el-form :inline="true" :model="filters" style="margin-bottom: 16px">
      <el-form-item label="角色">
        <el-select v-model="filters.role" clearable placeholder="全部" @change="loadData">
          <el-option label="租客" value="tenant" />
          <el-option label="房东" value="landlord" />
          <el-option label="管理员" value="admin" />
        </el-select>
      </el-form-item>
    </el-form>
    <el-table :data="users" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" width="140" />
      <el-table-column prop="email" label="邮箱" min-width="220" />
      <el-table-column prop="full_name" label="姓名" width="120" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="roleType(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">{{ row.is_active ? '正常' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="注册时间" width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button :type="row.is_active ? 'danger' : 'success'" size="small" @click="handleToggleStatus(row)">
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && users.length === 0" description="暂无数据" />

    <div class="pagination-wrap" v-if="total >= pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize" v-model:current-page="currentPage" @current-change="loadData" />
    </div>

    <el-dialog v-model="editVisible" title="编辑用户" width="600px">
      <el-form ref="formRef" :model="editForm" label-width="90px" :rules="userRules">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="手机号"><el-input v-model="editForm.phone" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名"><el-input v-model="editForm.full_name" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="角色">
          <el-select v-model="editForm.role" style="width: 100%">
            <el-option label="租客" value="tenant" />
            <el-option label="房东" value="landlord" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

  </div>
</template>


<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getUsers, updateUser, toggleUserStatus } from '../../api/user'
import { ElMessage } from 'element-plus'

const users = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(10)
const currentPage = ref(1)
const editVisible = ref(false)
const saving = ref(false)
const formRef = ref(null)
const filters = reactive({ role: '' })
const editForm = reactive({ id: '', phone: '', full_name: '', role: '' })

const userRules = {
  full_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const roleMap = { admin: '管理员', landlord: '房东', tenant: '租客' }
const roleTypeMap = { admin: 'danger', landlord: 'warning', tenant: 'info' }
function roleLabel(r) { return roleMap[r] || r }
function roleType(r) { return roleTypeMap[r] || 'info' }
function formatDate(d) { return d ? new Date(d).toLocaleString('zh-CN') : '' }

async function loadData() {
  loading.value = true
  try {
    const params = { skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value }
    if (filters.role) params.role = filters.role
    const res = await getUsers(params)
    users.value = Array.isArray(res) ? res : []
    total.value = Array.isArray(res) ? res.length : 0
  } catch (e) { ElMessage.error('加载用户列表失败') } finally {
    loading.value = false
  }
}

function openEditDialog(row) {
  editForm.id = row.id
  editForm.phone = row.phone || ''
  editForm.full_name = row.full_name || ''
  editForm.role = row.role
  editVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await updateUser(editForm.id, { phone: editForm.phone, full_name: editForm.full_name, role: editForm.role })
    ElMessage.success('更新成功')
    editVisible.value = false
    loadData()
  } catch (e) { ElMessage.error('保存用户信息失败') } finally {
    saving.value = false
  }
}

async function handleToggleStatus(row) {
  try {
    await toggleUserStatus(row.id)
    ElMessage.success('状态已更新')
    loadData()
  } catch (e) { ElMessage.error('更新用户状态失败') }
}

onMounted(loadData)
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; margin-top: 20px; }
</style>
