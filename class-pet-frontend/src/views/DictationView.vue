<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { wordsApi } from '@/api/words'
import type { WordGroup } from '@/types/domain'

const router = useRouter()
const groups = ref<WordGroup[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref({
  id: 0,
  name: '',
  description: '',
  lang: 'en-US',
  sort_order: 0,
})

const LANG_OPTIONS = [
  { label: '英语 (美式)', value: 'en-US' },
  { label: '英语 (英式)', value: 'en-GB' },
  { label: '中文', value: 'zh-CN' },
  { label: '日语', value: 'ja-JP' },
  { label: '法语', value: 'fr-FR' },
  { label: '德语', value: 'de-DE' },
]

async function load() {
  loading.value = true
  try {
    groups.value = await wordsApi.listGroups()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  isEdit.value = false
  form.value = { id: 0, name: '', description: '', lang: 'en-US', sort_order: groups.value.length }
  dialogVisible.value = true
}

function openEdit(g: WordGroup) {
  isEdit.value = true
  form.value = {
    id: g.id, name: g.name, description: g.description,
    lang: g.lang, sort_order: g.sort_order,
  }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.name.trim()) {
    ElMessage.warning('词库名不能为空')
    return
  }
  if (isEdit.value) {
    await wordsApi.updateGroup(form.value.id, {
      name: form.value.name.trim(),
      description: form.value.description,
      lang: form.value.lang,
      sort_order: form.value.sort_order,
    })
    ElMessage.success('已保存')
  } else {
    await wordsApi.createGroup({
      name: form.value.name.trim(),
      description: form.value.description,
      lang: form.value.lang,
      sort_order: form.value.sort_order,
    })
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  await load()
}

async function remove(g: WordGroup) {
  await ElMessageBox.confirm(`确认删除词库「${g.name}」？将连带删除其中所有单词。`, '危险操作', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
  await wordsApi.removeGroup(g.id)
  ElMessage.success('已删除')
  await load()
}

function langLabel(code: string) {
  return LANG_OPTIONS.find((o) => o.value === code)?.label ?? code
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">📢 单词听写</h2>
      <el-button type="primary" @click="openCreate">+ 新建词库</el-button>
    </div>

    <p class="hint">
      在这里维护单词词库，进入词库后可批量导入单词、并启动语音听写（基于浏览器语音合成）。
    </p>

    <el-empty v-if="!loading && groups.length === 0" description="还没有词库，先新建一个" />

    <div class="grid" v-loading="loading">
      <el-card
        v-for="g in groups"
        :key="g.id"
        class="card"
        shadow="hover"
        :body-style="{ padding: 0 }"
      >
        <div class="card-header" @click="router.push({ name: 'word-group-detail', params: { id: g.id } })">
          <div class="title-row">
            <span class="emoji">📚</span>
            <span class="name">{{ g.name }}</span>
          </div>
          <div class="meta">
            <el-tag size="small" effect="plain">{{ langLabel(g.lang) }}</el-tag>
            <el-tag size="small" type="info" effect="plain">{{ g.word_count }} 词</el-tag>
          </div>
          <div class="desc" v-if="g.description">{{ g.description }}</div>
        </div>
        <div class="card-actions">
          <el-button text size="small" @click="openEdit(g)">编辑</el-button>
          <el-button text size="small" type="danger" @click="remove(g)">删除</el-button>
        </div>
      </el-card>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑词库' : '新建词库'"
      width="440"
    >
      <el-form label-position="top">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="例如：五年级上册 Unit 3" />
        </el-form-item>
        <el-form-item label="说明（可选）">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="朗读语言">
          <el-select v-model="form.lang" style="width: 100%">
            <el-option
              v-for="o in LANG_OPTIONS"
              :key="o.value"
              :label="o.label"
              :value="o.value"
            />
          </el-select>
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
.hint {
  background: #f4f6fa;
  color: #606266;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 24px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.card {
  cursor: pointer;
  transition: transform 0.15s;
  overflow: hidden;
}

.card:hover {
  transform: translateY(-2px);
}

.card-header {
  padding: 16px 16px 8px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.emoji {
  font-size: 28px;
}

.name {
  font-size: 17px;
  font-weight: 600;
  color: #303133;
}

.meta {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.desc {
  font-size: 12px;
  color: #909399;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 28px;
}

.card-actions {
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: flex-end;
  padding: 6px 12px;
}
</style>
