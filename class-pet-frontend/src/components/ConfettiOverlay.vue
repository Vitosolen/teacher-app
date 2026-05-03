<script setup lang="ts">
/**
 * 全屏撒花覆盖层：宠物升级、批量好成绩等高光时刻触发
 *
 * 用法：在 App.vue 挂一次，任意位置调 useEffectsStore().fireConfetti(count)
 */
import { ref, watch } from 'vue'
import { useEffectsStore } from '@/stores/effects'

interface Piece {
  id: number
  emoji: string
  left: number
  rotate: number
  size: number
  duration: number
  delay: number
}

const EMOJIS = ['🎉', '🎊', '✨', '⭐', '🌟', '💫', '🎈', '🥳', '🏆', '💎']
const pieces = ref<Piece[]>([])
let nextId = 0
const effects = useEffectsStore()

function fire(count: number) {
  const batch: Piece[] = Array.from({ length: count }, () => ({
    id: nextId++,
    emoji: EMOJIS[Math.floor(Math.random() * EMOJIS.length)],
    left: Math.random() * 100,
    rotate: Math.random() * 720 - 360,
    size: 16 + Math.random() * 28,
    duration: 2.4 + Math.random() * 1.6,
    delay: Math.random() * 0.4,
  }))
  pieces.value.push(...batch)
  // 动画结束后清理这批，避免内存累积
  const maxMs = (batch[batch.length - 1].duration + batch[batch.length - 1].delay) * 1000 + 200
  setTimeout(() => {
    const ids = new Set(batch.map((p) => p.id))
    pieces.value = pieces.value.filter((p) => !ids.has(p.id))
  }, maxMs)
}

watch(
  () => effects.fireConfettiToken,
  (token) => {
    if (token > 0) fire(effects.lastConfettiCount)
  },
)
</script>

<template>
  <div class="confetti-layer" aria-hidden="true">
    <span
      v-for="p in pieces"
      :key="p.id"
      class="piece"
      :style="{
        left: `${p.left}%`,
        fontSize: `${p.size}px`,
        animationDuration: `${p.duration}s`,
        animationDelay: `${p.delay}s`,
        '--rotate-end': `${p.rotate}deg`,
      } as Record<string, string>"
    >{{ p.emoji }}</span>
  </div>
</template>

<style scoped>
.confetti-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 9999;
}

.piece {
  position: absolute;
  top: -10vh;
  display: inline-block;
  animation: fall ease-in forwards;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.15));
  user-select: none;
  will-change: transform;
}

@keyframes fall {
  0% {
    transform: translateY(0) rotate(0deg);
    opacity: 1;
  }
  100% {
    transform: translateY(115vh) rotate(var(--rotate-end, 720deg));
    opacity: 0.85;
  }
}
</style>
