<template>
  <div class="settings-page">
    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="密码策略" name="password">
        <el-form label-width="180px" class="settings-form">
          <el-form-item label="最小密码长度">
            <el-input-number v-model="passwordPolicy.min_length" :min="6" :max="32" />
          </el-form-item>
          <el-form-item label="会话超时（分钟）">
            <el-input-number v-model="passwordPolicy.session_timeout_minutes" :min="10" :max="1440" />
          </el-form-item>
          <el-form-item label="最大登录失败次数">
            <el-input-number v-model="passwordPolicy.max_login_retries" :min="3" :max="20" />
          </el-form-item>
          <el-form-item label="复杂度要求">
            <el-checkbox v-model="passwordPolicy.require_uppercase">包含大写字母</el-checkbox>
            <el-checkbox v-model="passwordPolicy.require_lowercase">包含小写字母</el-checkbox>
            <el-checkbox v-model="passwordPolicy.require_number">包含数字</el-checkbox>
            <el-checkbox v-model="passwordPolicy.require_special">包含特殊字符</el-checkbox>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :disabled="!isAdmin" @click="savePasswordPolicy">保存密码策略</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="告警阈值" name="alert">
        <el-form label-width="180px" class="settings-form">
          <el-form-item label="低库存告警阈值">
            <el-input-number v-model="alertThreshold.low_stock_threshold" :min="0" :max="999" />
          </el-form-item>
          <el-form-item label="识别置信度阈值">
            <el-slider
              v-model="alertThreshold.detection_confidence_threshold"
              :min="0.5"
              :max="0.99"
              :step="0.01"
              show-input
            />
          </el-form-item>
          <el-form-item label="告警去重时间（秒）">
            <el-input-number v-model="alertThreshold.alert_dedup_seconds" :min="10" :max="3600" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :disabled="!isAdmin" @click="saveAlertThreshold">保存告警阈值</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="工具类型字典" name="toolType">
        <div class="toolbar">
          <el-button type="primary" plain :disabled="!isAdmin" @click="openCreateTypeDialog">新增类型</el-button>
        </div>
        <el-table :data="toolTypes" border>
          <el-table-column prop="name" label="类型名称" min-width="140" />
          <el-table-column prop="description" label="描述" min-width="180" />
          <el-table-column prop="sort_order" label="排序" width="90" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '启用' : '停用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :disabled="!isAdmin" @click="openEditTypeDialog(row)">编辑</el-button>
              <el-button link type="danger" :disabled="!isAdmin" @click="deleteType(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="操作日志" name="logs">
        <el-empty v-if="!isAdmin" description="仅管理员可查看操作日志" />
        <template v-else>
          <el-form :model="logQuery" inline class="query-form">
            <el-form-item label="模块">
              <el-input v-model="logQuery.module" placeholder="如 系统设置" clearable />
            </el-form-item>
            <el-form-item label="动作">
              <el-input v-model="logQuery.action" placeholder="如 新增用户" clearable />
            </el-form-item>
            <el-form-item label="操作人">
              <el-input v-model="logQuery.actor" placeholder="如 admin" clearable />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="searchLogs">搜索</el-button>
              <el-button @click="resetLogs">重置</el-button>
            </el-form-item>
          </el-form>

          <el-table :data="operationLogs" border :loading="logLoading">
            <el-table-column prop="timestamp" label="时间" min-width="180" />
            <el-table-column prop="module" label="模块" min-width="100" />
            <el-table-column prop="action" label="动作" min-width="120" />
            <el-table-column prop="actor" label="操作人" min-width="100" />
            <el-table-column prop="target" label="目标" min-width="120" />
            <el-table-column label="详情" min-width="220">
              <template #default="{ row }">
                <span class="json-text">{{ JSON.stringify(row.detail_json || {}) }}</span>
              </template>
            </el-table-column>
          </el-table>

          <div class="pager">
            <el-pagination
              v-model:current-page="logPager.current"
              v-model:page-size="logPager.pageSize"
              :page-sizes="[10, 20, 50]"
              background
              layout="total, sizes, prev, pager, next"
              :total="logPager.total"
              @current-change="fetchOperationLogs"
              @size-change="onLogPageSizeChange"
            />
          </div>
        </template>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="typeDialog.visible" :title="typeDialog.mode === 'create' ? '新增工具类型' : '编辑工具类型'" width="560px">
      <el-form ref="typeFormRef" :model="typeForm" :rules="typeRules" label-width="90px">
        <el-form-item label="类型名称" prop="name">
          <el-input v-model="typeForm.name" placeholder="请输入类型名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="typeForm.description" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="typeForm.sort_order" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="typeForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="typeDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitTypeForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { http } from '../../api/http'
import { getSession } from '../../auth/session'

const session = getSession()
const isAdmin = computed(() => session?.roleKey === 'admin' || session?.username === 'admin')

const activeTab = ref('password')

const passwordPolicy = reactive({
  min_length: 8,
  require_uppercase: true,
  require_lowercase: true,
  require_number: true,
  require_special: false,
  session_timeout_minutes: 120,
  max_login_retries: 5
})

