<template>
  <div class="permission-page">
    <el-card v-if="isAdmin" shadow="never" class="perm-card">
      <el-form :model="query" inline class="query-form">
        <el-form-item label="工号">
          <el-input v-model="query.employeeNo" placeholder="请输入工号" clearable />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="query.name" placeholder="请输入姓名" clearable />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="query.department" placeholder="请输入部门" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <div class="toolbar">
        <el-button type="primary" plain @click="openCreateDialog">新增用户</el-button>
        <el-button type="success" plain @click="openEditBySelection">修改信息</el-button>
        <el-button type="warning" plain @click="openPermissionBySelection">分配权限</el-button>
        <el-button type="danger" plain @click="deleteBySelection">删除账号</el-button>
      </div>

      <el-table :data="users" border :loading="loading" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="48" />
        <el-table-column prop="employee_no" label="工号" min-width="100" />
        <el-table-column prop="username" label="账号" min-width="100" />
        <el-table-column prop="name" label="姓名" min-width="110" />
        <el-table-column prop="department" label="部门" min-width="120" />
        <el-table-column prop="position" label="职位" min-width="120" />
        <el-table-column label="角色" width="90">
          <template #default="{ row }">
            {{ row.role === 'admin' ? '管理员' : '员工' }}
          </template>
        </el-table-column>
        <el-table-column label="权限" min-width="210">
          <template #default="{ row }">
            <el-tag v-for="perm in row.permissions" :key="perm" size="small" class="perm-tag">{{ perm }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
            <el-button link type="warning" @click="openPermissionDialog(row)">分配权限</el-button>
            <el-button link type="danger" @click="deleteOneUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="pager.current"
          v-model:page-size="pager.pageSize"
          :page-sizes="[5, 10, 20]"
          background
          layout="total, sizes, prev, pager, next"
          :total="pager.total"
          @current-change="fetchUsers"
          @size-change="onPageSizeChange"
        />
      </div>
    </el-card>

    <el-card v-else shadow="never" class="perm-card">
      <template #header>我的权限</template>
      <el-descriptions v-if="me" :column="2" border>
        <el-descriptions-item label="账号">{{ me.username }}</el-descriptions-item>
        <el-descriptions-item label="工号">{{ me.employee_no }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ me.name }}</el-descriptions-item>
        <el-descriptions-item label="部门">{{ me.department }}</el-descriptions-item>
        <el-descriptions-item label="职位">{{ me.position }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ me.role === 'admin' ? '管理员' : '员工' }}</el-descriptions-item>
      </el-descriptions>
      <div class="my-perms">
        <div class="my-perms-title">已拥有权限</div>
        <el-empty v-if="!myPermissions.length" description="暂无权限" />
        <el-tag v-for="perm in myPermissions" :key="perm" class="perm-tag">{{ perm }}</el-tag>
      </div>
    </el-card>

    <el-dialog
      v-model="userDialog.visible"
      :title="userDialog.mode === 'create' ? '新增用户账号' : '修改用户信息'"
      width="680px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" placeholder="请输入账号" :disabled="userDialog.mode === 'edit'" />
        </el-form-item>
        <el-form-item label="工号" prop="employeeNo">
          <el-input v-model="form.employeeNo" placeholder="请输入工号" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-input v-model="form.department" placeholder="请输入部门" />
        </el-form-item>
        <el-form-item label="职位" prop="position">
          <el-input v-model="form.position" placeholder="请输入职位" />
        </el-form-item>
        <el-form-item v-if="userDialog.mode === 'create'" label="登录密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入登录密码" />
        </el-form-item>
        <el-form-item v-if="userDialog.mode === 'create'" label="确认密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" show-password placeholder="请再次输入密码" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" class="full-input">
            <el-option label="管理员" value="admin" />
            <el-option label="员工" value="employee" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitUserForm">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="permDialog.visible" title="分配权限" width="560px" destroy-on-close>
      <el-checkbox-group v-model="permDialog.permissions" class="perm-checks">
        <el-checkbox v-for="perm in permissionOptions" :key="perm" :label="perm">{{ perm }}</el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="permDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitPermissionForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSession } from '../../auth/session'
import { http } from '../../api/http'

const session = getSession()
const isAdmin = computed(() => session?.roleKey === 'admin' || session?.username === 'admin')

const query = reactive({ employeeNo: '', name: '', department: '' })
const users = ref([])
const loading = ref(false)
const selectedRows = ref([])
const permissionOptions = ref([])

const pager = reactive({ current: 1, pageSize: 10, total: 0 })

const me = ref(null)
const myPermissions = ref([])

const userDialog = reactive({ visible: false, mode: 'create' })
const permDialog = reactive({ visible: false, userId: null, permissions: [] })

