<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { Word } from '@/types/domain'

const props = defineProps<{
  modelValue: boolean
  words: Word[]
  groupName: string
  lang: string  // 朗读语言
}>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => emit('update:modelValue', v))

// 配置
const count = ref(10)
const repeat = ref(2)         // 每词朗读次数
const intervalSec = ref(5)    // 词间间隔
const rate = ref(0.9)         // 语速 0.5-2
const shuffleEnabled = ref(true)

// 状态
type Stage = 'config' | 'playing' | 'done'
const stage = ref<Stage>('config')
const playList = ref<Word[]>([])
const currentIdx = ref(0)
const currentRepeat = ref(0)
const countdown = ref(0)
const showAnswer = ref(false)

// 检查浏览器支持
const supported = typeof window !== 'undefined' && 'speechSynthesis' in window

// 控制 timer/cancel
let timer: number | null = null
let aborted = false

const maxCount = computed(() => props.words.length)

// 当弹窗关闭时复位
watch(visible, (v) => {
  if (!v) reset()
})

function reset() {
  if (timer !== null) {
    clearTimeout(timer)
    timer = null
  }
  if (supported) {
    window.speechSynthesis.cancel()
  }
  aborted = true
  stage.value = 'config'
  playList.value = []
  currentIdx.value = 0
  currentRepeat.value = 0
  countdown.value = 0
  showAnswer.value = false
}

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function speak(text: string): Promise<void> {
  return new Promise((resolve) => {
    if (!supported) {
      resolve()
      return
    }
    const u = new SpeechSynthesisUtterance(text)
    u.lang = props.lang || 'en-US'
    u.rate = rate.value
    u.onend = () => resolve()
    u.onerror = () => resolve()
    window.speechSynthesis.speak(u)
  })
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    timer = window.setTimeout(() => resolve(), ms)
  })
}

async function start() {
  if (!supported) {
    ElMessage.error('当前浏览器不支持语音合成（建议用 Chrome / Edge）')
    return
  }
  if (props.words.length === 0) {
    ElMessage.warning('词库里没有单词')
    return
  }

  let pool = props.words
  if (shuffleEnabled.value) pool = shuffle(pool)
  if (count.value < pool.length) pool = pool.slice(0, count.value)

  playList.value = pool
  currentIdx.value = 0
  currentRepeat.value = 0
  showAnswer.value = false
  stage.value = 'playing'
  aborted = false

  for (let i = 0; i < pool.length; i++) {
    if (aborted) return
    currentIdx.value = i
    const word = pool[i]
    for (let r = 0; r < repeat.value; r++) {
      if (aborted) return
      currentRepeat.value = r + 1
      await speak(word.text)
      // 同一个词的重复之间短暂停顿
      if (r < repeat.value - 1) await sleep(800)
    }
    // 词间倒计时间隔（让学生写）
    if (i < pool.length - 1) {
      for (let s = intervalSec.value; s > 0; s--) {
        if (aborted) return
        countdown.value = s
        await sleep(1000)
      }
    }
  }

  countdown.value = 0
  stage.value = 'done'
}

function stop() {
  reset()
  ElMessage.info('已停止')
}

function repeatCurrent() {
  if (!supported) return
  const word = playList.value[currentIdx.value]
  if (word) speak(word.text)
}

onUnmounted(() => {
  if (supported) window.speechSynthesis.cancel()
})
</script>

