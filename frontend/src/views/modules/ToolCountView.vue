<template>
  <div class="tool-count-page">
    <el-card shadow="never" class="count-card">
      <template #header>工具计数（YOLO）</template>

      <el-alert
        title="当前模型尚未训练完成，识别结果为占位返回。训练完成后只需替换后端推理逻辑。"
        type="info"
        :closable="false"
        show-icon
      />

      <div class="upload-area">
        <el-upload
          class="image-uploader"
          drag
          :show-file-list="false"
          :auto-upload="false"
          :before-upload="beforeUpload"
          accept="image/png,image/jpg,image/jpeg"
        >
          <img v-if="previewUrl" :src="previewUrl" class="preview-image" alt="preview" />
          <template v-else>
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">拖拽图片到此处，或 <em>点击上传</em></div>
            <div class="el-upload__tip">支持 png/jpg/jpeg，大小不超过 10MB</div>
          </template>
        </el-upload>

        <div class="actions">
          <el-button type="primary" :disabled="!imageFile || loading" :loading="loading" @click="runDetection">
            调用 YOLO 识别
          </el-button>
          <el-button @click="clearImage">清空图片</el-button>
        </div>
      </div>

      <el-card class="result-card" shadow="never">
        <template #header>识别结果</template>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="模型状态">{{ result.ready ? '已就绪' : '未就绪' }}</el-descriptions-item>
          <el-descriptions-item label="提示信息">{{ result.message || '请上传图片并执行识别' }}</el-descriptions-item>
          <el-descriptions-item label="检测总数">{{ result.total_count }}</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { http } from '../../api/http'

const imageFile = ref(null)
const previewUrl = ref('')
const loading = ref(false)

const result = reactive({
  ready: false,
  message: '',
  total_count: 0,
  detections: []
})

const beforeUpload = (file) => {
  const isAllowed = ['image/png', 'image/jpg', 'image/jpeg'].includes(file.type)
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isAllowed) {
    ElMessage.error('仅支持 png/jpg/jpeg 格式')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB')
    return false
  }

  imageFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  return false
}

const clearImage = () => {
  imageFile.value = null
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewUrl.value = ''
  result.ready = false
  result.message = ''
  result.total_count = 0
  result.detections = []
}

const runDetection = async () => {
  if (!imageFile.value) {
    ElMessage.warning('请先上传图片')
    return
  }

  loading.value = true
  try {
    const formData = new FormData()
    formData.append('image', imageFile.value)

    const { data } = await http.post('/api/v1/tool-count/detect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    result.ready = !!data.ready
    result.message = data.message || ''
    result.total_count = data.total_count || 0
    result.detections = data.detections || []

    if (!data.ready) {
      ElMessage.info(data.message || '模型暂未就绪')
    } else {
      ElMessage.success('识别完成')
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '识别请求失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.count-card {
  border-radius: 12px;
}

.upload-area {
  margin-top: 16px;
}

.image-uploader {
  width: 100%;
}

.image-uploader :deep(.el-upload-dragger) {
  width: 100%;
  min-height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 260px;
  object-fit: contain;
}

.actions {
  margin-top: 14px;
  display: flex;
  gap: 10px;
}

.result-card {
  margin-top: 18px;
}
</style>
