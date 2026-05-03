<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as XLSX from 'xlsx'
import type { UploadRawFile } from 'element-plus'
import { wordsApi } from '@/api/words'
import DictationPlayer from '@/components/DictationPlayer.vue'
import type { WordGroupDetail, Word } from '@/types/domain'

const props = defineProps<{ id: string | number }>()
const router = useRouter()

const groupId = computed(() => Number(props.id))
const group = ref<WordGroupDetail | null>(null)
const loading = ref(false)

// 添加 / 批量
const addDialog = ref(false)
const addMode = ref<'single' | 'batch' | 'excel'>('single')
const singleForm = ref({ text: '', translation: '' })
const batchText = ref('')

// Excel 导入
interface ExcelRow {
  text: string
  translation: string
}
const excelRows = ref<ExcelRow[]>([])
const excelFileName = ref('')
const excelImporting = ref(false)

// 编辑单词
const editDialog = ref(false)
const editForm = ref({ id: 0, text: '', translation: '' })

// 听写
const dictationVisible = ref(false)

async function load() {
  loading.value = true
  try {
    group.value = await wordsApi.getGroup(groupId.value)
  } finally {
    loading.value = false
  }
}

async function createSingle() {
  if (!singleForm.value.text.trim()) {
    ElMessage.warning('请输入单词')
    return
  }
  await wordsApi.createWord(groupId.value, {
    text: singleForm.value.text.trim(),
    translation: singleForm.value.translation.trim(),
  })
  ElMessage.success('已添加')
  addDialog.value = false
  singleForm.value = { text: '', translation: '' }
  await load()
}

async function createBatch() {
  const lines = batchText.value
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter(Boolean)
  if (lines.length === 0) {
    ElMessage.warning('请粘贴单词（每行一条）')
    return
  }
  const created = await wordsApi.batchCreateWords(groupId.value, lines)
  ElMessage.success(`已批量导入 ${created.length} 个单词`)
  addDialog.value = false
  batchText.value = ''
  await load()
}

// 解析 Excel：第 1 列单词，第 2 列释义；自动识别表头并跳过
async function parseExcel(file: UploadRawFile) {
  try {
    const buf = await file.arrayBuffer()
    const wb = XLSX.read(buf, { type: 'array' })
    const sheet = wb.Sheets[wb.SheetNames[0]]
    if (!sheet) {
      ElMessage.error('Excel 没有工作表')
      return false
    }
    // header: 1 → 返回二维数组（首行包含），便于判断表头
    const rows: unknown[][] = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' })
    if (rows.length === 0) {
      ElMessage.warning('Excel 内容为空')
      return false
    }
    // 表头识别：第 1 行第 1 列含「单词/word」类关键词则跳过
    const firstCell = String(rows[0][0] ?? '').trim().toLowerCase()
    const headerKeywords = ['单词', '词汇', 'word', 'words', 'vocabulary', '英语']
    const dataStart = headerKeywords.some((k) => firstCell.includes(k.toLowerCase())) ? 1 : 0

    const parsed: ExcelRow[] = []
    for (let i = dataStart; i < rows.length; i++) {
      const row = rows[i]
      const text = String(row?.[0] ?? '').trim()
      const translation = String(row?.[1] ?? '').trim()
      if (!text) continue
      parsed.push({ text, translation })
    }
    if (parsed.length === 0) {
      ElMessage.warning('Excel 中没有有效单词')
      return false
    }
    excelRows.value = parsed
    excelFileName.value = file.name
    return false  // 阻止 el-upload 自动上传，自己处理
  } catch (e) {
    ElMessage.error('解析 Excel 失败：' + (e instanceof Error ? e.message : String(e)))
    return false
  }
}

async function confirmExcelImport() {
  if (excelRows.value.length === 0) {
    ElMessage.warning('请先选择 Excel 文件')
    return
  }
  excelImporting.value = true
  try {
    // 把 {text, translation} 拼成 batch 接口认的格式
    const lines = excelRows.value.map((r) =>
      r.translation ? `${r.text}\t${r.translation}` : r.text,
    )
    const created = await wordsApi.batchCreateWords(groupId.value, lines)
    ElMessage.success(`已从 Excel 导入 ${created.length} 个单词`)
    addDialog.value = false
    resetExcel()
    await load()
  } finally {
    excelImporting.value = false
  }
}

function resetExcel() {
  excelRows.value = []
  excelFileName.value = ''
}

function openEdit(w: Word) {
  editForm.value = { id: w.id, text: w.text, translation: w.translation }
  editDialog.value = true
}

async function saveEdit() {
  if (!editForm.value.text.trim()) {
    ElMessage.warning('单词不能为空')
    return
  }
  await wordsApi.updateWord(editForm.value.id, {
    text: editForm.value.text.trim(),
    translation: editForm.value.translation.trim(),
  })
  ElMessage.success('已保存')
  editDialog.value = false
  await load()
}

