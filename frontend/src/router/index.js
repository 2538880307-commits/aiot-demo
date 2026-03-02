import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import MainLayout from '../views/MainLayout.vue'
import ToolRecognitionView from '../views/modules/ToolRecognitionView.vue'
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
      { path: 'tool-recognition', name: 'tool-recognition', component: ToolRecognitionView },
      {
        path: 'permission-management',
        name: 'permission-management',
        component: PermissionManagementView
      },
      { path: 'system-settings', name: 'system-settings', component: SystemSettingsView }
    ]
  }
]

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
    return { path: '/tool-recognition' }
  }

  return true
})

export default router
