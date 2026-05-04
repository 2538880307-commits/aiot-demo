<template>
  <div class="tool-page">
    <el-card shadow="never" class="tool-card">
      <el-form :model="query" inline class="query-form">
        <el-form-item label="工具编码">
          <el-input v-model="query.toolCode" placeholder="请输入工具编码" clearable />
        </el-form-item>
        <el-form-item label="工具类型">
          <el-select v-model="query.toolType" placeholder="请选择工具类型" clearable>
            <el-option v-for="item in typeOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="工具名称">
          <el-input v-model="query.toolName" placeholder="请输入工具名称" clearable />
        </el-form-item>
        <el-form-item label="库存">
          <el-input v-model="query.stock" placeholder="请输入库存" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <div class="toolbar">
        <el-button type="primary" plain @click="openCreateDialog">新增</el-button>
        <el-button type="success" plain @click="openEditBySelection">修改</el-button>
        <el-button type="danger" plain @click="deleteBySelection">删除</el-button>
        <el-button type="warning" plain @click="exportCsv">导出</el-button>
      </div>

      <el-table :data="tools" border :loading="loading" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="48" />
        <el-table-column prop="tool_code" label="工具编码" min-width="110" />
        <el-table-column prop="tool_type" label="工具类型" min-width="120" />
        <el-table-column prop="tool_name" label="工具名称" min-width="170" />
        <el-table-column prop="stock" label="库存" width="90" />
        <el-table-column prop="team" label="维护组" min-width="120" />
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDialog(row)">修改</el-button>
            <el-button link type="danger" @click="deleteOne(row)">删除</el-button>
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
          @current-change="fetchTools"
          @size-change="onPageSizeChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialog.visible"
      :title="dialog.mode === 'create' ? '添加工具管理' : '修改工具管理'"
      width="720px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px" class="edit-form">
        <el-form-item label="工具编码" prop="toolCode">
          <el-input v-model="form.toolCode" placeholder="请输入工具编码" />
        </el-form-item>
        <el-form-item label="工具类型" prop="toolType">
          <el-select v-model="form.toolType" placeholder="请选择工具类型" class="full-input">
            <el-option v-for="item in typeOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="工具名称" prop="toolName">
          <el-input v-model="form.toolName" placeholder="请输入工具名称" />
        </el-form-item>

        <el-form-item label="图片">
          <div class="upload-wrap">
            <el-upload
              class="tool-uploader"
              :show-file-list="false"
              :auto-upload="false"
              :before-upload="beforeImageUpload"
              accept="image/png,image/jpg,image/jpeg"
            >
              <img v-if="form.imageUrl" :src="form.imageUrl" class="preview-image" alt="tool" />
              <el-icon v-else class="uploader-plus"><Plus /></el-icon>
            </el-upload>
            <div class="upload-tip">请上传大小不超过 5MB，格式为 png/jpg/jpeg 的文件</div>
          </div>
        </el-form-item>

        <el-form-item label="库存" prop="stock">
          <el-input-number v-model="form.stock" :min="0" :max="99999" class="full-input" />
        </el-form-item>
        <el-form-item label="维护组" prop="team">
          <el-input v-model="form.team" placeholder="请输入维护组" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { http } from '../../api/http'
import { getSession } from '../../auth/session'

const typeOptions = ref([])
const session = getSession()

const query = reactive({
  toolCode: '',
  toolType: '',
  toolName: '',
  stock: ''
})

const tools = ref([])
const loading = ref(false)

const pager = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

const selectedRows = ref([])

const dialog = reactive({
  visible: false,
  mode: 'create'
})

const formRef = ref(null)
const form = reactive({
  id: null,
  toolCode: '',
  toolType: '',
  toolName: '',
  stock: 0,
  team: '',
  imageUrl: ''
})

const rules = {
  toolCode: [{ required: true, message: '请输入工具编码', trigger: 'blur' }],
  toolType: [{ required: true, message: '请选择工具类型', trigger: 'change' }],
  toolName: [{ required: true, message: '请输入工具名称', trigger: 'blur' }],
  stock: [{ required: true, message: '请输入库存', trigger: 'change' }],
  team: [{ required: true, message: '请输入维护组', trigger: 'blur' }]
}

const fetchTypeOptions = async () => {
  try {
    const { data } = await http.get('/api/v1/settings/tool-types/options')
    typeOptions.value = data.items || []
  } catch {
    typeOptions.value = ['电动工具', '手动工具', '测量工具', '安全设备']
  }
}

