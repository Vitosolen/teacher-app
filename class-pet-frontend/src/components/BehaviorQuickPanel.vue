<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { behaviorsApi } from '@/api/behaviors'
import { scoreRulesApi } from '@/api/scoreRules'
import { useEffectsStore } from '@/stores/effects'
import { showScoreUndoToast } from '@/composables/useScoreToast'
import type { ScoreRule, BehaviorWithPet } from '@/types/domain'

const props = defineProps<{ studentId: number; studentName?: string }>()
const emit = defineEmits<{
  submitted: [BehaviorWithPet]
  undone: []   // 撤回成功后通知父组件刷新（积分余额、行为时间线）
}>()

const submitting = ref(false)
const customDialog = ref(false)
const customForm = ref({ score: 1, category: '学习', reason: '' })

const rules = ref<ScoreRule[]>([])
const loading = ref(false)
const effects = useEffectsStore()

const positives = computed(() => rules.value.filter((r) => r.active && r.score > 0))
const negatives = computed(() => rules.value.filter((r) => r.active && r.score < 0))

async function loadRules() {
  loading.value = true
  try {
    rules.value = await scoreRulesApi.list()
  } finally {
    loading.value = false
  }
}

async function submitRule(rule: ScoreRule) {
  submitting.value = true
  try {
    const r = await behaviorsApi.create({
      student_id: props.studentId,
      score_rule_id: rule.id,
    })
    emit('submitted', r)
    if (r.leveled_up) {
      ElNotification({
        type: 'success',
        title: `🎉 ${props.studentName ?? '学生'} 的宠物升级了！`,
        message: `升到 Lv.${r.pet.level}（+${r.levels_gained} 级），积分余额：${r.student_points}`,
        duration: 4000,
      })
      effects.fireConfetti(60)
    } else {
      // 单条打分 → 撤回 toast
      showScoreUndoToast({
        studentName: props.studentName ?? '学生',
        ruleLabel: rule.label,
        score: rule.score,
        behaviorId: r.behavior.id,
        onUndo: () => emit('undone'),
      })
    }
  } finally {
    submitting.value = false
  }
}

async function submitCustom() {
  if (customForm.value.score === 0) {
    ElMessage.warning('分数不能为 0')
    return
  }
  submitting.value = true
  try {
    const r = await behaviorsApi.create({
      student_id: props.studentId,
      score: customForm.value.score,
      category: customForm.value.category,
      reason: customForm.value.reason,
    })
    ElMessage.success('已记录')
    customDialog.value = false
    customForm.value = { score: 1, category: '学习', reason: '' }
    emit('submitted', r)
  } finally {
    submitting.value = false
  }
}

onMounted(loadRules)
</script>

<template>
  <div class="bqp" v-loading="loading">
    <div class="bqp-section">
      <div class="bqp-title">👍 奖励 <span class="bqp-tip">（点击立即应用）</span></div>
      <el-empty v-if="!loading && positives.length === 0" description="还没有正向规则，去「积分规则」配置" :image-size="60" />
      <div class="bqp-buttons" v-else>
        <el-button
          v-for="r in positives"
          :key="r.id"
          type="success"
          plain
          :loading="submitting"
          @click="submitRule(r)"
        >
          {{ r.label }} +{{ r.score }}
        </el-button>
      </div>
    </div>

    <div class="bqp-section">
      <div class="bqp-title">⚠️ 提醒</div>
      <el-empty v-if="!loading && negatives.length === 0" description="还没有负向规则" :image-size="60" />
      <div class="bqp-buttons">
        <el-button
          v-for="r in negatives"
          :key="r.id"
          type="danger"
          plain
          :loading="submitting"
          @click="submitRule(r)"
        >
          {{ r.label }} {{ r.score }}
        </el-button>
        <el-button text type="primary" @click="customDialog = true">自定义...</el-button>
      </div>
    </div>

    <el-dialog v-model="customDialog" title="自定义评分" width="400">
      <el-form label-position="top">
        <el-form-item label="分数（-100 到 +100，正数加分，负数扣分）">
          <el-input-number v-model="customForm.score" :min="-100" :max="100" :step="1" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="customForm.category" style="width: 100%">
            <el-option label="学习" value="学习" />
            <el-option label="纪律" value="纪律" />
            <el-option label="积极" value="积极" />
            <el-option label="消极" value="消极" />
          </el-select>
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="customForm.reason" placeholder="可选，最多 200 字" maxlength="200" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="customDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCustom">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.bqp-section {
  margin-bottom: 12px;
}

.bqp-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 6px;
}

.bqp-tip {
  font-size: 12px;
  color: #909399;
}

.bqp-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
