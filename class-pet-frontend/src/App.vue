<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usePetSpeciesStore } from '@/stores/petSpecies'
import { useRouter, useRoute } from 'vue-router'
import BackendHealthBanner from '@/components/BackendHealthBanner.vue'
import ConfettiOverlay from '@/components/ConfettiOverlay.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

// 顶栏导航高亮
const activeMenu = computed(() => {
  const name = String(route.name ?? '')
  if (name === 'dashboard') return 'dashboard'
  if (name === 'classes' || name === 'class-detail' || name === 'student-detail') return 'classes'
  if (name === 'subjects') return 'subjects'
  if (name === 'homeworks' || name === 'homework-detail') return 'homeworks'
  if (name === 'exams' || name === 'exam-detail') return 'exams'
  if (name === 'dictation' || name === 'word-group-detail') return 'dictation'
  if (name === 'shop') return 'shop'
  if (name === 'score-rules') return 'score-rules'
  if (name === 'species-manage') return 'species-manage'
  return ''
})

const speciesStore = usePetSpeciesStore()

onMounted(async () => {
  if (auth.isLoggedIn && !auth.teacher) {
    try {
      await auth.fetchMe()
    } catch {
      // 拦截器会处理 401 跳登录
    }
  }
  // 登录后预加载物种字典，让所有页面 emoji fallback 立即可用
  if (auth.isLoggedIn) {
    speciesStore.ensureLoaded().catch(() => {/* 静默 */})
  }
})

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <el-container class="app-shell">
    <BackendHealthBanner />
    <ConfettiOverlay />
    <el-header v-if="auth.isLoggedIn && !route.meta.hideHeader" class="app-header">
      <div class="brand" @click="router.push({ name: 'dashboard' })">
        <span class="brand-icon">🐉</span>
        <span class="brand-name">班级养宠物系统</span>
      </div>

      <el-menu
        mode="horizontal"
        :default-active="activeMenu"
        class="nav-menu"
        @select="(k: string) => router.push({ name: k })"
        :ellipsis="false"
      >
        <el-menu-item index="dashboard">🏠 首页</el-menu-item>
        <el-menu-item index="classes">📚 班级</el-menu-item>
        <el-menu-item index="subjects">📖 科目</el-menu-item>
        <el-menu-item index="homeworks">📝 作业</el-menu-item>
        <el-menu-item index="exams">📊 成绩</el-menu-item>
        <el-menu-item index="dictation">📢 听写</el-menu-item>
        <el-menu-item index="shop">🛒 商城</el-menu-item>
        <el-sub-menu index="settings">
          <template #title>⚙️ 设置</template>
          <el-menu-item index="score-rules">积分规则</el-menu-item>
          <el-menu-item index="species-manage">宠物物种</el-menu-item>
        </el-sub-menu>
      </el-menu>

      <div class="user-area" v-if="auth.teacher">
        <span class="welcome">欢迎，{{ auth.teacher.display_name }} 老师</span>
        <el-button text size="small" @click="logout">退出</el-button>
      </div>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<style>
.app-shell {
  min-height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  height: 56px !important;
  padding: 0 24px;
  gap: 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  flex-shrink: 0;
}

.brand-icon {
  font-size: 22px;
}

.nav-menu {
  flex: 1;
  border-bottom: none !important;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.welcome {
  color: #606266;
  font-size: 14px;
}

.app-main {
  padding: 0 !important;
}
</style>
