<template>
  <div class="login-page">
    <div class="visual-overlay">
      <h2>轨道交通检修工具监测平台</h2>
      <p>实时感知 | 智能预警 | 闭环管理</p>
    </div>

    <section class="login-panel">
      <div class="login-card">
        <h1>用户登录</h1>
        <p>请输入账号登录系统</p>

        <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              size="large"
              placeholder="用户名"
              autocomplete="username"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              size="large"
              placeholder="密码"
              show-password
              autocomplete="current-password"
            />
          </el-form-item>
          <el-button type="primary" size="large" :loading="loading" class="submit-btn" @click="handleLogin">
            登录
          </el-button>
        </el-form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { setSession } from '../auth/session'
import { http } from '../api/http'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const { data } = await http.post('/api/v1/auth/login', {
      username: form.username,
      password: form.password
    })

    const session = {
      username: data.username,
      employeeNo: data.employee_no,
      displayName: data.display_name || data.name || data.username,
      role: data.role === 'admin' ? '管理员' : '员工',
      roleKey: data.role_key || data.role,
      permissions: data.permissions || [],
      loginAt: data.login_at
    }

    setSession(session)
    ElMessage.success(`欢迎，${session.displayName}`)
    router.replace('/')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 48px 84px;
  background-image: linear-gradient(rgba(9, 24, 45, 0.32), rgba(9, 24, 45, 0.48)), url('/images/metro-train.jpg');
  background-size: cover;
  background-position: center;
}

.visual-overlay {
  position: absolute;
  top: 48px;
  left: 56px;
  color: #f8fbff;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
}

.visual-overlay h2 {
  margin: 0;
  font-size: 56px;
  letter-spacing: 1px;
}

.visual-overlay p {
  margin: 18px 0 0;
  font-size: 30px;
  opacity: 0.95;
}

.login-panel {
  width: 100%;
  max-width: 500px;
}

.login-card {
  width: 100%;
  min-height: 400px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(6px);
  border-radius: 18px;
  padding: 45px 38px 48px;
  box-shadow: 0 22px 60px rgba(11, 27, 49, 0.35);
}

.login-card h1 {
  margin: 0;
  font-size: 40px;
  color: #1f2937;
}

.login-card p {
  margin: 10px 0 24px;
  color: #607089;
  font-size: 18px;
}

.submit-btn {
  width: 100%;
  margin-top: 10px;
}

@media (max-width: 1200px) {
  .visual-overlay h2 {
    font-size: 42px;
  }

  .visual-overlay p {
    font-size: 24px;
  }
}

@media (max-width: 900px) {
  .login-page {
    justify-content: center;
    padding: 24px;
  }

  .visual-overlay {
    position: static;
    margin-bottom: 14px;
    width: 100%;
  }

  .visual-overlay h2 {
    font-size: 28px;
  }

  .visual-overlay p {
    margin-top: 8px;
    font-size: 16px;
  }

  .login-panel {
    max-width: 540px;
  }

  .login-card {
    padding: 30px 24px;
  }

  .login-card h1 {
    font-size: 30px;
  }

  .login-card p {
    font-size: 16px;
  }
}
</style>
