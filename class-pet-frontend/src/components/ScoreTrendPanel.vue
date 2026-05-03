<script setup lang="ts">
/**
 * 学生成绩趋势分析
 *
 * - 顶部：科目选择 + 类型切换（全部 / 仅作业 / 仅成绩）
 * - 中部：SVG 折线图（按时间从左到右）
 *   - 等级颜色背景区（A 绿 / B 蓝 / C 黄 / D 红）
 *   - 鼠标悬停节点高亮显示标题与分数
 * - 底部：均值 / 最高分 / 最近一次进步退步
 * - 列表：明细按时间倒序，每行带等级标签
 */
import { ref, computed, onMounted, watch } from 'vue'
import { homeworksApi } from '@/api/homeworks'
import { subjectsApi } from '@/api/subjects'
import { getGrade } from '@/composables/useScoreGrade'
import { fmtShortDate, fmtDateTime } from '@/utils/datetime'
import type { StudentScore, Subject } from '@/types/domain'

const props = defineProps<{ studentId: number }>()

const subjects = ref<Subject[]>([])
const selectedSubjectId = ref<number | undefined>(undefined)
const selectedType = ref<'all' | 'homework' | 'exam'>('all')
const scores = ref<StudentScore[]>([])
const loading = ref(false)
const hoveredIdx = ref<number | null>(null)

async function loadSubjects() {
  subjects.value = await subjectsApi.list()
  if (subjects.value.length > 0 && !selectedSubjectId.value) {
    selectedSubjectId.value = subjects.value[0].id
  }
}

async function loadScores() {
  if (!selectedSubjectId.value) {
    scores.value = []
    return
  }
  loading.value = true
  try {
    scores.value = await homeworksApi.listStudentScores(props.studentId, {
      subject_id: selectedSubjectId.value,
      type: selectedType.value === 'all' ? undefined : selectedType.value,
    })
  } finally {
    loading.value = false
  }
}

// 用 watch 的 immediate 收敛"加载完字典 → 设默认 → 拉数据"的流程，避免 onMounted 再触发一次重复请求
watch([selectedSubjectId, selectedType, () => props.studentId], loadScores, { immediate: true })

onMounted(loadSubjects)

// —— 统计 ——
const stats = computed(() => {
  if (scores.value.length === 0) return null
  const arr = scores.value.map((s) => s.score)
  const avg = Math.round(arr.reduce((a, b) => a + b, 0) / arr.length)
  const max = Math.max(...arr)
  const min = Math.min(...arr)
  const last = arr[arr.length - 1]
  const prev = arr.length >= 2 ? arr[arr.length - 2] : null
  const delta = prev !== null ? last - prev : null
  return { avg, max, min, last, delta }
})

// —— SVG 参数 ——
const SVG_W = 100
const SVG_H = 60
const PAD_TOP = 4
const PAD_BOTTOM = 8
const CHART_H = SVG_H - PAD_TOP - PAD_BOTTOM

const svgPoints = computed(() => {
  const arr = scores.value
  if (arr.length === 0) return [] as { cx: number; cy: number; data: StudentScore }[]
  const xStep = arr.length === 1 ? 0 : SVG_W / (arr.length - 1)
  return arr.map((s, i) => ({
    cx: arr.length === 1 ? SVG_W / 2 : i * xStep,
    cy: PAD_TOP + (1 - s.score / 100) * CHART_H,
    data: s,
  }))
})

const polylinePoints = computed(() => {
  return svgPoints.value.map((p) => `${p.cx.toFixed(2)},${p.cy.toFixed(2)}`).join(' ')
})

// 等级背景区（A 85-100 / B 75-85 / C 60-75 / D 0-60）
const bandRects = computed(() => {
  const score2y = (s: number) => PAD_TOP + (1 - s / 100) * CHART_H
  return [
    { y: score2y(100), h: score2y(85) - score2y(100), color: '#67c23a', label: 'A' },
    { y: score2y(85), h: score2y(75) - score2y(85), color: '#409eff', label: 'B' },
    { y: score2y(75), h: score2y(60) - score2y(75), color: '#e6a23c', label: 'C' },
    { y: score2y(60), h: score2y(0) - score2y(60), color: '#f56c6c', label: 'D' },
  ]
})

