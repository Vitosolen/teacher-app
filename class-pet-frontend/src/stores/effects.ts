/**
 * 全局视觉效果 store：撒花、震屏等需要被任意页面触发的动画。
 *
 * 用 fireRequest 的变化驱动 ConfettiOverlay 监听 + 触发，
 * 避免 component 之间紧耦合（任意位置 import store 调 fire 即可）。
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useEffectsStore = defineStore('effects', () => {
  const fireConfettiToken = ref(0)
  const lastConfettiCount = ref(40)

  function fireConfetti(count = 40) {
    lastConfettiCount.value = count
    fireConfettiToken.value++
  }

  return { fireConfettiToken, lastConfettiCount, fireConfetti }
})
