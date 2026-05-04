<template>
  <div class="tool-count-page">
    <el-card shadow="never" class="count-card">
      <template #header>工具识别（检修前后对比）</template>

      <el-alert
        title="功能用途：对比检修前后两张照片中的工具数量，判断是否出现工具缺失。"
        type="info"
        :closable="false"
        show-icon
      />

      <div class="compare-grid">
        <el-card shadow="never" class="panel-card">
          <template #header>检修前拍照记录</template>
          <el-upload
            class="image-uploader"
            drag
            :show-file-list="false"
            :auto-upload="false"
            :on-change="(uploadFile) => handleUploadChange(uploadFile, 'before')"
            accept="image/png,image/jpg,image/jpeg"
          >
            <img v-if="beforeImage.url" :src="beforeImage.url" class="preview-image" alt="before" />
            <template v-else>
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">上传检修前图片</div>
              <div class="el-upload__tip">支持 png/jpg/jpeg，大小不超过 10MB</div>
            </template>
          </el-upload>

          <div class="actions">
            <el-button type="primary" :disabled="!beforeImage.file || loading.before" :loading="loading.before" @click="runDetection('before')">
              识别检修前图片
            </el-button>
            <el-button @click="clearImage('before')">清空</el-button>
          </div>

          <el-descriptions :column="1" border class="result-box">
            <el-descriptions-item label="模型状态">{{ beforeResult.ready ? '已就绪' : '未就绪' }}</el-descriptions-item>
            <el-descriptions-item label="识别结果">{{ beforeResult.total_count }}</el-descriptions-item>
            <el-descriptions-item label="提示信息">{{ beforeResult.message || '尚未识别' }}</el-descriptions-item>
          </el-descriptions>

          <div class="class-box">
            <div class="class-title">分类统计（检修前）</div>
            <el-empty v-if="!beforeClassRows.length" description="暂无分类数据" :image-size="60" />
            <el-table v-else :data="beforeClassRows" border size="small">
              <el-table-column prop="label" label="工具类型" min-width="120">
                <template #default="{ row }">
                  <span :class="{ 'diff-red': row.diff !== 0 }">{{ row.label }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="数量" width="90" align="center">
                <template #default="{ row }">
                  <span :class="{ 'diff-red': row.diff !== 0 }">{{ row.count }}</span>
                </template>
              </el-table-column>
              <el-table-column label="对比" min-width="120">
                <template #default="{ row }">
                  <span v-if="row.diff > 0" class="diff-red">检修后少 {{ row.diff }}</span>
                  <span v-else-if="row.diff < 0" class="diff-red">检修后多 {{ Math.abs(row.diff) }}</span>
                  <span v-else>一致</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>

        <el-card shadow="never" class="panel-card">
          <template #header>检修后拍照记录</template>
          <el-upload
            class="image-uploader"
            drag
            :show-file-list="false"
            :auto-upload="false"
            :on-change="(uploadFile) => handleUploadChange(uploadFile, 'after')"
            accept="image/png,image/jpg,image/jpeg"
          >
            <img v-if="afterImage.url" :src="afterImage.url" class="preview-image" alt="after" />
            <template v-else>
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">上传检修后图片</div>
              <div class="el-upload__tip">支持 png/jpg/jpeg，大小不超过 10MB</div>
            </template>
          </el-upload>

          <div class="actions">
            <el-button type="primary" :disabled="!afterImage.file || loading.after" :loading="loading.after" @click="runDetection('after')">
              识别检修后图片
            </el-button>
            <el-button @click="clearImage('after')">清空</el-button>
          </div>

          <el-descriptions :column="1" border class="result-box">
            <el-descriptions-item label="模型状态">{{ afterResult.ready ? '已就绪' : '未就绪' }}</el-descriptions-item>
            <el-descriptions-item label="识别结果">{{ afterResult.total_count }}</el-descriptions-item>
            <el-descriptions-item label="提示信息">{{ afterResult.message || '尚未识别' }}</el-descriptions-item>
          </el-descriptions>

          <div class="class-box">
            <div class="class-title">分类统计（检修后）</div>
            <el-empty v-if="!afterClassRows.length" description="暂无分类数据" :image-size="60" />
            <el-table v-else :data="afterClassRows" border size="small">
              <el-table-column prop="label" label="工具类型" min-width="120">
                <template #default="{ row }">
                  <span :class="{ 'diff-red': row.diff !== 0 }">{{ row.label }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="数量" width="90" align="center">
                <template #default="{ row }">
                  <span :class="{ 'diff-red': row.diff !== 0 }">{{ row.count }}</span>
                </template>
              </el-table-column>
              <el-table-column label="对比" min-width="120">
                <template #default="{ row }">
                  <span v-if="row.diff > 0" class="diff-red">检修后少 {{ row.diff }}</span>
                  <span v-else-if="row.diff < 0" class="diff-red">检修后多 {{ Math.abs(row.diff) }}</span>
                  <span v-else>一致</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </div>

      <el-card shadow="never" class="summary-card">
        <template #header>前后对比结论</template>

        <div class="summary-row">
          <div class="summary-item">检修前工具数量：<strong>{{ beforeResult.total_count }}</strong></div>
          <div class="summary-item">检修后工具数量：<strong>{{ afterResult.total_count }}</strong></div>
        </div>

        <el-alert :title="comparison.title" :description="comparison.desc" :type="comparison.type" :closable="false" show-icon />

        <div class="summary-actions">
          <el-button
            type="success"
            :disabled="!beforeImage.file || !afterImage.file || loading.before || loading.after"
            :loading="loading.before || loading.after"
            @click="runBothDetection"
          >
            一键识别并比较
          </el-button>
        </div>
      </el-card>

      <el-card shadow="never" class="summary-card">
        <template #header>分类差异明细（红色为异常）</template>
        <el-empty v-if="!diffRows.length" description="请先完成前后两张图片识别" :image-size="60" />
        <el-table v-else :data="diffRows" border>
          <el-table-column prop="label" label="工具类型" min-width="140" />
          <el-table-column prop="before" label="检修前" width="110" align="center" />
          <el-table-column prop="after" label="检修后" width="110" align="center" />
          <el-table-column label="变化" min-width="180">
            <template #default="{ row }">
              <span v-if="row.delta > 0" class="diff-red">缺失 {{ row.delta }}（检修后更少）</span>
              <span v-else-if="row.delta < 0" class="diff-red">新增 {{ Math.abs(row.delta) }}（检修后更多）</span>
              <span>一致</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card v-if="isAdmin" shadow="never" class="log-card">
        <template #header>工具识别日志（最近 20 条）</template>
        <el-table :data="recognitionLogs" border :loading="logLoading">
          <el-table-column prop="timestamp" label="时间" min-width="180" />
          <el-table-column prop="action" label="动作" width="110" />
          <el-table-column prop="actor" label="操作人" width="100" />
          <el-table-column prop="target" label="图片" min-width="160" />
          <el-table-column label="详情" min-width="260">
            <template #default="{ row }">
              <span class="json-text">{{ JSON.stringify(row.detail_json || {}) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { http } from '../../api/http'
import { getSession } from '../../auth/session'

const session = getSession()
const isAdmin = computed(() => session?.roleKey === 'admin' || session?.username === 'admin')

const beforeImage = reactive({ file: null, url: '' })
const afterImage = reactive({ file: null, url: '' })

const loading = reactive({ before: false, after: false })
const recognitionLogs = ref([])
const logLoading = ref(false)

const beforeResult = reactive({
  ready: false,
  message: '',
  total_count: 0,
  by_class: {},
  detections: []
})

const afterResult = reactive({
  ready: false,
  message: '',
  total_count: 0,
  by_class: {},
  detections: []
})

const beforeMap = computed(() => beforeResult.by_class || {})
const afterMap = computed(() => afterResult.by_class || {})

const allLabels = computed(() => {
  const set = new Set([...Object.keys(beforeMap.value), ...Object.keys(afterMap.value)])
  return Array.from(set)
})

const diffRows = computed(() => {
  if (!allLabels.value.length) return []
  return allLabels.value
    .map((label) => {
      const before = Number(beforeMap.value[label] || 0)
      const after = Number(afterMap.value[label] || 0)
      return { label, before, after, delta: before - after }
    })
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
})

const beforeClassRows = computed(() => {
  return Object.entries(beforeMap.value).map(([label, count]) => {
    const diff = Number(count) - Number(afterMap.value[label] || 0)
    return { label, count, diff }
  })
})

const afterClassRows = computed(() => {
  return Object.entries(afterMap.value).map(([label, count]) => {
    const diff = Number(beforeMap.value[label] || 0) - Number(count)
    return { label, count, diff }
  })
})

const comparison = computed(() => {
  const beforeDetected = beforeImage.file && (beforeResult.message || beforeResult.total_count >= 0)
  const afterDetected = afterImage.file && (afterResult.message || afterResult.total_count >= 0)

  if (!beforeDetected || !afterDetected) {
    return {
      type: 'info',
      title: '请先完成检修前和检修后图片识别',
      desc: '两侧都识别完成后，系统将自动判断是否缺失工具。'
    }
  }

  const diff = beforeResult.total_count - afterResult.total_count
  if (diff > 0) {
    return {
      type: 'error',
      title: `发现工具缺失：少 ${diff} 件`,
      desc: '检修后识别数量少于检修前，请立即复核并确认工具去向。'
    }
  }
  if (diff === 0) {
    return {
      type: 'success',
      title: '工具数量一致，未发现缺失',
      desc: '检修前后识别数量相同。'
    }
  }
  return {
    type: 'warning',
    title: `检修后数量多出 ${Math.abs(diff)} 件`,
    desc: '请确认是否新增了工具或识别产生误差。'
  }
})

const handleUploadChange = (uploadFile, phase) => {
  const file = uploadFile?.raw || uploadFile
  if (!file) return

  const isAllowed = ['image/png', 'image/jpg', 'image/jpeg'].includes(file.type)
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isAllowed) {
    ElMessage.error('仅支持 png/jpg/jpeg 格式')
    return
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB')
    return
  }

  const target = phase === 'before' ? beforeImage : afterImage
  if (target.url) URL.revokeObjectURL(target.url)
  target.file = file
  target.url = URL.createObjectURL(file)

  const targetResult = phase === 'before' ? beforeResult : afterResult
  targetResult.ready = false
  targetResult.message = ''
  targetResult.total_count = 0
  targetResult.by_class = {}
  targetResult.detections = []

  ElMessage.success(phase === 'before' ? '已选择检修前图片' : '已选择检修后图片')
}

const clearImage = (phase) => {
  const target = phase === 'before' ? beforeImage : afterImage
  const targetResult = phase === 'before' ? beforeResult : afterResult

  if (target.url) URL.revokeObjectURL(target.url)
  target.file = null
  target.url = ''

  targetResult.ready = false
  targetResult.message = ''
  targetResult.total_count = 0
  targetResult.by_class = {}
  targetResult.detections = []
}

const fetchRecognitionLogs = async () => {
  if (!isAdmin.value) return
  logLoading.value = true
  try {
    const { data } = await http.get('/api/v1/settings/operation-logs', {
      params: {
        requester_username: session.username,
        module: '工具识别',
        page: 1,
        page_size: 20
      }
    })
    recognitionLogs.value = (data.items || []).map((item) => ({
      ...item,
      timestamp: formatShanghaiTime(item.timestamp)
    }))
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '加载工具识别日志失败')
  } finally {
    logLoading.value = false
  }
}

const formatShanghaiTime = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).format(date)
}

