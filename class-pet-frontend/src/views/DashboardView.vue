<script setup lang="ts">
/**
 * 首页 Dashboard：登录第一屏
 *
 * 4 块内容：
 * 1. 顶部统计卡：班级 / 学生 / 今日打分 / 待办
 * 2. 排行榜：积分 Top 5 + 等级 Top 5
 * 3. 7 天打分趋势 SVG 折线
 * 4. 最近班级快捷入口
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dashboardApi, type DashboardData } from '@/api/dashboard'
import { useAuthStore } from '@/stores/auth'
import { usePetSpeciesStore } from '@/stores/petSpecies'
import PetAvatar from '@/components/PetAvatar.vue'

const router = useRouter()
const auth = useAuthStore()
const speciesStore = usePetSpeciesStore()

const data = ref<DashboardData | null>(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const [d] = await Promise.all([
      dashboardApi.get(),
      speciesStore.ensureLoaded(),
    ])
    data.value = d
  } finally {
    loading.value = false
  }
}

onMounted(load)

// 当前问候语
const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 11) return '早上好'
  if (h < 13) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const todoTotal = computed(() => {
  if (!data.value) return 0
  return data.value.todo.ungraded_homework_records + data.value.todo.correction_pending
})

// SVG 折线参数
const trendSvg = computed(() => {
  if (!data.value || data.value.trend_7d.length === 0) {
    return { points: '', labels: [] as { x: number; text: string; count: number }[], yMax: 0 }
  }
  const arr = data.value.trend_7d
  const w = 100, h = 100
  const yMax = Math.max(1, ...arr.map((p) => p.count))
  const xStep = w / (arr.length - 1 || 1)
  const points = arr
    .map((p, i) => {
      const x = i * xStep
      const y = h - (p.count / yMax) * (h - 10) - 4
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
  const labels = arr.map((p, i) => ({
    x: i * xStep,
    text: p.date.slice(5),  // MM-DD
    count: p.count,
  }))
  return { points, labels, yMax }
})
</script>

<template>
  <div class="page">
    <!-- 顶部欢迎 -->
    <div class="hero">
      <div>
        <div class="greeting">{{ greeting }}，{{ auth.teacher?.display_name ?? '老师' }} ☀️</div>
        <div class="hero-sub">让我们看看今天班级里发生了什么</div>
      </div>
      <el-button type="primary" plain @click="load" :loading="loading">🔄 刷新</el-button>
    </div>

    <div v-loading="loading">
      <!-- 4 张统计卡 -->
      <div class="stat-grid" v-if="data">
        <div class="stat-card stat-blue" @click="router.push({ name: 'classes' })">
          <div class="stat-icon">📚</div>
          <div class="stat-num">{{ data.overview.class_count }}</div>
          <div class="stat-label">班级</div>
        </div>
        <div class="stat-card stat-purple" @click="router.push({ name: 'classes' })">
          <div class="stat-icon">👥</div>
          <div class="stat-num">{{ data.overview.student_count }}</div>
          <div class="stat-label">
            学生
            <span class="stat-sub" v-if="data.overview.unadopted_count > 0">
              · {{ data.overview.unadopted_count }} 待领养
            </span>
          </div>
        </div>
        <div class="stat-card stat-orange">
          <div class="stat-icon">⚡</div>
          <div class="stat-num">{{ data.today.behavior_count }}</div>
          <div class="stat-label">
            今日打分
            <span class="stat-sub" v-if="data.today.points_granted > 0">
              · 发放 +{{ data.today.points_granted }}
            </span>
          </div>
        </div>
        <div
          class="stat-card stat-red"
          :class="{ 'is-clickable': todoTotal > 0 }"
          @click="todoTotal > 0 && router.push({ name: 'homeworks' })"
        >
          <div class="stat-icon">⚠️</div>
          <div class="stat-num">{{ todoTotal }}</div>
          <div class="stat-label">
            待办
            <span class="stat-sub" v-if="data.todo.ungraded_homework_records > 0">
              · {{ data.todo.ungraded_homework_records }} 待批改
            </span>
            <span class="stat-sub" v-if="data.todo.correction_pending > 0">
              · {{ data.todo.correction_pending }} 待订正
            </span>
          </div>
        </div>
      </div>

      <div class="cols" v-if="data">
        <!-- 左列：排行榜 -->
        <div class="col-rank">
          <div class="panel">
            <div class="panel-title">💰 积分排行榜 Top 5</div>
            <el-empty v-if="data.points_rank.length === 0" description="还没有积分记录" :image-size="60" />
            <ol v-else class="rank-list">
              <li
                v-for="(s, i) in data.points_rank"
                :key="s.id"
                @click="router.push({ name: 'student-detail', params: { id: s.id } })"
              >
                <span class="rank-no" :class="`rank-${i + 1}`">{{ i + 1 }}</span>
                <span class="rank-name">{{ s.name }}</span>
                <span class="rank-meta">{{ s.class_name }}</span>
                <span class="rank-num">💰 {{ s.points }}</span>
              </li>
            </ol>
          </div>

          <div class="panel">
            <div class="panel-title">🏆 等级排行榜 Top 5</div>
            <el-empty v-if="data.level_rank.length === 0" description="还没有领养宠物" :image-size="60" />
            <ol v-else class="rank-list">
              <li
                v-for="(p, i) in data.level_rank"
                :key="p.pet_id"
                @click="router.push({ name: 'student-detail', params: { id: p.student_id } })"
              >
                <span class="rank-no" :class="`rank-${i + 1}`">{{ i + 1 }}</span>
                <span class="rank-avatar">
                  <PetAvatar :species="p.species" :level="p.level" :size="28" />
                </span>
                <span class="rank-name">
                  {{ p.pet_name }}
                  <span class="rank-meta-inline">（{{ p.student_name }}）</span>
                </span>
                <span class="rank-num">Lv.{{ p.level }}</span>
              </li>
            </ol>
          </div>
        </div>

        <!-- 右列：趋势图 + 最近班级 -->
        <div class="col-trend">
          <div class="panel">
            <div class="panel-title">📈 最近 7 天打分趋势</div>
            <div v-if="data.trend_7d.length === 0" class="trend-empty">还没有数据</div>
            <div v-else class="trend-wrap">
              <svg :viewBox="`0 0 100 110`" preserveAspectRatio="none" class="trend-svg">
                <!-- 网格线 -->
                <line x1="0" y1="100" x2="100" y2="100" stroke="#ebeef5" stroke-width="0.3" />
                <line x1="0" y1="50" x2="100" y2="50" stroke="#ebeef5" stroke-width="0.3" stroke-dasharray="1 1" />
                <!-- 折线 -->
                <polyline
                  :points="trendSvg.points"
                  fill="none"
                  stroke="#409eff"
                  stroke-width="0.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <!-- 节点 -->
                <circle
                  v-for="(p, i) in data.trend_7d"
                  :key="i"
                  :cx="i * (100 / (data.trend_7d.length - 1 || 1))"
                  :cy="100 - (p.count / (trendSvg.yMax || 1)) * 90 - 4"
                  r="1.2"
                  fill="#409eff"
                />
                <!-- 数字 -->
                <text
                  v-for="(p, i) in data.trend_7d"
                  :key="`n${i}`"
                  :x="i * (100 / (data.trend_7d.length - 1 || 1))"
                  :y="100 - (p.count / (trendSvg.yMax || 1)) * 90 - 6"
                  font-size="3"
                  text-anchor="middle"
                  fill="#606266"
                >{{ p.count > 0 ? p.count : '' }}</text>
                <!-- X 轴日期 -->
                <text
                  v-for="(l, i) in trendSvg.labels"
                  :key="`l${i}`"
                  :x="l.x"
                  y="108"
                  font-size="2.6"
                  text-anchor="middle"
                  fill="#909399"
                >{{ l.text }}</text>
              </svg>
            </div>
          </div>

          <div class="panel">
            <div class="panel-title">📚 最近班级</div>
            <el-empty v-if="data.recent_classes.length === 0" description="还没有班级，先去创建一个" :image-size="60" />
            <div v-else class="recent-grid">
              <div
                v-for="c in data.recent_classes"
                :key="c.id"
                class="recent-card"
                @click="router.push({ name: 'class-detail', params: { id: c.id } })"
              >
                <span class="recent-emoji">📖</span>
                <div class="recent-info">
                  <div class="recent-name">{{ c.name }}</div>
                  <div class="recent-meta">
                    <span v-if="c.grade">{{ c.grade }} · </span>{{ c.student_count }} 名学生
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 20px 24px;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
}

.greeting {
  font-size: 22px;
  font-weight: 600;
}

.hero-sub {
  font-size: 13px;
  opacity: 0.85;
  margin-top: 4px;
}

.hero :deep(.el-button) {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
}
.hero :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.3);
}

/* —— 统计卡 —— */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  position: relative;
  overflow: hidden;
  cursor: default;
  transition: transform 0.15s, box-shadow 0.15s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.stat-card.is-clickable,
