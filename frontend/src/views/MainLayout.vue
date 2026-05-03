<template>
  <div class="console-page">
    <aside class="sidebar">
      <div class="brand">轨道交通检修工具监测平台</div>
      <el-menu
        :default-active="activeMenu"
        class="menu"
        router
        background-color="#091c33"
        text-color="#b8c9dd"
        active-text-color="#ffffff"
      >
        <el-menu-item v-if="hasPermission('工具管理')" index="/tool-recognition">工具管理</el-menu-item>
        <el-menu-item v-if="hasPermission('工具识别')" index="/tool-count">工具识别</el-menu-item>
        <el-menu-item v-if="hasPermission('权限管理')" index="/permission-management">权限管理</el-menu-item>
        <el-menu-item v-if="hasPermission('系统设置')" index="/system-settings">系统设置</el-menu-item>
      </el-menu>
    </aside>

    <section class="main">
      <header class="topbar">
        <div class="crumb">{{ pageTitle }}</div>
        <div class="user-area">
          <span>{{ session?.displayName }}（{{ session?.role }}）</span>
          <el-button size="small" type="danger" plain @click="logout">退出</el-button>
        </div>
      </header>

      <main class="content">
        <router-view />
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { clearSession, getSession } from '../auth/session'

const route = useRoute()
const router = useRouter()
const session = ref(getSession())

const titleMap = {
  '/no-permission': '无权限',
  '/tool-recognition': '工具管理',
  '/tool-count': '工具识别',
  '/permission-management': '权限管理',
  '/system-settings': '系统设置'
}

const activeMenu = computed(() => route.path)
const hasPermission = (perm) => {
  if (!session.value) return false
  if (session.value.roleKey === 'admin' || session.value.username === 'admin') return true
  return (session.value.permissions || []).includes(perm)
}

const pageTitle = computed(() => titleMap[route.path] || '控制台')

const logout = () => {
  clearSession()
  ElMessage.success('已退出登录')
  router.replace('/login')
}
</script>

<style scoped>
.console-page {
  min-height: 100vh;
  display: flex;
  background: #f3f6fb;
}

.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #07192f 0%, #0a2543 100%);
  color: #fff;
  box-shadow: 2px 0 18px rgba(5, 20, 36, 0.25);
}

.brand {
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0 18px;
  font-size: 20px;
  font-weight: 700;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.menu {
  border-right: none;
}

.main {
  flex: 1;
  min-width: 0;
}

.topbar {
  height: 64px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #e5eaf3;
}

.crumb {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #475569;
}

.content {
  padding: 20px;
}

@media (max-width: 900px) {
  .sidebar {
    width: 190px;
  }

  .brand {
    font-size: 16px;
  }

  .topbar {
    padding: 0 14px;
  }
}
</style>
