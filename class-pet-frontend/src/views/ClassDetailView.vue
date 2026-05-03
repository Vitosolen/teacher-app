<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { studentsApi } from '@/api/students'
import { classesApi } from '@/api/classes'
import { behaviorsApi } from '@/api/behaviors'
import { scoreRulesApi } from '@/api/scoreRules'
import RandomPickDialog from '@/components/RandomPickDialog.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import { useEffectsStore } from '@/stores/effects'
import { showScoreUndoToast } from '@/composables/useScoreToast'
import type { Student, ClassItem, ScoreRule } from '@/types/domain'

const props = defineProps<{ id: string | number }>()
const router = useRouter()
const effects = useEffectsStore()

const classId = computed(() => Number(props.id))
const students = ref<Student[]>([])
const classInfo = ref<ClassItem | null>(null)
const rules = ref<ScoreRule[]>([])
const loading = ref(false)

// 添加学生弹窗
const addDialog = ref(false)
const addMode = ref<'single' | 'batch'>('single')
const singleForm = ref({ name: '', student_no: '' })
const batchText = ref('')

// 编辑学生弹窗
const editStudentDialog = ref(false)
const editStudentForm = ref({ id: 0, name: '', student_no: '' })

// 编辑班级弹窗
const editClassDialog = ref(false)
const editClassForm = ref({ name: '', grade: '' })

// 行内打分弹窗（单个 / 批量复用同一弹窗）
const scoreDialog = ref(false)
const scoreTarget = ref<Student | null>(null)   // 单选模式才用
const scoreType = ref<'positive' | 'negative'>('positive')

// —— 批量选择 ——
const selectionMode = ref(false)
const selectedIds = ref<Set<number>>(new Set())

function toggleSelectionMode() {
  selectionMode.value = !selectionMode.value
  if (!selectionMode.value) selectedIds.value = new Set()
}

function toggleSelect(s: Student) {
  if (selectedIds.value.has(s.id)) selectedIds.value.delete(s.id)
  else selectedIds.value.add(s.id)
  selectedIds.value = new Set(selectedIds.value)  // 触发响应
}

function selectAll() {
  selectedIds.value = new Set(students.value.map((s) => s.id))
}

function clearSelection() {
  selectedIds.value = new Set()
}

const selectedCount = computed(() => selectedIds.value.size)

function openBatchScore(type: 'positive' | 'negative') {
  if (selectedCount.value === 0) {
    ElMessage.warning('请先选择至少 1 名学生')
    return
  }
  scoreTarget.value = null   // null 表示批量模式
  scoreType.value = type
  scoreDialog.value = true
}

// 随机点名
const pickDialog = ref(false)

async function loadAll() {
  loading.value = true
  try {
    const [list, all, ruleList] = await Promise.all([
      studentsApi.listByClass(classId.value),
      classesApi.list(),
      scoreRulesApi.list(),
    ])
    students.value = list
    classInfo.value = all.find((c) => c.id === classId.value) ?? null
    rules.value = ruleList
  } finally {
    loading.value = false
  }
}

async function createSingle() {
  if (!singleForm.value.name.trim()) {
    ElMessage.warning('请输入姓名')
    return
  }
  await studentsApi.create(classId.value, {
    name: singleForm.value.name.trim(),
    student_no: singleForm.value.student_no.trim() || undefined,
  })
  ElMessage.success('已添加')
  addDialog.value = false
  singleForm.value = { name: '', student_no: '' }
  await loadAll()
}

async function createBatch() {
  const names = batchText.value
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter(Boolean)
  if (names.length === 0) {
    ElMessage.warning('请粘贴姓名（每行一个）')
    return
  }
  const created = await studentsApi.batchCreate(classId.value, names)
  ElMessage.success(`已批量添加 ${created.length} 名学生`)
  addDialog.value = false
  batchText.value = ''
  await loadAll()
}

