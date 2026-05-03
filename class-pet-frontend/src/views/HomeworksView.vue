<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { homeworksApi } from '@/api/homeworks'
import { classesApi } from '@/api/classes'
import { subjectsApi } from '@/api/subjects'
import type { Homework, ClassItem, Subject } from '@/types/domain'

// 复用同一组件服务两种场景：作业 / 成绩
const props = withDefaults(defineProps<{ type?: 'homework' | 'exam' }>(), {
  type: 'homework',
})

const isExam = computed(() => props.type === 'exam')
const titleText = computed(() => isExam.value ? '成绩管理' : '作业管理')
const itemText = computed(() => isExam.value ? '成绩' : '作业')
const createBtnText = computed(() => isExam.value ? '+ 登记成绩' : '+ 创建作业')

const router = useRouter()
const route = useRoute()
const homeworks = ref<Homework[]>([])
const classes = ref<ClassItem[]>([])
const subjects = ref<Subject[]>([])
const loading = ref(false)

const filterClassId = ref<number | undefined>(undefined)
const filterSubjectId = ref<number | undefined>(undefined)

const dialogVisible = ref(false)
const form = ref({
  class_id: undefined as number | undefined,
  subject_id: undefined as number | undefined,
  title: '',
  content: '',
  due_date: null as string | null,
})

async function load() {
  loading.value = true
  try {
    homeworks.value = await homeworksApi.list({
      class_id: filterClassId.value,
      subject_id: filterSubjectId.value,
      type: props.type,
    })
  } finally {
    loading.value = false
  }
}

async function loadMeta() {
  const [c, s] = await Promise.all([classesApi.list(), subjectsApi.list()])
  classes.value = c
  subjects.value = s
}

async function refresh() {
  await loadMeta()
  await load()
}

async function openCreate() {
  if (classes.value.length === 0) {
    try {
      await ElMessageBox.confirm(
        `还没有班级。需要先创建班级（含学生）才能${isExam.value ? '登记成绩' : '创建作业'}，是否前往？`,
        '提示',
        { confirmButtonText: '去创建班级', cancelButtonText: '取消', type: 'info' },
      )
      router.push({ name: 'classes' })
    } catch {/* 用户取消 */}
    return
  }
  if (subjects.value.length === 0) {
    try {
      await ElMessageBox.confirm(
        `还没有科目。${isExam.value ? '成绩' : '作业'}需要选择所属科目，是否前往创建？`,
        '提示',
        { confirmButtonText: '去创建科目', cancelButtonText: '取消', type: 'info' },
      )
      router.push({ name: 'subjects' })
    } catch {/* 用户取消 */}
    return
  }
  form.value = {
    class_id: classes.value[0]?.id,
    subject_id: subjects.value[0]?.id,
    title: '',
    content: '',
    due_date: null,
  }
  dialogVisible.value = true
}

async function create() {
  if (!form.value.class_id || !form.value.subject_id) {
    ElMessage.warning('请选择班级和科目')
    return
  }
  if (!form.value.title.trim()) {
    ElMessage.warning('请填写作业标题')
    return
  }
  await homeworksApi.create({
    class_id: form.value.class_id,
    subject_id: form.value.subject_id,
    type: props.type,
    title: form.value.title.trim(),
    content: form.value.content,
    due_date: isExam.value ? null : form.value.due_date,
  })
  ElMessage.success(`${itemText.value}已创建，并已自动绑定全班学生`)
  dialogVisible.value = false
  await load()
}

