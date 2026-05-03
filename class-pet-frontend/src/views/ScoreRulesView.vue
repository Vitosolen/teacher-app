<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { scoreRulesApi } from '@/api/scoreRules'
import type { ScoreRule } from '@/types/domain'

const rules = ref<ScoreRule[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref({
  id: 0,
  label: '',
  category: '学习',
  score: 1,
  sort_order: 0,
  active: true,
})

const positives = computed(() => rules.value.filter((r) => r.score > 0))
const negatives = computed(() => rules.value.filter((r) => r.score < 0))

async function load() {
  loading.value = true
  try {
    rules.value = await scoreRulesApi.list()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  isEdit.value = false
  form.value = {
    id: 0, label: '', category: '学习', score: 1,
    sort_order: rules.value.length, active: true,
  }
  dialogVisible.value = true
}

function openEdit(r: ScoreRule) {
  isEdit.value = true
  form.value = {
    id: r.id, label: r.label, category: r.category,
    score: r.score, sort_order: r.sort_order, active: r.active,
  }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.label.trim()) {
    ElMessage.warning('规则名不能为空')
    return
  }
  if (form.value.score === 0) {
    ElMessage.warning('分数不能为 0')
    return
  }
  if (isEdit.value) {
    await scoreRulesApi.update(form.value.id, { ...form.value, label: form.value.label.trim() })
    ElMessage.success('已保存')
  } else {
    await scoreRulesApi.create({ ...form.value, label: form.value.label.trim() })
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  await load()
}

async function toggleActive(r: ScoreRule) {
  await scoreRulesApi.update(r.id, { active: !r.active })
  await load()
}

async function remove(r: ScoreRule) {
  await ElMessageBox.confirm(`确认删除规则「${r.label}」？`, '提示', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
  await scoreRulesApi.remove(r.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">积分规则</h2>
      <el-button type="primary" @click="openCreate">+ 新建规则</el-button>
    </div>

    <p class="hint">
      这里配置打分按钮。新规则即时生效到「班级」「学生详情」打分面板。
      ✅ 加分会累加学生「积分余额」（用来兑换商品）；扣分仅影响宠物属性。
    </p>

    <div v-loading="loading">
      <h3 class="section-title">👍 奖励规则（{{ positives.length }}）</h3>
      <el-table :data="positives" stripe>
        <el-table-column prop="label" label="名称" min-width="160" />
        <el-table-column prop="category" label="类别" width="100" />
        <el-table-column label="分数" width="100">
          <template #default="{ row }">
            <el-tag type="success">+{{ row.score }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="启用" width="100">
          <template #default="{ row }">
            <el-switch :model-value="row.active" @change="toggleActive(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text @click="openEdit(row)">编辑</el-button>
            <el-button size="small" text type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <h3 class="section-title">⚠️ 提醒规则（{{ negatives.length }}）</h3>
      <el-table :data="negatives" stripe>
        <el-table-column prop="label" label="名称" min-width="160" />
        <el-table-column prop="category" label="类别" width="100" />
        <el-table-column label="分数" width="100">
          <template #default="{ row }">
            <el-tag type="danger">{{ row.score }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="启用" width="100">
          <template #default="{ row }">
            <el-switch :model-value="row.active" @change="toggleActive(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text @click="openEdit(row)">编辑</el-button>
            <el-button size="small" text type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑规则' : '新建规则'"
      width="440"
    >
      <el-form label-position="top">
        <el-form-item label="名称">
          <el-input v-model="form.label" placeholder="例如：考试 90 以上" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="form.category" style="width: 100%">
            <el-option label="学习" value="学习" />
            <el-option label="纪律" value="纪律" />
            <el-option label="积极" value="积极" />
            <el-option label="消极" value="消极" />
          </el-select>
        </el-form-item>
        <el-form-item label="分数（-100 到 +100，正数为奖励，负数为提醒）">
          <el-input-number v-model="form.score" :min="-100" :max="100" :step="1" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item>
          <el-switch v-model="form.active" /> &nbsp;启用
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
  color: #606266;
  background: #f4f6fa;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  font-size: 13px;
}

.section-title {
  margin: 24px 0 12px;
  font-size: 16px;
  color: #303133;
}
</style>