const runDetection = async (phase) => {
  const target = phase === 'before' ? beforeImage : afterImage
  const targetResult = phase === 'before' ? beforeResult : afterResult
  const loadingKey = phase === 'before' ? 'before' : 'after'

  if (!target.file) {
    ElMessage.warning(phase === 'before' ? '请先上传检修前图片' : '请先上传检修后图片')
    return
  }

  loading[loadingKey] = true
  try {
    const formData = new FormData()
    formData.append('image', target.file)

    const { data } = await http.post('/api/v1/tool-count/detect', formData, {
      params: { requester_username: session?.username || 'system' },
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    targetResult.ready = !!data.ready
    targetResult.message = data.message || ''
    targetResult.total_count = data.total_count || 0
    targetResult.by_class = data.by_class || {}
    targetResult.detections = data.detections || []

    if (!data.ready) {
      ElMessage.info(data.message || '模型暂未就绪')
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '识别请求失败')
  } finally {
    loading[loadingKey] = false
    if (isAdmin.value) {
      await fetchRecognitionLogs()
    }
  }
}

const runBothDetection = async () => {
  await runDetection('before')
  await runDetection('after')
}

onMounted(async () => {
  if (isAdmin.value) {
    await fetchRecognitionLogs()
  }
})
</script>

<style scoped>
.count-card {
  border-radius: 12px;
}

.compare-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(2, minmax(280px, 1fr));
  gap: 14px;
}

.panel-card {
  border-radius: 10px;
}

.image-uploader {
  width: 100%;
}

.image-uploader :deep(.el-upload-dragger) {
  width: 100%;
  min-height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
}

.actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.result-box {
  margin-top: 12px;
}

.class-box {
  margin-top: 12px;
}

.class-title {
  margin-bottom: 8px;
  color: #334155;
  font-weight: 600;
}

.summary-card {
  margin-top: 14px;
}

.summary-row {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
  color: #334155;
}

.summary-item strong {
  color: #111827;
}

.summary-actions {
  margin-top: 12px;
}

.log-card {
  margin-top: 14px;
}

.diff-red {
  color: #dc2626;
  font-weight: 600;
}

@media (max-width: 1000px) {
  .compare-grid {
    grid-template-columns: 1fr;
  }

  .summary-row {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
