/**
 * 宠物物种 Pinia store
 *
 * 加载策略：
 * - 全局缓存所有物种 + 等级资源
 * - getPetEmoji(code, level) 同步返回 fallback emoji（找 ≤ level 的最大那档）
 * - 任意页面挂载时自动 ensureLoaded()，命中缓存不重复请求
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { petSpeciesApi } from '@/api/petSpecies'
import type { PetSpecies, PetSpeciesAsset } from '@/types/domain'

const FALLBACK_EMOJI = '🥚'

export const usePetSpeciesStore = defineStore('petSpecies', () => {
  const list = ref<PetSpecies[]>([])
  const loaded = ref(false)
  const loading = ref(false)

  const byCode = computed<Record<string, PetSpecies>>(() => {
    const m: Record<string, PetSpecies> = {}
    for (const s of list.value) m[s.code] = s
    return m
  })

  async function load() {
    if (loading.value) return
    loading.value = true
    try {
      list.value = await petSpeciesApi.list()
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  async function ensureLoaded() {
    if (!loaded.value) await load()
  }

  /**
   * 取该物种 ≤ 指定等级的最大资源（fallback 实现）
   * 返回 null 表示没找到任何资源
   */
  function findAsset(code: string | undefined, level: number): PetSpeciesAsset | null {
    if (!code) return null
    const sp = byCode.value[code]
    if (!sp || sp.assets.length === 0) return null
    let best: PetSpeciesAsset | null = null
    for (const a of sp.assets) {
      if (a.level <= level && (!best || a.level > best.level)) {
        best = a
      }
    }
    return best
  }

  function getPetEmoji(code: string | undefined, level: number): string {
    return findAsset(code, level)?.emoji ?? FALLBACK_EMOJI
  }

  /** 取宠物当前展示用的图片 URL（如果有）；没有时返回 null（前端走 emoji 兜底） */
  function getPetImage(code: string | undefined, level: number): string | null {
    return findAsset(code, level)?.image_url ?? null
  }

  function getSpeciesLabel(code: string | undefined): string {
    if (!code) return ''
    return byCode.value[code]?.name ?? code
  }

  return {
    list, loaded, loading,
    byCode,
    load, ensureLoaded,
    findAsset, getPetEmoji, getPetImage, getSpeciesLabel,
  }
})