const fetchTools = async () => {
  loading.value = true
  try {
    const { data } = await http.get('/api/v1/tools', {
      params: {
        requester_username: session?.username || '',
        tool_code: query.toolCode,
        tool_type: query.toolType,
        tool_name: query.toolName,
        stock: query.stock,
        page: pager.current,
        page_size: pager.pageSize
      }
    })

    tools.value = data.items || []
    pager.total = data.total || 0
  } catch {
    ElMessage.error('加载工具列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  pager.current = 1
  await fetchTools()
}

const handleReset = async () => {
  query.toolCode = ''
  query.toolType = ''
  query.toolName = ''
  query.stock = ''
  pager.current = 1
  await fetchTools()
}

const onPageSizeChange = async () => {
  pager.current = 1
  await fetchTools()
}

const onSelectionChange = (rows) => {
  selectedRows.value = rows
}

const resetForm = () => {
  form.id = null
  form.toolCode = ''
  form.toolType = ''
  form.toolName = ''
  form.stock = 0
  form.team = ''
  form.imageUrl = ''
}

const openCreateDialog = () => {
  dialog.mode = 'create'
  dialog.visible = true
  resetForm()
}

const openEditDialog = (row) => {
  dialog.mode = 'edit'
  dialog.visible = true
  form.id = row.id
  form.toolCode = row.tool_code
  form.toolType = row.tool_type
  form.toolName = row.tool_name
  form.stock = row.stock
  form.team = row.team
  form.imageUrl = row.image_url || ''
}

const openEditBySelection = () => {
  if (selectedRows.value.length !== 1) {
    ElMessage.warning('请先勾选且仅勾选一条数据进行修改')
    return
  }
  openEditDialog(selectedRows.value[0])
}

const submitForm = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  const payload = {
    tool_code: form.toolCode,
    tool_type: form.toolType,
    tool_name: form.toolName,
    stock: form.stock,
    team: form.team,
    image_url: form.imageUrl || ''
  }

  try {
    if (dialog.mode === 'create') {
      await http.post('/api/v1/tools', payload, { params: { requester_username: session?.username || '' } })
      ElMessage.success('新增成功')
    } else {
      await http.put(`/api/v1/tools/${form.id}`, payload, { params: { requester_username: session?.username || '' } })
      ElMessage.success('修改成功')
    }

    dialog.visible = false
    await fetchTools()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '保存失败')
  }
}

const deleteOne = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除工具 ${row.tool_code} 吗？`, '提示', { type: 'warning' })
    await http.delete(`/api/v1/tools/${row.id}`, { params: { requester_username: session?.username || '' } })
    ElMessage.success('删除成功')
    await fetchTools()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除失败')
    }
  }
}

const deleteBySelection = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先勾选需要删除的记录')
    return
  }

  try {
    await ElMessageBox.confirm(`确认删除已勾选的 ${selectedRows.value.length} 条记录吗？`, '提示', {
      type: 'warning'
    })
    await http.post('/api/v1/tools/batch-delete', {
      ids: selectedRows.value.map((item) => item.id)
    }, { params: { requester_username: session?.username || '' } })
    selectedRows.value = []
    ElMessage.success('批量删除成功')
    await fetchTools()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '批量删除失败')
    }
  }
}

const exportCsv = async () => {
  try {
    let exportItems = []

    if (selectedRows.value.length > 0) {
      exportItems = selectedRows.value
    } else {
      if (!session?.username) {
        throw new Error('登录状态已失效，请重新登录后再导出')
      }
      const pageSize = 100
      let page = 1
      let total = 0

      do {
        const { data } = await http.get('/api/v1/tools', {
          params: {
            requester_username: session?.username || '',
            tool_code: query.toolCode,
            tool_type: query.toolType,
            tool_name: query.toolName,
            stock: query.stock,
            page,
            page_size: pageSize
          }
        })

        const items = data.items || []
        total = Number(data.total || 0)
        exportItems.push(...items)
        page += 1
      } while (exportItems.length < total)
    }

    const headers = ['工具编码', '工具类型', '工具名称', '库存', '维护组']
    const rows = exportItems.map((item) => [
      item.tool_code ?? '',
      item.tool_type ?? '',
      item.tool_name ?? '',
      String(item.stock ?? ''),
      item.team ?? ''
    ])

    const csv = [headers, ...rows]
      .map((line) => line.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      .join('\n')

    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' })
    const link = document.createElement('a')
    const objectUrl = URL.createObjectURL(blob)
    link.href = objectUrl
    link.download = `工具管理_${new Date().toISOString().slice(0, 10)}.csv`
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
    ElMessage.success(selectedRows.value.length > 0 ? '导出勾选数据成功' : '导出成功')
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '导出失败'
    ElMessage.error(message)
    // 便于本地调试浏览器控制台定位问题
    // eslint-disable-next-line no-console
    console.error('exportCsv failed:', error)
  }
}

const beforeImageUpload = async (rawFile) => {
  const isValidType = ['image/png', 'image/jpg', 'image/jpeg'].includes(rawFile.type)
  const isLt5M = rawFile.size / 1024 / 1024 < 5

  if (!isValidType) {
    ElMessage.error('仅支持 png/jpg/jpeg 格式')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }

  form.imageUrl = await new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.readAsDataURL(rawFile)
  })
  return false
}

onMounted(async () => {
  await fetchTypeOptions()
  await fetchTools()
})
</script>

<style scoped>
.tool-page {
  display: block;
}

.tool-card {
  border-radius: 12px;
}

.query-form {
  margin-bottom: 10px;
}

.query-form :deep(.el-input),
.query-form :deep(.el-select) {
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

.full-input {
  width: 100%;
}

.upload-wrap {
  display: flex;
  flex-direction: column;
}

.tool-uploader {
  width: 190px;
  height: 190px;
  border: 1px dashed #d6dce6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.uploader-plus {
  font-size: 44px;
  color: #9aa6b2;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-tip {
  margin-top: 10px;
  color: #7b8795;
  font-size: 13px;
}

@media (max-width: 1200px) {
  .query-form {
    display: grid;
    grid-template-columns: repeat(2, minmax(220px, 1fr));
    gap: 4px 8px;
  }

  .query-form :deep(.el-form-item) {
    margin-right: 0;
  }
}

@media (max-width: 768px) {
  .toolbar {
    flex-wrap: wrap;
  }

  .pager {
    justify-content: center;
  }
}
</style>