const formRef = ref(null)
const form = reactive({
  id: null,
  username: '',
  employeeNo: '',
  name: '',
  department: '',
  position: '',
  role: 'employee',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (_rule, value, callback) => {
  if (userDialog.mode !== 'create') {
    callback()
    return
  }
  if (!value) {
    callback(new Error('请输入确认密码'))
    return
  }
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
    return
  }
  callback()
}

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  employeeNo: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  department: [{ required: true, message: '请输入部门', trigger: 'blur' }],
  position: [{ required: true, message: '请输入职位', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  password: [
    { required: true, message: '请输入登录密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }]
}

const fetchPermissionOptions = async () => {
  const { data } = await http.get('/api/v1/permissions/options')
  permissionOptions.value = data.items || []
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const { data } = await http.get('/api/v1/users', {
      params: {
        requester_username: session.username,
        employee_no: query.employeeNo,
        name: query.name,
        department: query.department,
        page: pager.current,
        page_size: pager.pageSize
      }
    })
    users.value = data.items || []
    pager.total = data.total || 0
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const fetchMe = async () => {
  try {
    const [meRes, permsRes] = await Promise.all([
      http.get('/api/v1/users/me', { params: { username: session.username } }),
      http.get('/api/v1/users/me/permissions', { params: { username: session.username } })
    ])
    me.value = meRes.data
    myPermissions.value = permsRes.data.permissions || []
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载我的权限失败')
  }
}

const handleSearch = async () => {
  pager.current = 1
  await fetchUsers()
}

const handleReset = async () => {
  query.employeeNo = ''
  query.name = ''
  query.department = ''
  pager.current = 1
  await fetchUsers()
}

const onPageSizeChange = async () => {
  pager.current = 1
  await fetchUsers()
}

const onSelectionChange = (rows) => {
  selectedRows.value = rows
}

const resetForm = () => {
  form.id = null
  form.username = ''
  form.employeeNo = ''
  form.name = ''
  form.department = ''
  form.position = ''
  form.role = 'employee'
  form.password = ''
  form.confirmPassword = ''
}

const openCreateDialog = () => {
  resetForm()
  userDialog.mode = 'create'
  userDialog.visible = true
}

const openEditDialog = (row) => {
  form.id = row.id
  form.username = row.username
  form.employeeNo = row.employee_no
  form.name = row.name
  form.department = row.department
  form.position = row.position
  form.role = row.role
  form.password = ''
  form.confirmPassword = ''
  userDialog.mode = 'edit'
  userDialog.visible = true
}

const openEditBySelection = () => {
  if (selectedRows.value.length !== 1) {
    ElMessage.warning('请先勾选且仅勾选一条用户记录')
    return
  }
  openEditDialog(selectedRows.value[0])
}

const openPermissionDialog = (row) => {
  permDialog.userId = row.id
  permDialog.permissions = [...(row.permissions || [])]
  permDialog.visible = true
}

const openPermissionBySelection = () => {
  if (selectedRows.value.length !== 1) {
    ElMessage.warning('请先勾选且仅勾选一条用户记录')
    return
  }
  openPermissionDialog(selectedRows.value[0])
}

const submitUserForm = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  const payload = {
    username: form.username,
    employee_no: form.employeeNo,
    name: form.name,
    department: form.department,
    position: form.position,
    role: form.role
  }

  try {
    if (userDialog.mode === 'create') {
      await http.post(
        '/api/v1/users',
        { ...payload, password: form.password, permissions: [] },
        { params: { requester_username: session.username } }
      )
      ElMessage.success('新增用户成功')
    } else {
      await http.put(`/api/v1/users/${form.id}`, payload, { params: { requester_username: session.username } })
      ElMessage.success('用户信息修改成功')
    }

    userDialog.visible = false
    await fetchUsers()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存失败')
  }
}

const submitPermissionForm = async () => {
  try {
    await http.put(
      `/api/v1/users/${permDialog.userId}/permissions`,
      { permissions: permDialog.permissions },
      { params: { requester_username: session.username } }
    )
    ElMessage.success('权限分配成功')
    permDialog.visible = false
    await fetchUsers()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '权限分配失败')
  }
}

const deleteOneUser = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除账号 ${row.username} 吗？`, '提示', { type: 'warning' })
    await http.delete(`/api/v1/users/${row.id}`, { params: { requester_username: session.username } })
    ElMessage.success('删除账号成功')
    await fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除失败')
    }
  }
}

const deleteBySelection = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先勾选要删除的账号')
    return
  }

  try {
    await ElMessageBox.confirm(`确认删除已勾选的 ${selectedRows.value.length} 个账号吗？`, '提示', {
      type: 'warning'
    })

    for (const row of selectedRows.value) {
      await http.delete(`/api/v1/users/${row.id}`, { params: { requester_username: session.username } })
    }

    selectedRows.value = []
    ElMessage.success('批量删除账号成功')
    await fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '批量删除失败')
    }
  }
}

onMounted(async () => {
  await fetchPermissionOptions()
  if (isAdmin.value) {
    await fetchUsers()
  } else {
    await fetchMe()
  }
})
</script>

<style scoped>
.perm-card {
  border-radius: 12px;
}

.query-form {
  margin-bottom: 10px;
}

.query-form :deep(.el-input) {
  width: 180px;
}

.toolbar {
  display: flex;
  gap: 10px;
  margin: 6px 0 14px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.perm-tag {
  margin: 0 6px 6px 0;
}

.perm-checks {
  display: grid;
  grid-template-columns: repeat(2, minmax(160px, 1fr));
  gap: 10px;
}

.full-input {
  width: 100%;
}

.my-perms {
  margin-top: 20px;
}

.my-perms-title {
  margin-bottom: 10px;
  color: #334155;
  font-weight: 600;
}
</style>
