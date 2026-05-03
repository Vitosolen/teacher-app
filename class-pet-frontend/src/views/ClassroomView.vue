<script setup lang="ts">
/**
 * 课堂大屏：投影到教室前面，全班学生宠物可视化
 *
 * - 进入自动 fullscreen
 * - 5 秒轮询拉最新学生数据，捕获积分变化触发"+X"飘字 + 闪光
 * - 顶部巨型班级名 + 实时时钟
 * - 中央：积分 Top 3 大字徽章
 * - 下方：网格学生卡（宠物头像 / 名字 / Lv / 积分 / 心情条）
 * - ESC 或右上角退出按钮返回
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { studentsApi } from '@/api/students'
import { classesApi } from '@/api/classes'
import { usePetSpeciesStore } from '@/stores/petSpecies'
import { useEffectsStore } from '@/stores/effects'
import PetAvatar from '@/components/PetAvatar.vue'
import type { Student, ClassItem } from '@/types/domain'

const props = defineProps<{ id: string | number }>()
const router = useRouter()
const speciesStore = usePetSpeciesStore()
const effects = useEffectsStore()

const classId = computed(() => Number(props.id))
const students = ref<Student[]>([])
const classInfo = ref<ClassItem | null>(null)
const loading = ref(false)
const now = ref(new Date())
let clockTimer: number | null = null
let pollTimer: number | null = null

// 上一次的 points 快照，对比检测变化
const prevPoints = ref<Record<number, number>>({})
const flashStudents = ref<Set<number>>(new Set())  // 刚加分的学生 id（短暂高亮）
const popups = ref<Array<{ id: number; studentId: number; delta: number; ts: number }>>([])
let popupId = 0

async function refresh() {
  loading.value = true
  try {
    const [list, all] = await Promise.all([
      studentsApi.listByClass(classId.value),
      classesApi.list(),
    ])
    classInfo.value = all.find((c) => c.id === classId.value) ?? null

    // 检测每个学生 points 变化
    const oldFlash = new Set<number>()
    let upgradedCount = 0
    for (const s of list) {
      const old = prevPoints.value[s.id]
      if (old !== undefined && s.points > old) {
        const delta = s.points - old
        oldFlash.add(s.id)
        popups.value.push({
          id: ++popupId,
          studentId: s.id,
          delta,
          ts: Date.now(),
        })
        // 简单升级触发：等级 > 之前。这里数据没保留 prev pet level，先用 points 增长 +5+ 作为近似撒花条件
        if (delta >= 5) upgradedCount++
      }
      prevPoints.value[s.id] = s.points
    }
    if (oldFlash.size > 0) {
      flashStudents.value = new Set([...flashStudents.value, ...oldFlash])
      setTimeout(() => {
        for (const id of oldFlash) flashStudents.value.delete(id)
        flashStudents.value = new Set(flashStudents.value)
      }, 1200)
    }
    if (upgradedCount > 0) effects.fireConfetti(50 + upgradedCount * 15)

    // 清理过期 popup（4 秒）
    const cutoff = Date.now() - 4000
    popups.value = popups.value.filter((p) => p.ts > cutoff)

    students.value = list
  } finally {
    loading.value = false
  }
}

// 排行榜 Top 3（按积分）
const top3 = computed(() => [...students.value].sort((a, b) => b.points - a.points).slice(0, 3))

// 退出大屏
async function exitClassroom() {
  if (document.fullscreenElement) {
    try { await document.exitFullscreen() } catch {/* ignore */}
  }
  router.push({ name: 'class-detail', params: { id: classId.value } })
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') exitClassroom()
}

async function tryFullscreen() {
  try {
    await document.documentElement.requestFullscreen()
  } catch {
    // 浏览器拦截或不支持，无所谓
  }
}

function statusEmoji(s?: string): string {
  switch (s) {
    case '健康': return '😊'
    case '饥饿': return '🍖'
    case '难过': return '😢'
    case '虚弱': return '😵'
    default: return ''
  }
}