async function remove(h: Homework) {
  await ElMessageBox.confirm(`确认删除${itemText.value}「${h.title}」？将连带删除所有学生记录。`, '危险操作', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
  await homeworksApi.remove(h.id)
  ElMessage.success('已删除')
  await load()
}

const progressPercent = (h: Homework) =>
  h.total_count > 0 ? Math.round((h.graded_count / h.total_count) * 100) : 0

onMounted(async () => {
  await refresh()
  // 从班级页带 ?create=1&class_id=X 跳过来：自动打开创建弹窗 + 预填班级
  if (route.query.create === '1') {
    const queryClassId = Number(route.query.class_id)
    if (classes.value.length === 0) {
      ElMessage.warning('还没有班级')
      return
    }
    if (subjects.value.length === 0) {
      ElMessageBox.confirm(
        `还没有科目。${isExam.value ? '成绩' : '作业'}需要选择所属科目，是否前往创建？`,
        '提示',
        { confirmButtonText: '去创建科目', cancelButtonText: '取消', type: 'info' },
      ).then(() => router.push({ name: 'subjects' })).catch(() => {})
      return
    }
    form.value = {
      class_id: queryClassId && classes.value.some((c) => c.id === queryClassId)
        ? queryClassId
        : classes.value[0].id,
      subject_id: subjects.value[0].id,
      title: '',
      content: '',
      due_date: null,
    }
    dialogVisible.value = true
    // 清掉 query 防止刷新或返回时重复弹
    router.replace({ query: {} })
  }
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">{{ titleText }}</h2>
      <el-button type="primary" @click="openCreate">{{ createBtnText }}</el-button>
    </div>

    <div class="filters">
      <el-select
        v-model="filterClassId"
        placeholder="按班级过滤"
        clearable
        style="width: 200px"
        @change="load"
      >
        <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-select
        v-model="filterSubjectId"
        placeholder="按科目过滤"
        clearable
        style="width: 200px"
        @change="load"
      >
        <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
    </div>

    <el-empty v-if="!loading && homeworks.length === 0" :description="`还没有${itemText}`" />

    <div class="hw-grid" v-loading="loading">
      <el-card
        v-for="h in homeworks"
        :key="h.id"
        class="hw-card"
        shadow="hover"
        :body-style="{ padding: 0 }"
        @click="router.push({ name: isExam ? 'exam-detail' : 'homework-detail', params: { id: h.id } })"
      >
        <div class="color-bar" :style="{ background: h.subject_color }"></div>
        <div class="card-body">
          <div class="hw-tags">
            <el-tag size="small" :style="{ background: h.subject_color, color: '#fff', borderColor: 'transparent' }">
              {{ h.subject_name }}
            </el-tag>
            <el-tag size="small" effect="plain">{{ h.class_name }}</el-tag>
          </div>
          <div class="hw-title">{{ h.title }}</div>
          <div class="hw-content" v-if="h.content">{{ h.content }}</div>
          <div class="hw-progress">
            <span class="progress-label">{{ isExam ? '登记进度' : '批改进度' }}</span>
            <el-progress
              :percentage="progressPercent(h)"
              :stroke-width="8"
              :format="() => `${h.graded_count}/${h.total_count}`"
            />
          </div>
          <div v-if="!isExam && h.correction_pending_count > 0" class="correction-tip">
            ⚠️ {{ h.correction_pending_count }} 名学生待订正
          </div>
          <div class="card-actions" @click.stop>
            <el-button text size="small" type="danger" @click="remove(h)">删除</el-button>
          </div>
        </div>
      </el-card>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isExam ? '登记成绩' : '创建作业'"
      width="500"
    >
      <el-form label-position="top">
        <el-form-item label="班级">
          <el-select v-model="form.class_id" style="width: 100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="科目">
          <el-select v-model="form.subject_id" style="width: 100%">
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="isExam ? '名称（如：2025 期中考）' : '标题'">
          <el-input
            v-model="form.title"
            :placeholder="isExam ? '例如：2025 期中考、第 3 单元测验' : '例如：作文 500 字'"
          />
        </el-form-item>
        <el-form-item v-if="!isExam" label="内容（可选）">
          <el-input v-model="form.content" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item v-if="isExam" label="备注（可选）">
          <el-input v-model="form.content" type="textarea" :rows="2" placeholder="例如：满分 100，含选择题与作文" />
        </el-form-item>
        <el-form-item v-if="!isExam" label="截止日期（可选）">
          <el-date-picker v-model="form.due_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="create">{{ isExam ? '登记' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.hw-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.hw-card {
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.15s;
}

.hw-card:hover {
  transform: translateY(-2px);
}

.color-bar {
  height: 6px;
}

.card-body {
  padding: 16px;
}

.hw-tags {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.hw-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}

.hw-content {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hw-progress {
  margin: 12px 0 4px;
}

.correction-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #e6a23c;
  background: #fdf6ec;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}

.progress-label {
  font-size: 12px;
  color: #909399;
  display: block;
  margin-bottom: 4px;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
</style>
