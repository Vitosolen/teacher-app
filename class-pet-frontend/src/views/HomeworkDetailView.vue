<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { homeworksApi } from '@/api/homeworks'
import { studentsApi } from '@/api/students'
import { getGrade } from '@/composables/useScoreGrade'
import { isSameDay as isSameDayUtc } from '@/utils/datetime'
import type { HomeworkDetail, HomeworkRecord, Student } from '@/types/domain'

const props = defineProps<{ id: string | number }>()
const router = useRouter()

const homeworkId = computed(() => Number(props.id))
const homework = ref<HomeworkDetail | null>(null)
const loading = ref(false)
const saving = ref<Record<number, boolean>>({})
const justSaved = ref<Record<number, boolean>>({})  // 刚保存成功 → 显示 ✓ 2 秒

const isExam = computed(() => homework.value?.type === 'exam')
const itemText = computed(() => isExam.value ? '成绩' : '作业')
const sectionTitle = computed(() => isExam.value ? '学生成绩' : '学生作业')

async function load() {
  loading.value = true
  try {
    homework.value = await homeworksApi.get(homeworkId.value)
  } finally {
    loading.value = false
  }
}

// —— 追加学生 ——
const addDialog = ref(false)
const classStudents = ref<Student[]>([])
const selectedNewIds = ref<number[]>([])
const addLoading = ref(false)

const candidateStudents = computed(() => {
  if (!homework.value) return []
  const existing = new Set(homework.value.records.map((r) => r.student_id))
  return classStudents.value.filter((s) => !existing.has(s.id))
})

async function openAddStudent() {
  if (!homework.value) return
  addLoading.value = true
  try {
    classStudents.value = await studentsApi.listByClass(homework.value.class_id)
    if (candidateStudents.value.length === 0) {
      ElMessage.info('班级里所有学生都已绑定该作业')
      return
    }
    selectedNewIds.value = []
    addDialog.value = true
  } finally {
    addLoading.value = false
  }
}

async function confirmAddStudents() {
  if (selectedNewIds.value.length === 0) {
    ElMessage.warning('请至少选择 1 名学生')
    return
  }
  await homeworksApi.addRecords(homeworkId.value, selectedNewIds.value)
  ElMessage.success(`已追加 ${selectedNewIds.value.length} 名学生`)
  addDialog.value = false
  await load()
}

function refreshStats() {
  if (!homework.value) return
  homework.value.graded_count = homework.value.records.filter((r) => r.status === '已批改').length
  homework.value.correction_pending_count = homework.value.records.filter(
    (r) => r.needs_correction && !r.corrected,
  ).length
}

async function saveRecord(rec: HomeworkRecord, opts: { silent?: boolean } = {}) {
  saving.value[rec.id] = true
  try {
    const updated = await homeworksApi.updateRecord(rec.id, {
      score: rec.score,
      comment: rec.comment,
    })
    if (homework.value) {
      const idx = homework.value.records.findIndex((r) => r.id === rec.id)
      if (idx >= 0) homework.value.records[idx] = updated
      refreshStats()
    }
    if (!isExam.value && updated.needs_correction && !opts.silent) {
      ElMessage.warning(`${rec.student_name} 已批改：${updated.score} 分，需要订正`)
    } else if (!opts.silent) {
      ElMessage.success(`${rec.student_name} 已保存`)
    }
    // 静默保存（失焦自动）只显示行内 ✓
    justSaved.value[rec.id] = true
    setTimeout(() => { delete justSaved.value[rec.id] }, 2000)
  } finally {
    saving.value[rec.id] = false
  }
}

// 失焦/值变化自动保存（行内显示状态，不弹 toast 避免打扰）
function autoSave(rec: HomeworkRecord) {
  saveRecord(rec, { silent: true })
}

async function markCorrected(rec: HomeworkRecord, value: boolean) {
  saving.value[rec.id] = true
  try {
    const updated = await homeworksApi.updateRecord(rec.id, { corrected: value })
    if (homework.value) {
      const idx = homework.value.records.findIndex((r) => r.id === rec.id)
      if (idx >= 0) homework.value.records[idx] = updated
      refreshStats()
    }
    ElMessage.success(value ? `${rec.student_name} 已订正` : '已撤销订正')
  } finally {
    saving.value[rec.id] = false
  }
}