onMounted(async () => {
  await speciesStore.ensureLoaded()
  await refresh()
  pollTimer = window.setInterval(refresh, 5000)
  clockTimer = window.setInterval(() => { now.value = new Date() }, 1000)
  window.addEventListener('keydown', onKey)
  // 用户点了"进入大屏"会有点击事件，从那里再 requestFullscreen
  await tryFullscreen()
})

onUnmounted(() => {
  if (pollTimer !== null) clearInterval(pollTimer)
  if (clockTimer !== null) clearInterval(clockTimer)
  window.removeEventListener('keydown', onKey)
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
})

const fmtTime = computed(() => {
  const d = now.value
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
})
const fmtDate = computed(() => {
  const d = now.value
  const days = ['日', '一', '二', '三', '四', '五', '六']
  return `${d.getMonth() + 1}月${d.getDate()}日 周${days[d.getDay()]}`
})
</script>

<template>
  <div class="classroom" v-loading="loading && students.length === 0">
    <!-- 顶部：班级 + 时钟 + 退出 -->
    <header class="top-bar">
      <div class="class-name">📚 {{ classInfo?.name ?? '班级' }}</div>
      <div class="clock-wrap">
        <div class="clock">{{ fmtTime }}</div>
        <div class="date">{{ fmtDate }}</div>
      </div>
      <el-button class="exit-btn" @click="exitClassroom" size="large">✕ 退出大屏</el-button>
    </header>

    <!-- Top 3 -->
    <div v-if="top3.length > 0" class="podium">
      <!-- 第二名（左）-->
      <div v-if="top3[1]" class="podium-card no-2">
        <div class="medal">🥈</div>
        <div class="podium-avatar">
          <PetAvatar v-if="top3[1].pet" :species="top3[1].pet.species" :level="top3[1].pet.level" :size="100" />
          <span v-else style="font-size: 100px">🐣</span>
        </div>
        <div class="podium-name">{{ top3[1].name }}</div>
        <div class="podium-points">💰 {{ top3[1].points }}</div>
      </div>
      <!-- 第一名（中）-->
      <div v-if="top3[0]" class="podium-card no-1">
        <div class="medal">🥇</div>
        <div class="podium-avatar">
          <PetAvatar v-if="top3[0].pet" :species="top3[0].pet.species" :level="top3[0].pet.level" :size="140" />
          <span v-else style="font-size: 140px">🐣</span>
        </div>
        <div class="podium-name">{{ top3[0].name }}</div>
        <div class="podium-points">💰 {{ top3[0].points }}</div>
      </div>
      <!-- 第三名（右）-->
      <div v-if="top3[2]" class="podium-card no-3">
        <div class="medal">🥉</div>
        <div class="podium-avatar">
          <PetAvatar v-if="top3[2].pet" :species="top3[2].pet.species" :level="top3[2].pet.level" :size="90" />
          <span v-else style="font-size: 90px">🐣</span>
        </div>
        <div class="podium-name">{{ top3[2].name }}</div>
        <div class="podium-points">💰 {{ top3[2].points }}</div>
      </div>
    </div>

    <!-- 全班网格 -->
    <div class="grid">
      <div
        v-for="s in students"
        :key="s.id"
        class="cell"
        :class="{ flash: flashStudents.has(s.id), homeless: !s.pet }"
      >
        <!-- 加分飘字 -->
        <transition-group name="popup" tag="div" class="popups">
          <div
            v-for="p in popups.filter((x) => x.studentId === s.id)"
            :key="p.id"
            class="popup"
          >+{{ p.delta }}</div>
        </transition-group>

        <div class="cell-avatar">
          <PetAvatar v-if="s.pet" :species="s.pet.species" :level="s.pet.level" :size="64" />
          <span v-else style="font-size: 56px; opacity: 0.6">🐣</span>
        </div>
        <div class="cell-name">{{ s.name }}</div>
        <div class="cell-meta">
          <span v-if="s.pet" class="lv">Lv.{{ s.pet.level }}</span>
          <span class="points">💰 {{ s.points }}</span>
          <span v-if="s.pet" class="mood-emoji">{{ statusEmoji(s.pet.status) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.classroom {
  position: fixed;
  inset: 0;
  background: linear-gradient(135deg, #1a1f3a 0%, #2d1b69 50%, #1a1f3a 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 100;
}

/* 装饰星空（用 box-shadow 画几个静态白点） */
.classroom::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(2px 2px at 20% 30%, rgba(255, 255, 255, 0.6), transparent),
    radial-gradient(1px 1px at 60% 70%, rgba(255, 255, 255, 0.4), transparent),
    radial-gradient(2px 2px at 80% 40%, rgba(255, 255, 255, 0.5), transparent),
    radial-gradient(1px 1px at 30% 80%, rgba(255, 255, 255, 0.5), transparent),
    radial-gradient(2px 2px at 90% 90%, rgba(255, 255, 255, 0.4), transparent);
  background-size: 200px 200px;
  animation: twinkle 6s ease-in-out infinite;
  pointer-events: none;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

/* —— 顶栏 —— */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 40px;
  position: relative;
  z-index: 2;
}

.class-name {
  font-size: 36px;
  font-weight: 700;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}

.clock-wrap {
  text-align: center;
}

.clock {
  font-size: 56px;
  font-weight: 700;
  letter-spacing: 4px;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 2px 12px rgba(102, 126, 234, 0.6);
}

.date {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: -4px;
}

.exit-btn :deep(.el-button) {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
}
.exit-btn {
  background: rgba(255, 255, 255, 0.1);
  color: #fff !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
}
.exit-btn:hover {
  background: rgba(255, 255, 255, 0.2) !important;
}

/* —— Top 3 —— */
.podium {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 32px;
  padding: 12px 40px 24px;
  position: relative;
  z-index: 2;
}

.podium-card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 16px 24px;
  text-align: center;
  position: relative;
  animation: float 3s ease-in-out infinite;
}
.podium-card.no-1 {
  transform: scale(1.15);
  border-color: #ffd700;
  box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
}
.podium-card.no-2 {
  border-color: #c0c0c0;
  animation-delay: 0.3s;
}
.podium-card.no-3 {
  border-color: #cd7f32;
  animation-delay: 0.6s;
}

@keyframes float {
  0%, 100% { transform: translateY(0) scale(var(--s, 1)); }
  50% { transform: translateY(-8px) scale(var(--s, 1)); }
}
.podium-card.no-1 { --s: 1.15; }

.medal {
  font-size: 40px;
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
}

.podium-avatar {
  margin: 8px 0;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.4));
}