.stat-blue, .stat-purple, .stat-red.is-clickable {
  cursor: pointer;
}

.stat-blue, .stat-purple, .stat-red {
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 32px;
  position: absolute;
  top: 16px;
  right: 16px;
  opacity: 0.5;
}

.stat-num {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  margin-top: 8px;
  font-size: 13px;
  color: #606266;
}

.stat-sub {
  color: #909399;
  font-size: 12px;
}

.stat-blue { background: linear-gradient(135deg, #ebf5ff 0%, #fff 60%); border-left: 4px solid #409eff; }
.stat-blue .stat-num { color: #409eff; }

.stat-purple { background: linear-gradient(135deg, #f4ecff 0%, #fff 60%); border-left: 4px solid #9c27b0; }
.stat-purple .stat-num { color: #9c27b0; }

.stat-orange { background: linear-gradient(135deg, #fff4e6 0%, #fff 60%); border-left: 4px solid #e6a23c; }
.stat-orange .stat-num { color: #e6a23c; }

.stat-red { background: linear-gradient(135deg, #fef0f0 0%, #fff 60%); border-left: 4px solid #f56c6c; }
.stat-red .stat-num { color: #f56c6c; }

/* —— 双列 —— */
.cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.col-rank, .col-trend {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

/* —— 排行榜 —— */
.rank-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.rank-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.1s;
}

.rank-list li:hover {
  background: #f4f6fa;
}

.rank-no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #ebeef5;
  color: #606266;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.rank-no.rank-1 { background: linear-gradient(135deg, #f7d423 0%, #f8b500 100%); color: #fff; }
.rank-no.rank-2 { background: linear-gradient(135deg, #c9d6e0 0%, #8392a3 100%); color: #fff; }
.rank-no.rank-3 { background: linear-gradient(135deg, #e8a36d 0%, #b86a3a 100%); color: #fff; }

.rank-avatar {
  display: inline-flex;
  align-items: center;
}

.rank-name {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rank-meta {
  font-size: 12px;
  color: #909399;
}

.rank-meta-inline {
  font-size: 12px;
  color: #909399;
  margin-left: 4px;
}

.rank-num {
  font-size: 13px;
  font-weight: 600;
  color: #e6a23c;
}

/* —— 趋势 —— */
.trend-wrap {
  width: 100%;
  height: 200px;
}

.trend-svg {
  width: 100%;
  height: 100%;
}

.trend-empty {
  text-align: center;
  color: #c0c4cc;
  padding: 40px 0;
}

/* —— 最近班级 —— */
.recent-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.recent-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f4f6fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.recent-card:hover {
  background: #ebf5ff;
  transform: translateX(2px);
}

.recent-emoji {
  font-size: 28px;
  line-height: 1;
}

.recent-info {
  flex: 1;
  min-width: 0;
}

.recent-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

@media (max-width: 900px) {
  .cols {
    grid-template-columns: 1fr;
  }
}
</style>