function statusTagType(status: string) {
  switch (status) {
    case '已批改': return 'success'
    case '已提交': return 'warning'
    default: return 'info'
  }
}

// 是否在批改当天（用 UTC 解析后比较本地日期）
const isSameDay = isSameDayUtc

function correctionBadge(rec: HomeworkRecord): { text: string; type: '' | 'success' | 'warning' | 'danger' | 'info' } | null {
  if (isExam.value) return null
  if (!rec.needs_correction) return null
  if (rec.corrected) return { text: '✓ 已订正', type: 'success' }
  // 未订正：判断是否还在当日
  if (rec.scored_at && isSameDay(rec.scored_at)) {
    return { text: '⚠ 待订正（今日）', type: 'warning' }
  }
  return { text: '🚨 逾期未订正', type: 'danger' }
}

onMounted(load)
</script>

<template>
  <div class="page" v-loading="loading">
    <div class="page-header">
      <div>
        <el-button text @click="router.back()">← 返回</el-button>
        <h2 class="page-title" style="display: inline; margin-left: 8px">
          {{ homework?.title ?? itemText }}
        </h2>
        <el-tag v-if="isExam" type="primary" size="small" style="margin-left: 8px">📊 成绩</el-tag>
        <el-tag v-else size="small" style="margin-left: 8px">📝 作业</el-tag>
      </div>
    </div>

    <div v-if="homework" class="meta-bar">
      <el-tag
        size="default"
        :style="{
          background: homework.subject_color,
          color: '#fff',
          borderColor: 'transparent',
        }"
      >{{ homework.subject_name }}</el-tag>
      <el-tag size="default" effect="plain">{{ homework.class_name }}</el-tag>
      <el-tag v-if="homework.due_date" size="default" type="warning" effect="plain">
        截止 {{ homework.due_date }}
      </el-tag>
      <span class="meta-progress">
        {{ isExam ? '登记进度' : '批改进度' }}
        <strong>{{ homework.graded_count }} / {{ homework.total_count }}</strong>
        <span
          v-if="!isExam && homework.correction_pending_count > 0"
          class="correction-summary"
        >
          · ⚠️ {{ homework.correction_pending_count }} 待订正
        </span>
      </span>
    </div>

    <div v-if="homework?.content" class="content-box">
      {{ homework.content }}
    </div>

    <div class="section-bar">
      <h3 class="section-title">{{ sectionTitle }}</h3>
      <el-button size="small" type="primary" plain @click="openAddStudent">
        ➕ 追加学生
      </el-button>
    </div>
    <el-table :data="homework?.records ?? []" stripe>
      <el-table-column prop="student_name" label="姓名" width="100" fixed />
      <el-table-column prop="student_no" label="学号" width="100" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="isExam ? '分数' : '分数（0-100）'" width="200">
        <template #default="{ row }">
          <div class="score-cell">
            <el-input-number
              v-model="row.score"
              :min="0"
              :max="100"
              :step="1"
              size="small"
              controls-position="right"
              style="width: 110px"
              @change="autoSave(row)"
            />
            <el-tag
              v-if="getGrade(row.score)"
              :type="getGrade(row.score)!.tagType"
              size="small"
              effect="dark"
              class="grade-tag"
              :title="`${getGrade(row.score)!.grade} 等级 ${getGrade(row.score)!.range}`"
            >
              {{ getGrade(row.score)!.sub }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="isExam ? '备注' : '评语'" min-width="220">
        <template #default="{ row }">
          <el-input
            v-model="row.comment"
            :placeholder="isExam ? '备注（可选）' : '点评（最多 500 字）'"
            maxlength="500"
            size="small"
            @blur="autoSave(row)"
            @keydown.enter="autoSave(row)"
          />
        </template>
      </el-table-column>
      <el-table-column v-if="!isExam" label="订正" width="160">
        <template #default="{ row }">
          <span v-if="!row.needs_correction" class="muted">—</span>
          <template v-else>
            <el-tag
              v-if="correctionBadge(row)"
              :type="correctionBadge(row)!.type"
              size="small"
              style="margin-bottom: 4px"
            >{{ correctionBadge(row)!.text }}</el-tag>
            <div>
              <el-button
                v-if="!row.corrected"
                size="small"
                type="success"
                plain
                :loading="saving[row.id]"
                @click="markCorrected(row, true)"
              >标记已订正</el-button>
              <el-button
                v-else
                size="small"
                text
                @click="markCorrected(row, false)"
              >撤销</el-button>
            </div>
          </template>
        </template>
      </el-table-column>
      <el-table-column label="保存" width="90" fixed="right">
        <template #default="{ row }">
          <span v-if="saving[row.id]" class="save-state saving">
            <el-icon class="is-loading"><svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="9" stroke="#909399" stroke-width="2" fill="none" stroke-dasharray="40 60"/></svg></el-icon>
            保存中
          </span>
          <span v-else-if="justSaved[row.id]" class="save-state saved">✓ 已保存</span>
          <el-button
            v-else
            text
            size="small"
            @click="saveRecord(row)"
          >💾 保存</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 追加学生弹窗 -->
    <el-dialog v-model="addDialog" title="追加学生到此作业" width="460">
      <p class="add-tip">
        勾选要加入的学生（仅显示班内还没绑定该{{ isExam ? '成绩' : '作业' }}的学生）：
      </p>
      <el-checkbox-group v-model="selectedNewIds">
        <div class="add-list">
          <el-checkbox
            v-for="s in candidateStudents"
            :key="s.id"
            :value="s.id"
            class="add-item"
          >
            <span class="add-name">{{ s.name }}</span>
            <span class="add-no" v-if="s.student_no">#{{ s.student_no }}</span>
          </el-checkbox>
        </div>
      </el-checkbox-group>
      <div class="add-foot">
        <el-button text size="small" @click="selectedNewIds = candidateStudents.map((s) => s.id)">全选</el-button>
        <el-button text size="small" @click="selectedNewIds = []">清空</el-button>
        <span class="add-count">已选 {{ selectedNewIds.length }} / {{ candidateStudents.length }}</span>
      </div>
      <template #footer>
        <el-button @click="addDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddStudents">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.meta-bar {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 16px;
}

.meta-progress {
  margin-left: auto;
  color: #606266;
  font-size: 14px;
}

.meta-progress strong {
  color: #303133;
  font-weight: 600;
}

.correction-summary {
  margin-left: 8px;
  color: #e6a23c;
  font-weight: 500;
}

.content-box {
  background: #f4f6fa;
  border-left: 4px solid #409eff;
  padding: 12px 16px;
  border-radius: 4px;
  margin-bottom: 16px;
  white-space: pre-wrap;
  color: #303133;
}

.section-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 24px 0 12px;
}

.section-title {
  font-size: 16px;
  margin: 0;
  color: #303133;
}

.add-tip {
  margin: 0 0 12px;
  font-size: 13px;
  color: #606266;
}

.add-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 320px;
  overflow-y: auto;
  padding: 6px 4px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}

.add-item {
  display: flex;
  align-items: center;
  margin: 0;
}

.add-item :deep(.el-checkbox__label) {
  display: flex;
  align-items: center;
  gap: 6px;
}

.add-name {
  font-weight: 500;
  color: #303133;
}

.add-no {
  font-size: 12px;
  color: #909399;
}

.add-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.add-count {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
}

.save-state {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.save-state.saving {
  color: #909399;
}

.save-state.saving :deep(.is-loading) {
  animation: spin 1s linear infinite;
}

.save-state.saved {
  color: #67c23a;
  font-weight: 500;
  animation: fadeIn 0.2s ease;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

.muted {
  color: #c0c4cc;
  font-size: 13px;
}

.score-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.grade-tag {
  font-weight: 600;
  letter-spacing: 0.5px;
}
</style>