<template>
  <el-dialog
    v-model="visible"
    :title="`📢 听写：${groupName}`"
    width="640"
    :close-on-click-modal="stage !== 'playing'"
    :close-on-press-escape="stage !== 'playing'"
    :show-close="stage !== 'playing'"
  >
    <!-- 配置阶段 -->
    <div v-if="stage === 'config'" class="config">
      <el-alert
        v-if="!supported"
        type="error"
        :closable="false"
        title="当前浏览器不支持语音合成"
        description="请用最新版 Chrome / Edge 打开本页"
      />
      <el-form label-position="top">
        <el-form-item :label="`抽取数量（最多 ${maxCount}）`">
          <el-input-number v-model="count" :min="1" :max="maxCount" />
        </el-form-item>
        <el-form-item label="每词朗读遍数">
          <el-input-number v-model="repeat" :min="1" :max="5" />
        </el-form-item>
        <el-form-item label="词间间隔（秒，让学生写）">
          <el-input-number v-model="intervalSec" :min="1" :max="60" />
        </el-form-item>
        <el-form-item label="朗读语速">
          <el-slider v-model="rate" :min="0.5" :max="1.5" :step="0.1" :format-tooltip="(v) => `${v}x`" />
        </el-form-item>
        <el-form-item>
          <el-switch v-model="shuffleEnabled" /> &nbsp;随机打乱顺序
        </el-form-item>
      </el-form>
    </div>

    <!-- 播放阶段 -->
    <div v-else-if="stage === 'playing'" class="playing">
      <div class="progress">
        第 <span class="num">{{ currentIdx + 1 }}</span> / {{ playList.length }} 题
        <span class="repeat-info" v-if="repeat > 1">（第 {{ currentRepeat }}/{{ repeat }} 遍）</span>
      </div>
      <div class="big-emoji">🔊</div>
      <div class="hint" v-if="countdown > 0">
        还剩 <span class="countdown">{{ countdown }}</span> 秒，准备下一题…
      </div>
      <div class="hint" v-else>正在朗读…</div>
      <div class="play-actions">
        <el-button @click="repeatCurrent">🔁 再读一遍</el-button>
      </div>
    </div>

    <!-- 完成阶段（展示答案让学生对） -->
    <div v-else class="done">
      <div class="done-title">✅ 全部播放完毕，对答案 👇</div>
      <div class="answer-toggle">
        <el-switch v-model="showAnswer" inline-prompt active-text="显示" inactive-text="隐藏" />
        <span class="answer-tip">显示拼写</span>
      </div>
      <ol class="answer-list">
        <li v-for="(w, idx) in playList" :key="w.id">
          <span class="seq">{{ idx + 1 }}.</span>
          <span class="answer" v-if="showAnswer">{{ w.text }}</span>
          <span class="answer hidden-answer" v-else>━━━━</span>
          <span class="trans" v-if="w.translation"> · {{ w.translation }}</span>
        </li>
      </ol>
    </div>

    <template #footer>
      <template v-if="stage === 'config'">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :disabled="!supported" @click="start">▶ 开始听写</el-button>
      </template>
      <template v-else-if="stage === 'playing'">
        <el-button type="danger" plain @click="stop">⏹ 停止</el-button>
      </template>
      <template v-else>
        <el-button @click="reset">再来一次</el-button>
        <el-button type="primary" @click="visible = false">完成</el-button>
      </template>
    </template>
  </el-dialog>
</template>

<style scoped>
.config :deep(.el-alert) {
  margin-bottom: 12px;
}

.playing {
  text-align: center;
  padding: 20px 0;
}

.progress {
  font-size: 18px;
  color: #303133;
}

.progress .num {
  font-weight: 700;
  color: #409eff;
  font-size: 24px;
}

.repeat-info {
  color: #909399;
  font-size: 14px;
  margin-left: 6px;
}

.big-emoji {
  font-size: 96px;
  animation: pulse 1.2s ease-in-out infinite;
  margin: 16px 0;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.hint {
  color: #606266;
  font-size: 16px;
}

.countdown {
  color: #e6a23c;
  font-size: 36px;
  font-weight: 700;
  margin: 0 4px;
}

.play-actions {
  margin-top: 16px;
}

.done-title {
  text-align: center;
  font-size: 18px;
  color: #67c23a;
  margin-bottom: 16px;
}

.answer-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.answer-tip {
  color: #606266;
  font-size: 13px;
}

.answer-list {
  max-height: 360px;
  overflow-y: auto;
  padding-left: 16px;
}

.answer-list li {
  margin: 6px 0;
  font-size: 15px;
}

.seq {
  display: inline-block;
  width: 32px;
  color: #909399;
}

.answer {
  font-weight: 600;
  color: #303133;
}

.hidden-answer {
  color: #c0c4cc;
  letter-spacing: 4px;
}

.trans {
  color: #909399;
  font-size: 13px;
}
</style>
