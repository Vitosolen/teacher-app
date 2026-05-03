<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { classesApi } from '@/api/classes'
import type { ClassItem } from '@/types/domain'

const router = useRouter()
const classes = ref<ClassItem[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const newClass = ref({ name: '', grade: '' })

// 编辑弹窗
const editDialog = ref(false)
const editForm = ref({ id: 0, name: '', grade: '' })

async function load() {
  loading.value = true
  try {
    classes.value = await classesApi.list()
  } finally {
    loading.value = false
  }
}

async function createClass() {
  if (!newClass.value.name) {
    ElMessage.warning('班级名不能为空')
    return
  }
  await classesApi.create({ name: newClass.value.name, grade: newClass.value.grade })
  ElMessage.success('班级已创建')
  dialogVisible.value = false
  newClass.value = { name: '', grade: '' }
  await load()
}

function openEdit(c: ClassItem) {
  editForm.value = { id: c.id, name: c.name, grade: c.grade }
  editDialog.value = true
}

async function saveEdit() {
  if (!editForm.value.name.trim()) {
    ElMessage.warning('班级名不能为空')
    return
  }
  await classesApi.update(editForm.value.id, {
    name: editForm.value.name.trim(),
    grade: editForm.value.grade.trim(),
  })
  ElMessage.success('已保存')
  editDialog.value = false
  await load()
}

async function removeClass(c: ClassItem) {
  await ElMessageBox.confirm(`确认删除班级「${c.name}」？将连带删除班内所有学生与宠物。`, '危险操作', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
  await classesApi.remove(c.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">我的班级</h2>
      <el-button type="primary" @click="dialogVisible = true">+ 新建班级</el-button>
    </div>

    <el-empty v-if="!loading && classes.length === 0" description="还没有班级，点右上角创建" />

    <div class="class-grid" v-loading="loading">
      <el-card
        v-for="c in classes"
        :key="c.id"
        class="class-card"
        shadow="hover"
        @click="router.push({ name: 'class-detail', params: { id: c.id } })"
      >
        <div class="class-card-top">
          <span class="emoji">📚</span>
          <div>
            <el-button text size="small" @click.stop="openEdit(c)">编辑</el-button>
            <el-button text size="small" type="danger" @click.stop="removeClass(c)">删除</el-button>
          </div>
        </div>
        <div class="class-name">{{ c.name }}</div>
        <div class="class-meta">
          <span v-if="c.grade">{{ c.grade }} · </span>
          <span>{{ c.student_count }} 名学生</span>
        </div>
      </el-card>
    </div>

    <el-dialog v-model="dialogVisible" title="新建班级" width="400">
      <el-form :model="newClass" label-position="top">
        <el-form-item label="班级名">
          <el-input v-model="newClass.name" placeholder="例如：五年级三班" />
        </el-form-item>
        <el-form-item label="年级（可选）">
          <el-input v-model="newClass.grade" placeholder="例如：五年级" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createClass">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialog" title="编辑班级" width="400">
      <el-form label-position="top">
        <el-form-item label="班级名">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="年级">
          <el-input v-model="editForm.grade" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.class-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.class-card {
  cursor: pointer;
  transition: transform 0.15s;
}

.class-card:hover {
  transform: translateY(-2px);
}

.class-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.emoji {
  font-size: 32px;
}

.class-name {
  font-size: 18px;
  font-weight: 600;
  margin-top: 12px;
  color: #303133;
}

.class-meta {
  margin-top: 4px;
  color: #909399;
  font-size: 13px;
}
</style>
