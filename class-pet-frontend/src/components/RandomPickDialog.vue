<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { classesApi } from '@/api/classes'
import PetAvatar from '@/components/PetAvatar.vue'
import type { Student } from '@/types/domain'

const props = defineProps<{
  modelValue: boolean
  classId: number
  studentsCount: number
}>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()

const visible = ref(props.modelValue)
const count = ref(1)
const picking = ref(false)
const result = ref<Student[]>([])
const tickName = ref('')   // 转盘动画显示的当前名字

// 同步 props ↔ visible
watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => emit('update:modelValue', v))
watch(visible, (v) => {
  if (!v) {
    result.value = []
    tickName.value = ''
  }
})

async function pick() {
  if (count.value < 1) {
    ElMessage.warning('数量至少 1')
    return
  }
  picking.value = true
  result.value = []
  // 先开转盘动画：拉一遍学生列表用作展示池
  // 简化：直接复用后端接口，先快速调一次拿全班池子（其实直接用 listByClass 更省）
  // 这里用 random-pick 拿到结果后做"假动画"——前后切换学生姓名
  try {
    const picked = await classesApi.randomPick(props.classId, count.value)
    // 假转盘：先快速切换 ~20 次
    const pool = picked.length > 0 ? picked : []
    for (let i = 0; i < 20; i++) {
      tickName.value = pool[i % pool.length]?.name ?? '...'
      await new Promise((resolve) => setTimeout(resolve, 60 + i * 10))
    }
    tickName.value = ''
    result.value = picked
  } catch {
    // 拦截器已弹错
  } finally {
    picking.value = false
  }
}

function close() {
  visible.value = false
}
</script>

<template>
  <el-dialog v-model="visible" title="🎲 随机点名" width="500" @close="close">
    <div class="pick-body">
      <el-form inline>
        <el-form-item label="抽取人数">
          <el-input-number
            v-model="count"
            :min="1"
            :max="Math.max(1, studentsCount)"
            :disabled="picking"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="picking" @click="pick">
            {{ picking ? '抽取中...' : '开始抽取' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 转盘动画 -->
      <transition name="fade">
        <div v-if="picking" class="wheel">
          <div class="wheel-name">{{ tickName || '🎯' }}</div>
          <div class="wheel-tip">⏳ 抽取中...</div>
        </div>
      </transition>

      <!-- 结果 -->
      <transition name="fade">
        <div v-if="!picking && result.length > 0" class="result">
          <div class="result-title">🎉 抽中：</div>
          <div class="result-grid">
            <div
              v-for="(s, idx) in result"
              :key="s.id"
              class="result-card"
              :style="{ animationDelay: `${idx * 100}ms` }"
            >
              <div class="result-emoji">
                <PetAvatar
                  v-if="s.pet"
                  :species="s.pet.species"
                  :level="s.pet.level"
                  :size="32"
                />
                <span v-else style="font-size: 32px">🐣</span>
              </div>
              <div class="result-name">{{ s.name }}</div>
              <div class="result-meta" v-if="s.student_no">学号 {{ s.student_no }}</div>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </el-dialog>
</template>

<style scoped>
.pick-body {
  min-height: 200px;
}

.wheel {
  text-align: center;
  padding: 24px 0;
}

.wheel-name {
  font-size: 48px;
  font-weight: 700;
  color: #409eff;
  letter-spacing: 4px;
  animation: shake 0.15s linear infinite;
}

.wheel-tip {
  color: #909399;
  margin-top: 8px;
}

@keyframes shake {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.06); }
}

.result-title {
  font-size: 16px;
  color: #303133;
  margin-bottom: 12px;
  text-align: center;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.result-card {
  background: linear-gradient(135deg, #fff8f0 0%, #fff 100%);
  border: 2px solid #ffd1a3;
  border-radius: 12px;
  padding: 12px;
  text-align: center;
  animation: pop 0.4s ease both;
}

@keyframes pop {
  0% { transform: scale(0.6); opacity: 0; }
  60% { transform: scale(1.08); }
  100% { transform: scale(1); opacity: 1; }
}

.result-emoji {
  font-size: 32px;
}

.result-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-top: 4px;
}

.result-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