function fmtDate(s: string | null) {
  return fmtShortDate(s)
}

function fmtDateTimeLocal(s: string | null) {
  return fmtDateTime(s)
}

function deltaText(curr: number, prev: number | null | undefined) {
  if (prev === null || prev === undefined) return ''
  const d = curr - prev
  if (d > 0) return `↑ +${d}`
  if (d < 0) return `↓ ${d}`
  return '— 持平'
}
</script>

<template>
  <div class="trend-panel">
    <!-- 控制栏 -->
    <div class="ctrl">
      <el-select
        v-model="selectedSubjectId"
        placeholder="选择科目"
        size="small"
        style="width: 140px"
      >
        <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-radio-group v-model="selectedType" size="small">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="homework">作业</el-radio-button>
        <el-radio-button value="exam">考试</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 统计概览 -->
    <div v-if="stats" class="stats-row">
      <div class="stat-box">
        <span class="stat-label">平均</span>
        <span class="stat-val">{{ stats.avg }}</span>
        <el-tag v-if="getGrade(stats.avg)" :type="getGrade(stats.avg)!.tagType" size="small" effect="dark">
          {{ getGrade(stats.avg)!.sub }}
        </el-tag>
      </div>
      <div class="stat-box">
        <span class="stat-label">最高</span>
        <span class="stat-val pos">{{ stats.max }}</span>
      </div>
      <div class="stat-box">
        <span class="stat-label">最低</span>
        <span class="stat-val">{{ stats.min }}</span>
      </div>
      <div class="stat-box" v-if="stats.delta !== null">
        <span class="stat-label">最近变化</span>
        <span
          class="stat-val"
          :class="{ pos: stats.delta > 0, neg: stats.delta < 0 }"
        >
          <template v-if="stats.delta > 0">↑ +{{ stats.delta }}</template>
          <template v-else-if="stats.delta < 0">↓ {{ stats.delta }}</template>
          <template v-else>— 持平</template>
        </span>
      </div>
    </div>

    <!-- 折线图 -->
    <el-empty v-if="scores.length === 0 && !loading" description="该科目下还没有已批改的成绩" :image-size="60" />
    <div v-else v-loading="loading" class="chart-wrap">
      <svg :viewBox="`0 0 ${SVG_W} ${SVG_H}`" preserveAspectRatio="none" class="chart-svg">
        <!-- 等级背景区 -->
        <rect
          v-for="b in bandRects"
          :key="b.label"
          x="0"
          :y="b.y"
          :width="SVG_W"
          :height="b.h"
          :fill="b.color"
          opacity="0.07"
        />
        <!-- 等级阈值线 -->
        <line v-for="t in [85, 75, 60]" :key="t" x1="0" :y1="PAD_TOP + (1 - t / 100) * CHART_H" :x2="SVG_W" :y2="PAD_TOP + (1 - t / 100) * CHART_H" stroke="#dcdfe6" stroke-width="0.15" stroke-dasharray="0.8 0.8" />
        <!-- 折线 -->
        <polyline
          v-if="svgPoints.length > 1"
          :points="polylinePoints"
          fill="none"
          stroke="#409eff"
          stroke-width="0.6"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <!-- 节点 -->
        <g v-for="(p, i) in svgPoints" :key="i">
          <circle
            :cx="p.cx"
            :cy="p.cy"
            :r="hoveredIdx === i ? 1.6 : 1.0"
            :fill="getGrade(p.data.score)?.tagType === 'success' ? '#67c23a'
                   : getGrade(p.data.score)?.tagType === 'primary' ? '#409eff'
                   : getGrade(p.data.score)?.tagType === 'warning' ? '#e6a23c'
                   : '#f56c6c'"
            stroke="#fff"
            stroke-width="0.3"
            @mouseenter="hoveredIdx = i"
            @mouseleave="hoveredIdx = null"
            style="cursor: pointer"
          />
          <text
            :x="p.cx"
            :y="p.cy - 1.4"
            font-size="2.2"
            text-anchor="middle"
            fill="#303133"
            font-weight="600"
          >{{ p.data.score }}</text>
        </g>
      </svg>

      <!-- 悬停 tooltip -->
      <div v-if="hoveredIdx !== null && svgPoints[hoveredIdx]" class="tooltip">
        <div class="tt-title">{{ svgPoints[hoveredIdx].data.homework_title }}</div>
        <div class="tt-row">
          <span class="tt-label">{{ svgPoints[hoveredIdx].data.homework_type === 'exam' ? '📊 成绩' : '📝 作业' }}</span>
          <span class="tt-score">{{ svgPoints[hoveredIdx].data.score }} 分</span>
          <el-tag
            v-if="getGrade(svgPoints[hoveredIdx].data.score)"
            :type="getGrade(svgPoints[hoveredIdx].data.score)!.tagType"
            size="small"
            effect="dark"
          >{{ getGrade(svgPoints[hoveredIdx].data.score)!.sub }}</el-tag>
        </div>
        <div class="tt-time">{{ fmtDateTimeLocal(svgPoints[hoveredIdx].data.scored_at) }}</div>
      </div>
    </div>

    <!-- 明细列表（最近 N 条，倒序） -->
    <div v-if="scores.length > 0" class="detail-list">
      <div class="detail-title">明细（{{ scores.length }} 次）</div>
      <div class="detail-rows">
        <div
          v-for="(s, i) in [...scores].reverse()"
          :key="s.record_id"
          class="detail-row"
        >
          <span class="d-date">{{ fmtDate(s.scored_at) }}</span>
          <span class="d-tag">{{ s.homework_type === 'exam' ? '📊' : '📝' }}</span>
          <span class="d-title">{{ s.homework_title }}</span>
          <el-tag
            v-if="getGrade(s.score)"
            :type="getGrade(s.score)!.tagType"
            size="small"
            effect="dark"
          >{{ getGrade(s.score)!.sub }}</el-tag>
          <span class="d-score">{{ s.score }}</span>
          <!-- 与上次的变化（注意 scores 是升序，reverse 后第 i 个对应原 length-1-i） -->
          <span
            class="d-delta"
            :class="{
              pos: scores[scores.length - 1 - i].score - (scores[scores.length - 2 - i]?.score ?? scores[scores.length - 1 - i].score) > 0,
              neg: scores[scores.length - 1 - i].score - (scores[scores.length - 2 - i]?.score ?? scores[scores.length - 1 - i].score) < 0,
            }"
          >{{ deltaText(scores[scores.length - 1 - i].score, scores[scores.length - 2 - i]?.score) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.trend-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ctrl {
  display: flex;
  gap: 8px;
  align-items: center;
}

.stats-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-box {
  flex: 1;
  min-width: 90px;
  background: #f4f6fa;
  border-radius: 8px;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.stat-val {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.stat-val.pos {
  color: #67c23a;
}

.stat-val.neg {
  color: #f56c6c;
}

.chart-wrap {
  position: relative;
  width: 100%;
  height: 180px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
}

.chart-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.tooltip {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  pointer-events: none;
  max-width: 220px;
}

.tt-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.tt-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tt-label {
  color: #606266;
}

.tt-score {
  font-weight: 600;
  color: #409eff;
  font-size: 14px;
}

.tt-time {
  color: #909399;
  font-size: 11px;
  margin-top: 4px;
}

.detail-list {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 10px 12px;
}

.detail-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
  font-weight: 500;
}

.detail-rows {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 180px;
  overflow-y: auto;
}

.detail-row {
  display: grid;
  grid-template-columns: 50px 24px 1fr 50px 36px 60px;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  font-size: 12px;
}

.d-date {
  color: #909399;
}

.d-tag {
  text-align: center;
}

.d-title {
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.d-score {
  font-weight: 600;
  color: #303133;
  text-align: right;
}

.d-delta {
  text-align: right;
  color: #909399;
  font-size: 11px;
}

.d-delta.pos {
  color: #67c23a;
}

.d-delta.neg {
  color: #f56c6c;
}
</style>
