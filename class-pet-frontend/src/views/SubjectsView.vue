<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { subjectsApi } from '@/api/subjects'
import type { Subject } from '@/types/domain'

const subjects = ref<Subject[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref({ id: 0, name: '', color: '#409EFF', sort_order: 0 })

const PRESET_COLORS = [
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C',
  '#909399', '#9C27B0', '#FF6F61', '#26A69A',
]

async function load() {
  loading.value = true
  try {
    subjects.value = await subjectsApi.list()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  isEdit.value = false
  form.value = { id: 0, name: '', color: PRESET_COLORS[0], sort_order: subjects.value.length }
  dialogVisible.value = true
}

function openEdit(s: Subject) {
  isEdit.value = true
  form.value = { id: s.id, name: s.name, color: s.color, sort_order: s.sort_order }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.name.trim()) {
    ElMessage.warning('科目名不能为空')
    return
  }
  if (isEdit.value) {
    await subjectsApi.update(form.value.id, {
      name: form.value.name.trim(),
      color: form.value.color,
      sort_order: form.value.sort_order,
    })
    ElMessage.success('已保存')
  } else {
    await subjectsApi.create({
      name: form.value.name.trim(),
      color: form.value.color,
      sort_order: form.value.sort_order,
    })
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  await load()
}

async function remove(s: Subject) {
  await ElMessageBox.confirm(`确认删除科目「${s.name}」？该科目下的作业也会被删除。`, '危险操作', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
  await subjectsApi.remove(s.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">科目管理</h2>
      <el-button type="primary" @click="openCreate">+ 新建科目</el-button>
    </div>

    <el-empty v-if="!loading && subjects.length === 0" description="还没有科目，先新建一个" />

    <div class="subject-grid" v-loading="loading">
      <el-card
        v-for="s in subjects"
        :key="s.id"
        class="subject-card"
        shadow="hover"
        :body-style="{ padding: 0 }"
      >
        <div class="color-bar" :style="{ background: s.color }"></div>
        <div class="card-body">
          <div class="subject-name">{{ s.name }}</div>
          <div class="card-actions">
            <el-button text size="small" @click="openEdit(s)">编辑</el-button>
            <el-button text size="small" type="danger" @click="remove(s)">删除</el-button>
          </div>
        </div>
      </el-card>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑科目' : '新建科目'"
      width="400"
    >
      <el-form label-position="top">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="例如：语文" />
        </el-form-item>
        <el-form-item label="颜色">
          <div class="color-picker">
            <div
              v-for="c in PRESET_COLORS"
              :key="c"
              class="color-dot"
              :class="{ active: form.color === c }"
              :style="{ background: c }"
              @click="form.color = c"
            ></div>
          </div>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.subject-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.subject-card {
  overflow: hidden;
  transition: transform 0.15s;
}

.subject-card:hover {
  transform: translateY(-2px);
}

.color-bar {
  height: 8px;
}

.card-body {
  padding: 16px;
}

.subject-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
}

.color-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.color-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: transform 0.1s;
}

.color-dot:hover {
  transform: scale(1.1);
}

.color-dot.active {
  border-color: #303133;
  box-shadow: 0 0 0 2px white inset;
}
</style>
