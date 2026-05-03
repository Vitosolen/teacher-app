<script setup lang="ts">
/**
 * 宠物头像：图片优先，emoji 兜底
 *
 * 用法：<PetAvatar :species="pet.species" :level="pet.level" :size="64" />
 *
 * 行为：
 * - 该物种 ≤ level 中最大那档 asset：有 image_url 显示图片，否则显示 emoji
 * - 物种字典还没加载完时显示 🥚
 * - 图片加载失败时自动回退到 emoji
 */
import { computed, ref, watch } from 'vue'
import { usePetSpeciesStore } from '@/stores/petSpecies'

const props = withDefaults(defineProps<{
  species: string | undefined | null
  level: number
  size?: number       // px
}>(), {
  size: 64,
})

const store = usePetSpeciesStore()

const asset = computed(() => store.findAsset(props.species ?? undefined, props.level))
const emoji = computed(() => asset.value?.emoji ?? '🥚')
const imageUrl = computed(() => asset.value?.image_url ?? null)

// 图片加载失败时降级到 emoji
const imgFailed = ref(false)
watch(imageUrl, () => { imgFailed.value = false })

function onImgError() {
  imgFailed.value = true
}

const showImage = computed(() => imageUrl.value && !imgFailed.value)

const emojiStyle = computed(() => ({
  fontSize: `${props.size}px`,
  lineHeight: 1,
}))

const imgStyle = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
  objectFit: 'contain' as const,
}))
</script>

<template>
  <img
    v-if="showImage"
    :src="imageUrl!"
    :alt="species ?? 'pet'"
    class="pet-avatar-img"
    :style="imgStyle"
    @error="onImgError"
  />
  <span v-else class="pet-avatar-emoji" :style="emojiStyle">{{ emoji }}</span>
</template>

<style scoped>
.pet-avatar-emoji {
  display: inline-block;
  filter: drop-shadow(0 3px 4px rgba(0, 0, 0, 0.18));
}

.pet-avatar-img {
  filter: drop-shadow(0 3px 4px rgba(0, 0, 0, 0.18));
  user-select: none;
}
</style>
