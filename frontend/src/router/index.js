import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import MainLayout from '../views/MainLayout.vue'
import NoPermissionView from '../views/NoPermissionView.vue'
import ToolRecognitionView from '../views/modules/ToolRecognitionView.vue'
import ToolCountView from '../views/modules/ToolCountView.vue'
import PermissionManagementView from '../views/modules/PermissionManagementView.vue'
import SystemSettingsView from '../views/modules/SystemSettingsView.vue'
import { getSession } from '../auth/session'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/tool-recognition' },
      { path: 'no-permission', name: 'no-permission', component: NoPermissionView },
      { path: 'tool-recognition', name: 'tool-recognition', component: ToolRecognitionView, meta: { permission: '工具管理' } },
      { path: 'tool-count', name: 'tool-count', component: ToolCountView, meta: { permission: '工具识别' } },
      {
        path: 'permission-management',
        name: 'permission-management',
        component: PermissionManagementView,
        meta: { permission: '权限管理' }
      },
      { path: 'system-settings', name: 'system-settings', component: SystemSettingsView, meta: { permission: '系统设置' } }
    ]
  }
]

const hasPermission = (session, perm) => {
  if (!perm) return true
  if (!session) return false
  if (session.roleKey === 'admin' || session.username === 'admin') return true
  return (session.permissions || []).includes(perm)
}

const firstAllowedPath = (session) => {
  if (hasPermission(session, '工具管理')) return '/tool-recognition'
  if (hasPermission(session, '工具识别')) return '/tool-count'
  if (hasPermission(session, '权限管理')) return '/permission-management'
  if (hasPermission(session, '系统设置')) return '/system-settings'
  return '/no-permission'
}

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const session = getSession()

  if (to.meta.requiresAuth && !session) {
    return { name: 'login' }
  }

  if (to.name === 'login' && session) {
    return { path: firstAllowedPath(session) }
  }

  if (to.meta.requiresAuth && to.meta.permission && !hasPermission(session, to.meta.permission)) {
    return { path: firstAllowedPath(session) }
  }

  return true
})

export default router