function openEditStudent(s: Student) {
  editStudentForm.value = { id: s.id, name: s.name, student_no: s.student_no }
  editStudentDialog.value = true
}

async function saveEditStudent() {
  if (!editStudentForm.value.name.trim()) {
    ElMessage.warning('姓名不能为空')
    return
  }
  await studentsApi.update(editStudentForm.value.id, {
    name: editStudentForm.value.name.trim(),
    student_no: editStudentForm.value.student_no.trim(),
  })
  ElMessage.success('已保存')
  editStudentDialog.value = false
  await loadAll()
}

function openEditClass() {
  if (!classInfo.value) return
  editClassForm.value = {
    name: classInfo.value.name,
    grade: classInfo.value.grade,
  }
  editClassDialog.value = true
}

async function saveEditClass() {
  if (!editClassForm.value.name.trim()) {
    ElMessage.warning('班级名不能为空')
    return
  }
  const updated = await classesApi.update(classId.value, {
    name: editClassForm.value.name.trim(),
    grade: editClassForm.value.grade.trim(),
  })
  classInfo.value = updated
  ElMessage.success('已保存')
  editClassDialog.value = false
}

async function removeStudent(s: Student) {
  await ElMessageBox.confirm(`确认删除「${s.name}」？将连带删除其宠物与行为记录。`, '危险操作', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
  await studentsApi.remove(s.id)
  ElMessage.success('已删除')
  await loadAll()
}

function openScore(s: Student, type: 'positive' | 'negative') {
  scoreTarget.value = s
  scoreType.value = type
  scoreDialog.value = true
}

const rulesForType = computed(() =>
  rules.value.filter((r) => r.active && (scoreType.value === 'positive' ? r.score > 0 : r.score < 0))
)

async function applyRule(rule: ScoreRule) {
  // 单选 vs 批量
  if (scoreTarget.value) {
    // —— 单选模式 ——
    const target = scoreTarget.value
    const r = await behaviorsApi.create({
      student_id: target.id,
      score_rule_id: rule.id,
    })
    const idx = students.value.findIndex((s) => s.id === target.id)
    if (idx >= 0) {
      students.value[idx] = { ...students.value[idx], pet: r.pet, points: r.student_points }
    }
    if (r.leveled_up) {
      ElNotification({
        type: 'success',
        title: `🎉 ${target.name} 的宠物升级了！`,
        message: `升到 Lv.${r.pet.level}（+${r.levels_gained} 级），积分余额：${r.student_points}`,
        duration: 4000,
      })
      effects.fireConfetti(60)
    } else {
      // 普通打分：右下角撤回 toast
      showScoreUndoToast({
        studentName: target.name,
        ruleLabel: rule.label,
        score: rule.score,
        behaviorId: r.behavior.id,
        onUndo: () => loadAll(),
      })
    }
  } else {
    // —— 批量模式 ——
    const ids = [...selectedIds.value]
    if (ids.length === 0) return
    const r = await behaviorsApi.createBatch({
      student_ids: ids,
      score_rule_id: rule.id,
    })
    // 局部刷新所有受影响的学生
    const byId = new Map<number, typeof r.results[number]>()
    for (const item of r.results) byId.set(item.behavior.student_id, item)
    students.value = students.value.map((s) => {
      const upd = byId.get(s.id)
      if (!upd) return s
      return { ...s, pet: upd.pet, points: upd.student_points }
    })
    if (r.total_leveled_up > 0) {
      ElNotification({
        type: 'success',
        title: `🎉 ${r.total_leveled_up} 只宠物升级了！`,
        message: `给 ${r.total_students} 名学生应用「${rule.label} ${rule.score > 0 ? '+' : ''}${rule.score}」`,
        duration: 4000,
      })
      // 批量升级撒大花
      effects.fireConfetti(Math.min(120, 30 + r.total_leveled_up * 20))
    } else {
      ElMessage.success(`已批量应用「${rule.label}」给 ${r.total_students} 名学生`)
    }
    // 操作完默认清空选择 + 退出选择模式
    clearSelection()
  }
  scoreDialog.value = false
}

function statusTagType(status?: string) {
  switch (status) {
    case '健康': return 'success'
    case '饥饿': return 'warning'
    case '难过': return 'info'
    case '虚弱': return 'danger'
    default: return ''
  }
}

function onCardAction(cmd: string, s: Student) {
  if (cmd === 'edit') openEditStudent(s)
  else if (cmd === 'delete') removeStudent(s)
}

onMounted(loadAll)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <el-button text @click="router.push({ name: 'classes' })">← 返回</el-button>
        <h2 class="page-title" style="display: inline; margin-left: 8px">
          {{ classInfo?.name ?? '班级' }}
          <span class="meta" v-if="classInfo?.grade">· {{ classInfo.grade }}</span>
        </h2>
        <el-button
          v-if="classInfo"
          text
          size="small"
          type="primary"
          @click="openEditClass"
        >编辑</el-button>
      </div>
      <div class="header-actions">
        <el-button
          @click="router.push({ name: 'homeworks', query: { create: '1', class_id: classId } })"
        >📝 创建作业</el-button>
        <el-button
          @click="router.push({ name: 'exams', query: { create: '1', class_id: classId } })"
        >📊 登记成绩</el-button>
        <el-button
          @click="router.push({ name: 'classroom', params: { id: classId } })"
        >📺 课堂大屏</el-button>
        <el-button
          :type="selectionMode ? 'warning' : ''"
          :plain="!selectionMode"
          @click="toggleSelectionMode"
        >{{ selectionMode ? '✕ 退出多选' : '☑️ 多选打分' }}</el-button>
        <el-button @click="pickDialog = true">🎲 随机点名</el-button>
        <el-button type="primary" @click="addDialog = true">+ 添加学生</el-button>
      </div>
    </div>

    <!-- 多选模式工具栏（吸顶） -->
    <transition name="slide">
      <div v-if="selectionMode" class="batch-bar">
        <span class="batch-info">
          已选 <strong>{{ selectedCount }}</strong> / {{ students.length }} 名学生
        </span>
        <el-button size="small" text @click="selectAll">全选</el-button>
        <el-button size="small" text @click="clearSelection">清空</el-button>
        <div class="batch-spacer"></div>
        <el-button
          type="success"
          size="small"
          :disabled="selectedCount === 0"
          @click="openBatchScore('positive')"
        >+ 批量加分</el-button>
        <el-button
          type="danger"
          size="small"
          :disabled="selectedCount === 0"
          @click="openBatchScore('negative')"
        >- 批量减分</el-button>
      </div>
    </transition>

    <el-empty
      v-if="!loading && students.length === 0"
      description="还没有学生，点右上角添加"
    />

    <div v-else class="student-grid" v-loading="loading">
      <el-card
        v-for="s in students"
        :key="s.id"
        class="student-card"
        :class="{ selected: selectionMode && selectedIds.has(s.id), 'select-mode': selectionMode }"
        shadow="hover"
        :body-style="{ padding: 0 }"
        @click="selectionMode ? toggleSelect(s) : router.push({ name: 'student-detail', params: { id: s.id } })"
      >
        <!-- 多选模式：左上角 checkbox -->
        <div v-if="selectionMode" class="select-mark">
          <span class="check-circle" :class="{ checked: selectedIds.has(s.id) }">
            {{ selectedIds.has(s.id) ? '✓' : '' }}
          </span>
        </div>
        <!-- 顶部：宠物头像区 -->
        <div class="avatar-area" :class="{ adopted: !!s.pet }">
          <div class="avatar">
            <PetAvatar
              v-if="s.pet"
              :species="s.pet.species"
              :level="s.pet.level"
              :size="64"
            />
            <span v-else style="font-size: 64px">🐣</span>
          </div>
          <div v-if="s.pet" class="pet-meta">
            <el-tag size="small" effect="plain" round>Lv.{{ s.pet.level }}</el-tag>
            <el-tag
              size="small"
              :type="statusTagType(s.pet.status)"
              effect="light"
              round
            >{{ s.pet.status }}</el-tag>
          </div>
          <div v-else class="adopt-hint">
            <el-tag size="small" type="info" effect="plain">待领养</el-tag>
          </div>
        </div>

        <!-- 底部：信息列 + 操作 -->
        <div class="info-area">
          <div class="line-name">
            <span class="stu-name">{{ s.name }}的宠物</span>
            <span v-if="s.student_no" class="stu-no">#{{ s.student_no }}</span>
          </div>
          <div v-if="s.pet" class="line-pet">
            🐾 {{ s.pet.name }}
          </div>
          <div v-if="s.pet" class="line-bar">
            <span class="bar-label">心情</span>
            <el-progress
              :percentage="s.pet.mood"
              :stroke-width="6"
              color="#e6a23c"
              :show-text="false"
              class="bar"
            />
            <span class="bar-num">{{ s.pet.mood }}</span>
          </div>
          <div v-if="s.pet" class="line-bar">
            <span class="bar-label">饥饿</span>
            <el-progress
              :percentage="s.pet.hunger"
              :stroke-width="6"
              color="#67c23a"
              :show-text="false"
              class="bar"
            />
            <span class="bar-num">{{ s.pet.hunger }}</span>
          </div>
          <div class="line-points">
            💰 {{ s.points }} 积分
          </div>

          <div class="actions" @click.stop>
            <el-button
              type="success"
              size="small"
              plain
              @click="openScore(s, 'positive')"
            >+加分</el-button>
            <el-button
              type="danger"
              size="small"
              plain
              @click="openScore(s, 'negative')"
            >-减分</el-button>
            <el-dropdown trigger="click" @command="(c) => onCardAction(String(c), s)">
              <el-button size="small" text>更多</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">✏️ 编辑信息</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>🗑️ 删除学生</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 添加学生弹窗 -->
    <el-dialog v-model="addDialog" title="添加学生" width="480">
      <el-radio-group v-model="addMode" style="margin-bottom: 16px">
        <el-radio-button value="single">单个添加</el-radio-button>
        <el-radio-button value="batch">批量粘贴</el-radio-button>
      </el-radio-group>

      <el-form v-if="addMode === 'single'" label-position="top">
        <el-form-item label="姓名">
          <el-input v-model="singleForm.name" placeholder="例如：张三" />
        </el-form-item>
        <el-form-item label="学号（可选）">
          <el-input v-model="singleForm.student_no" placeholder="例如：001" />
        </el-form-item>
      </el-form>

      <el-form v-else label-position="top">
        <el-form-item label="姓名（每行一个）">
          <el-input
            v-model="batchText"
            type="textarea"
            :rows="8"
            placeholder="张三&#10;李四&#10;王五"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="addMode === 'single' ? createSingle() : createBatch()"
        >确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑学生弹窗 -->
    <el-dialog v-model="editStudentDialog" title="编辑学生" width="400">
      <el-form label-position="top">
        <el-form-item label="姓名">
          <el-input v-model="editStudentForm.name" />
        </el-form-item>
        <el-form-item label="学号">
          <el-input v-model="editStudentForm.student_no" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editStudentDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEditStudent">保存</el-button>
      </template>
    </el-dialog>

    <!-- 编辑班级弹窗 -->
    <el-dialog v-model="editClassDialog" title="编辑班级" width="400">
      <el-form label-position="top">
        <el-form-item label="班级名">
          <el-input v-model="editClassForm.name" />
        </el-form-item>
        <el-form-item label="年级">
          <el-input v-model="editClassForm.grade" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editClassDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEditClass">保存</el-button>
      </template>
    </el-dialog>

    <!-- 打分弹窗：单选 / 批量复用 -->
    <el-dialog
      v-model="scoreDialog"
      :title="scoreTarget
        ? `${scoreTarget.name} · ${scoreType === 'positive' ? '奖励' : '提醒'}`
        : `批量${scoreType === 'positive' ? '加分' : '减分'} · 已选 ${selectedCount} 名学生`"
      width="460"
    >
      <el-empty v-if="rulesForType.length === 0" description="还没有此类规则，请在「积分规则」页配置" />
      <div v-else class="preset-grid">
        <el-button
          v-for="r in rulesForType"
          :key="r.id"
          :type="scoreType === 'positive' ? 'success' : 'danger'"
          plain
          @click="applyRule(r)"
        >
          {{ r.label }} {{ r.score >= 0 ? '+' : '' }}{{ r.score }}
        </el-button>
      </div>
      <div class="dialog-tip">
        点击按钮立即应用并关闭。详情页可填自定义分数。
      </div>
    </el-dialog>

    <!-- 随机点名 -->
    <RandomPickDialog
      v-model="pickDialog"
      :class-id="classId"
      :students-count="students.length"
    />
  </div>
</template>

<style scoped>
.meta {
  color: #909399;
  font-size: 14px;
  font-weight: normal;
  margin-left: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.muted {
  color: #c0c4cc;
  font-size: 13px;
}

/* —— 学生卡片网格 —— */
.student-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.student-card {
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.15s, box-shadow 0.15s;
}

.student-card:hover {
  transform: translateY(-3px);
}

.student-card.select-mode {
  cursor: pointer;
}

.student-card.selected {
  outline: 3px solid #409eff;
  outline-offset: -3px;
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.3);
}

.select-mark {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
}

.check-circle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid #c0c4cc;
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  transition: all 0.15s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.check-circle.checked {
  background: #409eff;
  border-color: #409eff;
}

.batch-bar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(90deg, #fef9e7 0%, #fff3d6 100%);
  border: 1px solid #faecd8;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(230, 162, 60, 0.15);
}

.batch-info {
  font-size: 14px;
  color: #303133;
}

.batch-info strong {
  color: #e6a23c;
  font-size: 16px;
  margin: 0 2px;
}

.batch-spacer {
  flex: 1;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.avatar-area {
  background: linear-gradient(135deg, #f4f6fa 0%, #ebeef5 100%);
  padding: 20px 12px 12px;
  text-align: center;
  border-bottom: 1px solid #ebeef5;
}

.avatar-area.adopted {
  background: linear-gradient(135deg, #fef9e7 0%, #fff3d6 100%);
}

.avatar {
  font-size: 64px;
  line-height: 1;
  filter: drop-shadow(0 3px 4px rgba(0, 0, 0, 0.18));
  margin-bottom: 8px;
}

.pet-meta {
  display: flex;
  justify-content: center;
  gap: 6px;
  flex-wrap: wrap;
}

.adopt-hint {
  margin-top: 4px;
}

.info-area {
  padding: 12px 14px 10px;
  font-size: 13px;
}

.line-name {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
}

.stu-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.stu-no {
  color: #909399;
  font-size: 12px;
}

.line-pet {
  color: #606266;
  margin-bottom: 8px;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.line-bar {
  display: grid;
  grid-template-columns: 32px 1fr 28px;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.bar-label {
  font-size: 11px;
  color: #909399;
}

.bar-num {
  font-size: 11px;
  color: #606266;
  text-align: right;
}

.line-points {
  color: #e6a23c;
  font-weight: 600;
  margin-top: 6px;
  margin-bottom: 8px;
}

.actions {
  display: flex;
  gap: 4px;
  align-items: center;
  border-top: 1px dashed #ebeef5;
  padding-top: 8px;
}

.actions .el-button + .el-button {
  margin-left: 0;
}

.preset-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.dialog-tip {
  margin-top: 12px;
  color: #909399;
  font-size: 12px;
}
</style>