.podium-name {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 4px;
}

.podium-points {
  font-size: 20px;
  color: #ffd700;
  font-weight: 600;
}

/* —— 全班网格 —— */
.grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 14px;
  padding: 16px 40px 40px;
  overflow-y: auto;
  position: relative;
  z-index: 2;
  align-content: start;
}

.cell {
  position: relative;
  background: rgba(255, 255, 255, 0.06);
  border: 1.5px solid rgba(255, 255, 255, 0.15);
  border-radius: 14px;
  padding: 14px 8px 10px;
  text-align: center;
  transition: all 0.3s;
}

.cell.homeless {
  opacity: 0.5;
}

.cell.flash {
  background: rgba(255, 215, 0, 0.25);
  border-color: #ffd700;
  box-shadow: 0 0 24px rgba(255, 215, 0, 0.6);
  transform: scale(1.05);
}

.cell-avatar {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cell-name {
  font-size: 16px;
  font-weight: 600;
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cell-meta {
  display: flex;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
  margin-top: 2px;
}

.lv {
  color: #91d5ff;
}

.points {
  color: #ffd700;
  font-weight: 600;
}

/* 飘字 */
.popups {
  position: absolute;
  top: 6px;
  right: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  pointer-events: none;
  z-index: 5;
}

.popup {
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #fff;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 16px;
  box-shadow: 0 2px 8px rgba(255, 140, 0, 0.5);
  animation: popUp 2.4s ease-out forwards;
}

@keyframes popUp {
  0% { transform: translateY(0); opacity: 0; }
  20% { transform: translateY(-10px); opacity: 1; }
  80% { transform: translateY(-30px); opacity: 1; }
  100% { transform: translateY(-50px); opacity: 0; }
}

.popup-enter-active,
.popup-leave-active {
  transition: all 0.3s;
}
.popup-leave-to {
  opacity: 0;
}
</style>
