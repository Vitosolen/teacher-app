<script setup lang="ts">
/**
 * 后端连通性自检：
 * - 启动时 ping 一次
 * - 失败时顶部展示告警横幅，提示常见原因和排查步骤
 * - 横幅上有「重试」按钮；恢复后自动消失
 * - 持续运行期每 30 秒静默 ping 一次（不打扰）
 */
import { onMounted, onUnmounted, ref } from 'vue'
import axios from 'axios'

type Status = 'checking' | 'ok' | 'down'
const status = ref<Status>('checking')
const checking = ref(false)
const errorDetail = ref('')

let timer: number | null = null

async function probe() {
  checking.value = true
  try {
    // 直接用 axios 不走我们 http 拦截器，避免无限递归 / token 影响
    const r = await axios.get('/api/v1/ping', { timeout: 5000 })
    if (r.data?.ok === true) {
      status.value = 'ok'
      errorDetail.value = ''
    } else {
      status.value = 'down'
      errorDetail.value = '后端响应格式异常'
    }
  } catch (e: unknown) {
    status.value = 'down'
    if (axios.isAxiosError(e)) {
      if (e.code === 'ECONNABORTED') errorDetail.value = '连接超时'
      else if (!e.response) errorDetail.value = '无法连接到后端服务'
      else errorDetail.value = `HTTP ${e.response.status}`
    } else {
      errorDetail.value = String(e)
    }
  } finally {
    checking.value = false
  }
}

onMounted(() => {
  probe()
  // 每 30 秒静默自检一次
  timer = window.setInterval(() => {
    if (!checking.value) probe()
  }, 30000)
})

onUnmounted(() => {
  if (timer !== null) clearInterval(timer)
})
</script>

<template>
  <transition name="banner">
    <div v-if="status === 'down'" class="banner">
      <div class="banner-inner">
        <span class="icon">🚨</span>
        <div class="text">
          <div class="title">无法连接后端服务（{{ errorDetail }}）</div>
          <div class="hint">
            常见原因：①后端 uvicorn 未启动 ②端口被占用（看
            <code>vite.config.ts</code> 的 proxy 与 <code>.env.local</code> 的
            <code>VITE_BACKEND_PORT</code>）③后端崩溃。请检查后端 cmd 窗口是否报错。
          </div>
        </div>
        <el-button
          size="small"
          type="primary"
          plain
          :loading="checking"
          @click="probe"
        >重试</el-button>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.banner {
  background: linear-gradient(90deg, #fef0f0 0%, #fef0f0 100%);
  border-bottom: 1px solid #fbc4c4;
  color: #b30000;
  padding: 8px 16px;
  z-index: 1000;
}

.banner-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon {
  font-size: 24px;
  flex-shrink: 0;
}

.text {
  flex: 1;
}

.title {
  font-weight: 600;
  font-size: 14px;
}

.hint {
  font-size: 12px;
  color: #803131;
  margin-top: 2px;
  line-height: 1.5;
}

.hint code {
  background: rgba(255, 255, 255, 0.6);
  padding: 0 4px;
  border-radius: 3px;
  font-size: 11px;
}

.banner-enter-active,
.banner-leave-active {
  transition: max-height 0.25s ease, opacity 0.2s ease;
  overflow: hidden;
}

.banner-enter-from,
.banner-leave-to {
  max-height: 0;
  opacity: 0;
}

.banner-enter-to,
.banner-leave-from {
  max-height: 80px;
  opacity: 1;
}
</style>
