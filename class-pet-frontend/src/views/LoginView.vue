<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { AxiosError } from 'axios'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const tab = ref<'login' | 'register'>('login')
const loading = ref(false)
const errorMsg = ref('')
const shake = ref(false)

const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', password: '', display_name: '' })

// 切换 Tab 时清空错误，避免错误信息错位
watch(tab, () => {
  errorMsg.value = ''
})

// 把 axios 错误转成用户能看懂的中文提示
function extractError(e: unknown, fallback: string): string {
  if (e instanceof AxiosError) {
    const status = e.response?.status
    const detail = (e.response?.data as { detail?: string } | undefined)?.detail

    // 401 登录失败 = 用户名或密码错误（即便后端 detail 是英文也覆盖掉）
    if (status === 401) return '用户名或密码错误'
    if (status === 400 && detail) return detail
    if (status === 422) return '输入格式有误，请检查'
    if (e.code === 'ECONNABORTED') return '请求超时，请检查后端是否启动'
    if (!e.response) return '无法连接服务器，请检查后端是否在 8000 端口运行'
    return detail || fallback
  }
  return fallback
}

function triggerShake() {
  shake.value = false
  // 重置后再触发，确保动画每次都重放
  requestAnimationFrame(() => {
    shake.value = true
    setTimeout(() => (shake.value = false), 400)
  })
}

async function handleLogin() {
  errorMsg.value = ''
  if (!loginForm.username || !loginForm.password) {
    errorMsg.value = '请填写用户名和密码'
    triggerShake()
    return
  }
  loading.value = true
  try {
    await auth.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    router.push({ name: 'dashboard' })
  } catch (e) {
    errorMsg.value = extractError(e, '登录失败')
    triggerShake()
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  errorMsg.value = ''
  if (!regForm.username || !regForm.password || !regForm.display_name) {
    errorMsg.value = '请填写完整信息'
    triggerShake()
    return
  }
  if (regForm.password.length < 6) {
    errorMsg.value = '密码至少 6 位'
    triggerShake()
    return
  }
  loading.value = true
  try {
    await auth.register({ ...regForm })
    ElMessage.success('注册成功，已自动登录')
    router.push({ name: 'dashboard' })
  } catch (e) {
    errorMsg.value = extractError(e, '注册失败')
    triggerShake()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <!-- 装饰浮动元素 -->
    <div class="bg-blob blob-1"></div>
    <div class="bg-blob blob-2"></div>
    <div class="bg-blob blob-3"></div>

    <div class="login-card" :class="{ shake }">
      <div class="login-header">
        <div class="logo-wrap">
          <span class="logo">🐉</span>
        </div>
        <h2>班级养宠物系统</h2>
        <p class="tagline">让每个学生都有一只属于自己的宠物</p>
      </div>

      <el-tabs v-model="tab" stretch class="login-tabs">
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" label-position="top" @submit.prevent="handleLogin">
            <transition name="alert-fade">
              <el-alert
                v-if="errorMsg && tab === 'login'"
                :title="errorMsg"
                type="error"
                show-icon
                :closable="false"
                class="login-alert"
              />
            </transition>

            <el-form-item label="用户名">
              <el-input
                v-model="loginForm.username"
                placeholder="输入用户名"
                size="large"
                :prefix-icon="undefined"
                clearable
                autocomplete="username"
              >
                <template #prefix>👤</template>
              </el-input>
            </el-form-item>
            <el-form-item label="密码">
              <el-input
                v-model="loginForm.password"
                type="password"
                show-password
                placeholder="输入密码"
                size="large"
                autocomplete="current-password"
              >
                <template #prefix>🔒</template>
              </el-input>
            </el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              native-type="submit"
              size="large"
              style="width: 100%"
              class="submit-btn"
            >
              登录
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form :model="regForm" label-position="top" @submit.prevent="handleRegister">
            <transition name="alert-fade">
              <el-alert
                v-if="errorMsg && tab === 'register'"
                :title="errorMsg"
                type="error"
                show-icon
                :closable="false"
                class="login-alert"
              />
            </transition>

            <el-form-item label="用户名">
              <el-input
                v-model="regForm.username"
                placeholder="3-50 字符"
                size="large"
                clearable
                autocomplete="username"
              >
                <template #prefix>👤</template>
              </el-input>
            </el-form-item>
            <el-form-item label="密码">
              <el-input
                v-model="regForm.password"
                type="password"
                show-password
                placeholder="至少 6 位"
                size="large"
                autocomplete="new-password"
              >
                <template #prefix>🔒</template>
              </el-input>
            </el-form-item>
            <el-form-item label="显示名">
              <el-input
                v-model="regForm.display_name"
                placeholder="例如：张老师"
                size="large"
                clearable
              >
                <template #prefix>✨</template>
              </el-input>
            </el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              native-type="submit"
              size="large"
              style="width: 100%"
              class="submit-btn"
            >
              注册并登录
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <p class="footer-tip">忘记密码？请联系管理员重置</p>
    </div>
  </div>
</template>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

/* 背景浮动装饰 */
.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.4;
  pointer-events: none;
}

.blob-1 {
  width: 320px;
  height: 320px;
  background: #ffd1ff;
  top: -80px;
  left: -80px;
  animation: float 12s ease-in-out infinite;
}

.blob-2 {
  width: 260px;
  height: 260px;
  background: #a3e9ff;
  bottom: -60px;
  right: -60px;
  animation: float 15s ease-in-out infinite reverse;
}

.blob-3 {
  width: 200px;
  height: 200px;
  background: #ffe7a3;
  top: 50%;
  right: 10%;
  animation: float 18s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(30px, -30px) scale(1.1); }
}

.login-card {
  position: relative;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.18);
  padding: 36px 32px 24px;
  width: 400px;
  z-index: 1;
}

.login-card.shake {
  animation: shake 0.4s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-10px); }
  40% { transform: translateX(10px); }
  60% { transform: translateX(-6px); }
  80% { transform: translateX(6px); }
}

.login-header {
  text-align: center;
  margin-bottom: 8px;
}

.logo-wrap {
  display: inline-block;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ffe9d4 0%, #ffd1f0 100%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 20px rgba(255, 154, 158, 0.4);
}

.logo {
  font-size: 44px;
  line-height: 1;
}

.login-header h2 {
  margin: 16px 0 6px;
  color: #303133;
  font-size: 22px;
  font-weight: 600;
}

.tagline {
  margin: 0;
  color: #909399;
  font-size: 13px;
}

.login-tabs {
  margin-top: 8px;
}

.login-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 500;
}

.login-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 2px;
}

.login-alert {
  margin-bottom: 16px;
}

.alert-fade-enter-active,
.alert-fade-leave-active {
  transition: all 0.25s ease;
}

.alert-fade-enter-from,
.alert-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.submit-btn {
  margin-top: 8px;
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 2px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: transform 0.15s, box-shadow 0.15s;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.footer-tip {
  text-align: center;
  margin: 16px 0 0;
  color: #c0c4cc;
  font-size: 12px;
}
</style>