const alertThreshold = reactive({
  low_stock_threshold: 5,
  detection_confidence_threshold: 0.8,
  alert_dedup_seconds: 60
})

const toolTypes = ref([])
const typeDialog = reactive({ visible: false, mode: 'create' })
const typeFormRef = ref(null)
const typeForm = reactive({ id: null, name: '', description: '', sort_order: 100, enabled: true })
const typeRules = {
  name: [{ required: true, message: '请输入类型名称', trigger: 'blur' }]
}

const operationLogs = ref([])
const logLoading = ref(false)
const logQuery = reactive({ module: '', action: '', actor: '' })
const logPager = reactive({ current: 1, pageSize: 10, total: 0 })

const fetchPasswordPolicy = async () => {
  const { data } = await http.get('/api/v1/settings/password-policy')
  Object.assign(passwordPolicy, data.setting_value || {})
}

const fetchAlertThreshold = async () => {
  const { data } = await http.get('/api/v1/settings/alert-threshold')
  Object.assign(alertThreshold, data.setting_value || {})
}

const fetchToolTypes = async () => {
  const { data } = await http.get('/api/v1/settings/tool-types', { params: { include_disabled: true } })
  toolTypes.value = data.items || []
}

const fetchOperationLogs = async () => {
  if (!isAdmin.value) return
  logLoading.value = true
  try {
    const { data } = await http.get('/api/v1/settings/operation-logs', {
      params: {
        requester_username: session.username,
        module: logQuery.module,
        action: logQuery.action,
        actor: logQuery.actor,
        page: logPager.current,
        page_size: logPager.pageSize
      }
    })
    operationLogs.value = data.items || []
    logPager.total = data.total || 0
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载操作日志失败')
  } finally {
    logLoading.value = false
  }
}

const savePasswordPolicy = async () => {
  if (!isAdmin.value) return
  try {
    await http.put('/api/v1/settings/password-policy', { ...passwordPolicy }, { params: { requester_username: session.username } })
    ElMessage.success('密码策略已保存')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存失败')
  }
}

const saveAlertThreshold = async () => {
  if (!isAdmin.value) return
  try {
    await http.put('/api/v1/settings/alert-threshold', { ...alertThreshold }, { params: { requester_username: session.username } })
    ElMessage.success('告警阈值已保存')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存失败')
  }
}

const resetTypeForm = () => {
  typeForm.id = null
  typeForm.name = ''
  typeForm.description = ''
  typeForm.sort_order = 100
  typeForm.enabled = true
}

const openCreateTypeDialog = () => {
  resetTypeForm()
  typeDialog.mode = 'create'
  typeDialog.visible = true
}

const openEditTypeDialog = (row) => {
  typeDialog.mode = 'edit'
  typeDialog.visible = true
  typeForm.id = row.id
  typeForm.name = row.name
  typeForm.description = row.description
  typeForm.sort_order = row.sort_order
  typeForm.enabled = row.enabled
}

const submitTypeForm = async () => {
  if (!typeFormRef.value) return
  const valid = await typeFormRef.value.validate().catch(() => false)
  if (!valid) return

  const payload = {
    name: typeForm.name,
    description: typeForm.description,
    sort_order: typeForm.sort_order,
    enabled: typeForm.enabled
  }

  try {
    if (typeDialog.mode === 'create') {
      await http.post('/api/v1/settings/tool-types', payload, { params: { requester_username: session.username } })
      ElMessage.success('工具类型新增成功')
    } else {
      await http.put(`/api/v1/settings/tool-types/${typeForm.id}`, payload, {
        params: { requester_username: session.username }
      })
      ElMessage.success('工具类型修改成功')
    }
    typeDialog.visible = false
    await fetchToolTypes()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存失败')
  }
}

const deleteType = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除工具类型 ${row.name} 吗？`, '提示', { type: 'warning' })
    await http.delete(`/api/v1/settings/tool-types/${row.id}`, { params: { requester_username: session.username } })
    ElMessage.success('删除成功')
    await fetchToolTypes()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除失败')
    }
  }
}

const searchLogs = async () => {
  logPager.current = 1
  await fetchOperationLogs()
}

const resetLogs = async () => {
  logQuery.module = ''
  logQuery.action = ''
  logQuery.actor = ''
  logPager.current = 1
  await fetchOperationLogs()
}

const onLogPageSizeChange = async () => {
  logPager.current = 1
  await fetchOperationLogs()
}

onMounted(async () => {
  await Promise.all([fetchPasswordPolicy(), fetchAlertThreshold(), fetchToolTypes()])
  await fetchOperationLogs()
})
</script>

<style scoped>
.settings-form {
  max-width: 760px;
  padding: 8px 8px 0;
}

.toolbar {
  margin-bottom: 12px;
}

.query-form {
  margin-bottom: 12px;
}

.query-form :deep(.el-input) {
  width: 180px;
}

.pager {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

.json-text {
  color: #64748b;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
}
</style>
