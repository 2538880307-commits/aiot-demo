<template>
  <div class="page">
    <header class="header">
      <h1>轨道交通 AIoT 工具监测平台</h1>
      <el-tag :type="healthTagType">后端状态: {{ healthStatus }}</el-tag>
    </header>

    <section class="cards">
      <el-card>
        <div class="stat-title">总检测次数</div>
        <div class="stat-value">{{ stats.total_detections }}</div>
      </el-card>
      <el-card>
        <div class="stat-title">活跃告警</div>
        <div class="stat-value danger">{{ stats.active_alerts }}</div>
      </el-card>
      <el-card>
        <div class="stat-title">在线站点</div>
        <div class="stat-value">{{ stats.sites_online }}</div>
      </el-card>
    </section>

    <section class="panel">
      <el-card>
        <template #header>实时告警日志</template>
        <el-empty v-if="alerts.length === 0" description="暂无告警" />
        <ul v-else class="log-list">
          <li v-for="(item, idx) in alerts" :key="idx">{{ item }}</li>
        </ul>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { http } from '../api/http'

const healthStatus = ref('unknown')
const stats = ref({
  total_detections: 0,
  active_alerts: 0,
  sites_online: 0
})
const alerts = ref([])

const healthTagType = computed(() => (healthStatus.value === 'ok' ? 'success' : 'danger'))

const loadHealth = async () => {
  try {
    const { data } = await http.get('/health')
    healthStatus.value = data.status
  } catch {
    healthStatus.value = 'down'
  }
}

const loadStats = async () => {
  try {
    const { data } = await http.get('/api/v1/stats')
    stats.value = data
  } catch {
    // keep defaults when backend is unavailable
  }
}

const connectWebsocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${protocol}://${window.location.hostname}:8000/ws/alerts`)

  ws.onopen = () => ws.send('ping')
  ws.onmessage = (event) => {
    alerts.value.unshift(event.data)
    alerts.value = alerts.value.slice(0, 20)
  }
}

onMounted(() => {
  loadHealth()
  loadStats()
  connectWebsocket()
})
</script>
