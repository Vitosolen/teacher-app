<script setup lang="ts">
/**
 * 领养弹窗：选物种 + 起名
 *
 * 物种列表与「设置 → 宠物物种」管理页保持一致：
 * - 顺序按 sort_order（管理页拖拽即可改）
 * - 主图按最高等级资源（图片优先 emoji 兜底）
 * - 显示完整成长阶梯（所有已配置的等级资源依次列出）
 * - 显示物种描述
 */
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { studentsApi } from '@/api/students'
import { usePetSpeciesStore } from '@/stores/petSpecies'
import type { Student, PetSpecies, PetSpeciesAsset } from '@/types/domain'

const props = defineProps<{
  modelValue: boolean
  studentId: number
  studentName: string
}>()
const emit = defineEmits<{
  'update:modelValue': [boolean]
  adopted: [Student]
}>()

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => emit('update:modelValue', v))

const speciesStore = usePetSpeciesStore()
const speciesList = computed<PetSpecies[]>(() => speciesStore.list)

const selectedSpecies = ref('')
const petName = ref('')
const submitting = ref(false)

// 等级排序后的资源
function sortedAssets(s: PetSpecies): PetSpeciesAsset[] {
  return [...s.assets].sort((a, b) => a.level - b.level)
}

// 主图（最高等级，宠物长大后的样子）
function topAsset(s: PetSpecies): PetSpeciesAsset | null {
  if (s.assets.length === 0) return null
  return s.assets.reduce((a, b) => (a.level >= b.level ? a : b))
}

// 打开时复位 + 确保字典已拉
watch(visible, async (v) => {
  if (v) {
    await speciesStore.ensureLoaded()
    selectedSpecies.value = speciesList.value[0]?.code ?? ''
    petName.value = ''
  }
})

onMounted(() => speciesStore.ensureLoaded())

async function adopt() {
  if (!selectedSpecies.value) {
    ElMessage.warning('请先选择一种宠物')
    return
  }
  if (!petName.value.trim()) {
    ElMessage.warning('给宠物起个名字吧')
    return
  }
  submitting.value = true
  try {
    const updated = await studentsApi.adoptPet(props.studentId, {
      name: petName.value.trim(),
      species: selectedSpecies.value,
    })
    ElMessage.success(`🎉 ${props.studentName} 领养了「${petName.value.trim()}」`)
    emit('adopted', updated)
    visible.value = false
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog v-model="visible" title="🐾 领养宠物" width="640">
    <p class="tip">为「{{ studentName }}」选择一只心仪的宠物，并给它起个名字。</p>

    <el-empty
      v-if="speciesList.length === 0"
      description="还没有可领养的物种，请在「设置 → 宠物物种」先添加"
      :image-size="60"
    />

    <div v-else class="species-grid">
      <div
        v-for="s in speciesList"
        :key="s.code"
        class="species-card"
        :class="{ active: selectedSpecies === s.code }"
        @click="selectedSpecies = s.code"
      >
        <!-- 主图：最高等级（图片优先 emoji 兜底） -->
        <div class="cover">
          <img v-if="topAsset(s)?.image_url" :src="topAsset(s)!.image_url!" :alt="s.name" />
          <span v-else class="cover-emoji">{{ topAsset(s)?.emoji ?? '🥚' }}</span>
        </div>

        <div class="info">
          <div class="name-row">
            <span class="name">{{ s.name }}</span>
            <span v-if="selectedSpecies === s.code" class="check">✓</span>
          </div>
          <div v-if="s.description" class="desc">{{ s.description }}</div>

          <!-- 完整成长阶梯 -->
          <div class="stages">
            <span class="stages-label">成长：</span>
            <template v-for="(a, i) in sortedAssets(s)" :key="a.id">
              <span class="stage">
                <img v-if="a.image_url" :src="a.image_url" :alt="`Lv${a.level}`" class="stage-img" />
                <span v-else class="stage-emoji">{{ a.emoji }}</span>
                <span class="stage-lv">Lv{{ a.level }}</span>
              </span>
              <span v-if="i < sortedAssets(s).length - 1" class="arrow">→</span>
            </template>
            <span v-if="sortedAssets(s).length === 0" class="empty-stage">未配置阶梯</span>
          </div>
        </div>
      </div>
    </div>

    <el-form label-position="top" style="margin-top: 16px">
      <el-form-item label="宠物名">
        <el-input
          v-model="petName"
          placeholder="例如：小白、贝贝"
          maxlength="50"
          show-word-limit
          @keydown.enter="adopt"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="adopt">领养</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.tip {
  margin: 0 0 16px;
  color: #606266;
  font-size: 13px;
}

.species-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  max-height: 50vh;
  overflow-y: auto;
}

.species-card {
  position: relative;
  display: flex;
  gap: 12px;
  border: 2px solid #ebeef5;
  border-radius: 10px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.15s;
  background: #fafafa;
}

.species-card:hover {
  border-color: #c0c4cc;
  transform: translateY(-1px);
}

.species-card.active {
  border-color: #409eff;
  background: linear-gradient(180deg, #ecf5ff 0%, #fff 100%);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.cover {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.cover img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.15));
}

.cover-emoji {
  font-size: 44px;
  line-height: 1;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.15));
}

.info {
  flex: 1;
  min-width: 0;
}

.name-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.check {
  color: #409eff;
  font-weight: 700;
  font-size: 16px;
}

.desc {
  margin-top: 2px;
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stages {
  margin-top: 6px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 2px;
  font-size: 12px;
  color: #606266;
}

.stages-label {
  color: #909399;
  margin-right: 2px;
}

.stage {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  padding: 0 2px;
}

.stage-img {
  width: 22px;
  height: 22px;
  object-fit: contain;
}

.stage-emoji {
  font-size: 18px;
  line-height: 1;
}

.stage-lv {
  font-size: 9px;
  color: #909399;
  line-height: 1.2;
}

.arrow {
  color: #c0c4cc;
  font-size: 11px;
}

.empty-stage {
  color: #c0c4cc;
  font-size: 11px;
  font-style: italic;
}
</style>
