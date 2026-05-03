<script setup lang="ts">
import { computed } from 'vue'
import type { Pet } from '@/types/domain'
import { getSpeciesLabel } from '@/composables/useSpecies'
import PetAvatar from '@/components/PetAvatar.vue'

const props = defineProps<{ pet: Pet; compact?: boolean }>()

const statusColor = computed(() => {
  switch (props.pet.status) {
    case '健康': return '#67c23a'
    case '饥饿': return '#e6a23c'
    case '难过': return '#909399'
    case '虚弱': return '#f56c6c'
    default: return '#67c23a'
  }
})

const speciesLabel = computed(() => getSpeciesLabel(props.pet.species))
const avatarSize = computed(() => props.compact ? 36 : 64)

const expPercent = computed(() => {
  return Math.round((props.pet.exp / props.pet.exp_to_next_level) * 100)
})
</script>

<template>
  <div class="pet-card" :class="{ compact }">
    <div class="pet-emoji">
      <PetAvatar :species="pet.species" :level="pet.level" :size="avatarSize" />
    </div>
    <div class="pet-name">{{ pet.name }}</div>
    <div class="pet-tags">
      <el-tag size="small" effect="plain">{{ speciesLabel }}</el-tag>
      <el-tag size="small" effect="plain">Lv.{{ pet.level }}</el-tag>
      <el-tag size="small" :color="statusColor" effect="dark" style="border: none; color: #fff">
        {{ pet.status }}
      </el-tag>
    </div>

    <div class="bar-row">
      <span class="bar-label">经验</span>
      <el-progress
        :percentage="expPercent"
        :stroke-width="10"
        color="#409eff"
        :text-inside="true"
        :format="() => `${pet.exp}/${pet.exp_to_next_level}`"
      />
    </div>
    <div class="bar-row">
      <span class="bar-label">心情</span>
      <el-progress
        :percentage="pet.mood"
        :stroke-width="10"
        color="#e6a23c"
        :text-inside="true"
      />
    </div>
    <div class="bar-row">
      <span class="bar-label">饥饿</span>
      <el-progress
        :percentage="pet.hunger"
        :stroke-width="10"
        color="#67c23a"
        :text-inside="true"
      />
    </div>
  </div>
</template>

<style scoped>
.pet-card {
  background: linear-gradient(135deg, #fff8f0 0%, #fff 100%);
  border: 1px solid #fce4d6;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.pet-card.compact {
  padding: 12px;
}

.pet-emoji {
  font-size: 64px;
  line-height: 1;
}

.pet-card.compact .pet-emoji {
  font-size: 36px;
}

.pet-name {
  font-size: 18px;
  font-weight: 600;
  margin-top: 8px;
  color: #303133;
}

.pet-card.compact .pet-name {
  font-size: 14px;
  margin-top: 4px;
}

.pet-tags {
  margin: 8px 0;
  display: flex;
  justify-content: center;
  gap: 6px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.bar-label {
  width: 36px;
  font-size: 12px;
  color: #606266;
  text-align: right;
}

.bar-row :deep(.el-progress) {
  flex: 1;
}
</style>