async function remove(w: Word) {
  await ElMessageBox.confirm(`确认删除「${w.text}」？`, '提示', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
  await wordsApi.removeWord(w.id)
  ElMessage.success('已删除')
  await load()
}

function startDictation() {
  if (!group.value || group.value.words.length === 0) {
    ElMessage.warning('词库里还没有单词，请先添加')
    return
  }
  dictationVisible.value = true
}

onMounted(load)
</script>

<template>
  <div class="page" v-loading="loading">
    <div class="page-header">
      <div>
        <el-button text @click="router.push({ name: 'dictation' })">← 返回词库列表</el-button>
        <h2 class="page-title" style="display: inline; margin-left: 8px">
          📚 {{ group?.name ?? '词库' }}
        </h2>
        <el-tag v-if="group" size="small" effect="plain" style="margin-left: 8px">
          {{ group.lang }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button type="success" @click="startDictation">📢 开始听写</el-button>
        <el-button type="primary" @click="addDialog = true">+ 添加单词</el-button>
      </div>
    </div>

    <p v-if="group?.description" class="desc-bar">{{ group.description }}</p>

    <el-empty v-if="!loading && group?.words.length === 0" description="还没有单词，点右上角添加" />

    <el-table v-else :data="group?.words ?? []" stripe>
      <el-table-column type="index" label="#" width="60" />
      <el-table-column prop="text" label="单词" min-width="160">
        <template #default="{ row }">
          <span class="word-text">{{ row.text }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="translation" label="释义" min-width="160" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button text size="small" @click="openEdit(row)">编辑</el-button>
          <el-button text size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加单词 -->
    <el-dialog v-model="addDialog" title="添加单词" width="560" @close="resetExcel">
      <el-radio-group v-model="addMode" style="margin-bottom: 16px">
        <el-radio-button value="single">单条添加</el-radio-button>
        <el-radio-button value="batch">批量粘贴</el-radio-button>
        <el-radio-button value="excel">📊 Excel 导入</el-radio-button>
      </el-radio-group>

      <el-form v-if="addMode === 'single'" label-position="top">
        <el-form-item label="单词">
          <el-input v-model="singleForm.text" placeholder="例如：apple" />
        </el-form-item>
        <el-form-item label="释义（可选）">
          <el-input v-model="singleForm.translation" placeholder="例如：苹果" />
        </el-form-item>
      </el-form>

      <el-form v-else-if="addMode === 'batch'" label-position="top">
        <el-form-item label="每行一条，可只写单词，也可空格/逗号分隔写释义">
          <el-input
            v-model="batchText"
            type="textarea"
            :rows="10"
            placeholder="apple 苹果&#10;banana 香蕉&#10;cat&#10;dog,狗"
          />
        </el-form-item>
      </el-form>

      <div v-else>
        <p class="excel-tip">
          上传 .xlsx 或 .xls 文件。<strong>第 1 列</strong>为单词，<strong>第 2 列</strong>为释义（可选）。
          含表头会自动跳过。
        </p>
        <el-upload
          v-if="excelRows.length === 0"
          drag
          accept=".xlsx,.xls"
          :auto-upload="false"
          :show-file-list="false"
          :before-upload="parseExcel"
        >
          <el-icon class="el-icon--upload"><svg viewBox="0 0 24 24" width="42" height="42"><path fill="#c0c4cc" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6m4 18H6V4h7v5h5v11Z"/></svg></el-icon>
          <div class="el-upload__text">
            将 Excel 拖到此处，或<em>点击选择</em>
          </div>
        </el-upload>

        <div v-else class="excel-preview">
          <div class="preview-bar">
            <span>📄 {{ excelFileName }} · 共 <b>{{ excelRows.length }}</b> 条</span>
            <el-button text size="small" type="danger" @click="resetExcel">重选</el-button>
          </div>
          <el-table :data="excelRows.slice(0, 10)" stripe size="small">
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="text" label="单词" />
            <el-table-column prop="translation" label="释义" />
          </el-table>
          <div v-if="excelRows.length > 10" class="more-tip">
            … 还有 {{ excelRows.length - 10 }} 条未展示
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="addDialog = false">取消</el-button>
        <el-button
          v-if="addMode === 'single'"
          type="primary"
          @click="createSingle"
        >确定</el-button>
        <el-button
          v-else-if="addMode === 'batch'"
          type="primary"
          @click="createBatch"
        >确定</el-button>
        <el-button
          v-else
          type="primary"
          :disabled="excelRows.length === 0"
          :loading="excelImporting"
          @click="confirmExcelImport"
        >导入 {{ excelRows.length }} 条</el-button>
      </template>
    </el-dialog>

    <!-- 编辑单词 -->
    <el-dialog v-model="editDialog" title="编辑单词" width="400">
      <el-form label-position="top">
        <el-form-item label="单词">
          <el-input v-model="editForm.text" />
        </el-form-item>
        <el-form-item label="释义">
          <el-input v-model="editForm.translation" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 听写播放器 -->
    <DictationPlayer
      v-if="group"
      v-model="dictationVisible"
      :words="group.words"
      :group-name="group.name"
      :lang="group.lang"
    />
  </div>
</template>

<style scoped>
.header-actions {
  display: flex;
  gap: 8px;
}

.desc-bar {
  background: #f4f6fa;
  color: #606266;
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 16px;
}

.word-text {
  font-weight: 500;
  color: #303133;
}

.excel-tip {
  color: #606266;
  background: #f4f6fa;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  margin: 0 0 12px;
}

.excel-tip strong {
  color: #303133;
}

.excel-preview {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
}

.preview-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: #303133;
}

.more-tip {
  text-align: center;
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}
</style>
