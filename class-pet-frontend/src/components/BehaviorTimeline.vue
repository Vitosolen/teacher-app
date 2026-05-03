<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { behaviorsApi } from '@/api/behaviors'
import { fmtDateTime } from '@/utils/datetime'
import type { Behavior } from '@/types/domain'

defineProps<{ behaviors: Behavior[] }>()
const emit = defineEmits<{
  updated: [Behavior]
  removed: [Behavior]
}>()

// 编辑弹窗
const editDialog = ref(false)
const editForm = ref({
  id: 0,
  category: '学习',
  reason: '',
  scoreSnapshot: 0,
  labelSnapshot: '',  // 显示原分数，用于头部
})

const CATEGORIES = ['学习', '纪律', '积极', '消极']

function formatTime(s: string) {
  return fmtDateTime(s) || s
}

function openEdit(b: Behavior) {
  editForm.value = {
    id: b.id,
    category: b.category,
    reason: b.reason,
    scoreSnapshot: b.score,
    labelSnapshot: `${b.score >= 0 ? '+' : ''}${b.score} 分`,
  }
  editDialog.value = true
}

async function saveEdit() {
  const updated = await behaviorsApi.update(editForm.value.id, {
    category: editForm.value.category,
    reason: editForm.value.reason,
  })
  ElMessage.success('已保存')
  editDialog.value = false
  emit('updated', updated)
}

async function removeBehavior(b: Behavior) {
  const tip = b.score > 0
    ? `确认删除？将从积分余额中扣回 ${b.score} 分（保底 0）。\n注意：宠物属性（经验/心情/饥饿）不会回滚。`
    : '确认删除？宠物属性（心情/饥饿）不会回滚。'
  await ElMessageBox.confirm(tip, '撤销打分', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
  await behaviorsApi.remove(b.id)
  ElMessage.success('已删除')
  emit('removed', b)
}
</script>

<template>
  <div class="timeline">
    <el-empty v-if="behaviors.length === 0" description="还没有任何行为记录" :image-size="80" />
    <el-timeline v-else>
      <el-timeline-item
        v-for="b in behaviors"
        :key="b.id"
        :type="b.score > 0 ? 'success' : 'danger'"
        :timestamp="formatTime(b.created_at)"
        placement="top"
      >
        <div class="row">
          <span class="score" :class="b.score > 0 ? 'pos' : 'neg'">
            {{ b.score >= 0 ? '+' : '' }}{{ b.score }}
          </span>
          <el-tag size="small" effect="plain">{{ b.category }}</el-tag>
          <span class="reason">{{ b.reason || '（未填写原因）' }}</span>
          <span class="actions">
            <el-button text size="small" @click="openEdit(b)">✏️</el-button>
            <el-button text size="small" type="danger" @click="removeBehavior(b)">🗑️</el-button>
          </span>
        </div>
      </el-timeline-item>
    </el-timeline>

    <el-dialog v-model="editDialog" title="编辑行为记录" width="440">
      <p class="edit-tip">
        原打分：<strong>{{ editForm.labelSnapshot }}</strong>
        <span class="edit-note">（分数已生效，不可修改；如需撤销请删除整条记录）</span>
      </p>
      <el-form label-position="top">
        <el-form-item label="类别">
          <el-select v-model="editForm.category" style="width: 100%">
            <el-option v-for="c in CATEGORIES" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="原因">
          <el-input
            v-model="editForm.reason"
            placeholder="备注（最多 200 字）"
            maxlength="200"
            show-word-limit
            type="textarea"
            :rows="2"
          />
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
.row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score {
  font-weight: 600;
  font-size: 16px;
  min-width: 40px;
}

.score.pos {
  color: #67c23a;
}

.score.neg {
  color: #f56c6c;
}

.reason {
  color: #606266;
  font-size: 14px;
  flex: 1;
}

.actions {
  display: flex;
  gap: 2px;
  opacity: 0.7;
  transition: opacity 0.15s;
}

.row:hover .actions {
  opacity: 1;
}

.edit-tip {
  background: #f4f6fa;
  padding: 10px 12px;
  border-radius: 6px;
  margin: 0 0 12px;
  color: #303133;
  font-size: 13px;
}

.edit-note {
  margin-left: 4px;
  color: #909399;
  font-size: 12px;
  font-weight: normal;
}
</style>
