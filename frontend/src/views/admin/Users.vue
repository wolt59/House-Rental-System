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
    <el-table :data="users" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="email" label="邮箱" width="200" />
      <el-table-column prop="full_name" label="姓名" width="120" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="roleType(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">{{ row.is_active ? '正常' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="注册时间" width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button :type="row.is_active ? 'danger' : 'success'" size="small" @click="handleToggleStatus(row)">
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="editVisible" title="编辑用户" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="手机号"><el-input v-model="editForm.phone" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="editForm.full_name" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role">
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
const editVisible = ref(false)
const saving = ref(false)
const filters = reactive({ role: '' })
const editForm = reactive({ id: '', phone: '', full_name: '', role: '' })

const roleMap = { admin: '管理员', landlord: '房东', tenant: '租客' }
const roleTypeMap = { admin: 'danger', landlord: 'warning', tenant: '' }
function roleLabel(r) { return roleMap[r] || r }
function roleType(r) { return roleTypeMap[r] || 'info' }
function formatDate(d) { return d ? new Date(d).toLocaleString('zh-CN') : '' }

async function loadData() {
  loading.value = true
  try {
    const params = { limit: 50 }
    if (filters.role) params.role = filters.role
    const res = await getUsers(params)
    users.value = Array.isArray(res) ? res : []
  } catch (e) {} finally {
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
  saving.value = true
  try {
    await updateUser(editForm.id, { phone: editForm.phone, full_name: editForm.full_name, role: editForm.role })
    ElMessage.success('更新成功')
    editVisible.value = false
    loadData()
  } catch (e) {} finally {
    saving.value = false
  }
}

async function handleToggleStatus(row) {
  try {
    await toggleUserStatus(row.id)
    ElMessage.success('状态已更新')
    loadData()
  } catch (e) {}
}

onMounted(loadData)
</script>
