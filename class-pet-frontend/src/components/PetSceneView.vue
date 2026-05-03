<script setup lang="ts">
/**
 * 宠物场景：纯数据驱动
 *
 * 房子、家具的外观完全来自 shop_item.icon（emoji），
 * 前端不映射、不写死外形——加新商品只需后端 seed，前端自动适应。
 *
 * 布局：
 *   ┌─ 天空 ☀️ ☁️
 *   │ 大 emoji 房子
 *   │ 草地上：家具 emoji + 宠物（活动状态）+ 家具 emoji
 *   └─ 草地
 */
import { computed, ref, watch, onUnmounted } from 'vue'
import type { Pet, OwnedItem } from '@/types/domain'
import PetAvatar from '@/components/PetAvatar.vue'

const props = defineProps<{
  pet: Pet
  ownedItems: OwnedItem[]
}>()

// —— 装备过滤（全部按 item_type 自动分组，无写死名字） ——
const equippedHouse = computed(() =>
  props.ownedItems.find((o) => o.equipped && o.item?.item_type === '房子'),
)
const equippedClothes = computed(() =>
  props.ownedItems.find((o) => o.equipped && o.item?.item_type === '衣服'),
)
const placedFurniture = computed(() =>
  props.ownedItems.filter((o) => o.equipped && o.item?.item_type === '家具'),
)

// 家具按摆放顺序左右交替分布（不依赖具体名字）
const leftFurniture = computed(() =>
  placedFurniture.value.filter((_, idx) => idx % 2 === 0),
)
const rightFurniture = computed(() =>
  placedFurniture.value.filter((_, idx) => idx % 2 === 1),
)

// —— 宠物活动状态 ——
type Activity = 'sleeping' | 'eating' | 'playing' | 'idle'
const activity = ref<Activity>('idle')

// petBaseEmoji 已被 PetAvatar 替代（图片优先 emoji 兜底），此处保留 species/level 给模板用

// 默认状态：根据属性派生（不依赖具体家具名字，而是数量）
function deriveDefault(): Activity {
  const { hunger, mood } = props.pet
  if (hunger <= 30 && placedFurniture.value.length > 0) return 'sleeping'
  if (mood <= 40 && placedFurniture.value.length > 0) return 'playing'
  return 'idle'
}

let cycleTimer: number | null = null
function startCycle() {
  if (cycleTimer !== null) clearInterval(cycleTimer)
  if (!equippedHouse.value) return
  cycleTimer = window.setInterval(() => {
    const choices: Activity[] = ['idle', 'eating']
    if (placedFurniture.value.length > 0) {
      choices.push('sleeping', 'playing')
    }
    activity.value = choices[Math.floor(Math.random() * choices.length)]
  }, 6000)
}

watch(
  () => [equippedHouse.value?.id, props.pet.hunger, props.pet.mood, placedFurniture.value.length],
  () => {
    activity.value = deriveDefault()
    startCycle()
  },
  { immediate: true },
)

onUnmounted(() => {
  if (cycleTimer !== null) clearInterval(cycleTimer)
})

const activityLabel = computed(() => {
  switch (activity.value) {
    case 'sleeping': return '💤 睡觉中'
    case 'eating': return '🍽️ 吃饭中'
    case 'playing': return '🎉 玩耍中'
    default: return '😊 站立'
  }
})
</script>

<template>
  <div class="scene">
    <!-- 状态徽章悬浮 -->
    <div class="badge-row">
      <el-tag effect="dark" round>Lv.{{ pet.level }}</el-tag>
      <el-tag effect="dark" type="warning" round>😊 {{ pet.mood }}</el-tag>
      <el-tag effect="dark" type="success" round>🍖 {{ pet.hunger }}</el-tag>
      <el-tag v-if="equippedHouse" effect="dark" type="info" round>{{ activityLabel }}</el-tag>
    </div>

    <!-- 天空装饰 -->
    <div class="sky">
      <div class="sun">☀️</div>
      <div class="cloud cloud-1">☁️</div>
      <div class="cloud cloud-2">☁️</div>
    </div>

    <!-- 没领养房子 -->
    <div v-if="!equippedHouse" class="homeless">
      <div class="pet-emoji-big bob">
        <PetAvatar :species="pet.species" :level="pet.level" :size="80" />
      </div>
      <div class="pet-name-big">{{ pet.name }}</div>
      <div class="homeless-tip">
        🥺 还没有自己的家<br>
        快去「商城」买一座房子吧！
      </div>
    </div>

    <!-- 已入住：房子 emoji 大图 + 名牌 -->
    <div v-else class="stage">
      <div class="house-area">
        <div class="house-emoji" :title="equippedHouse.item?.name">
          {{ equippedHouse.item?.icon }}
        </div>
        <div class="house-name-tag">{{ equippedHouse.item?.name }}</div>
      </div>

      <!-- 草地上的家具 + 宠物 -->
      <div class="floor">
        <!-- 左侧家具 -->
        <div class="furniture-col left">
          <div
            v-for="(f, idx) in leftFurniture"
            :key="f.id"
            class="furniture-item"
            :title="f.item?.name"
            :style="{ animationDelay: `${idx * 0.15}s` }"
          >{{ f.item?.icon }}</div>
        </div>

        <!-- 中间：宠物（按活动状态切换） -->
        <div class="pet-zone">
          <!-- 睡觉 -->
          <div v-if="activity === 'sleeping'" class="pet-stand sleeping">
            <span class="zzz">💤</span>
            <span class="pet-emoji bob-slow">
              <PetAvatar :species="pet.species" :level="pet.level" :size="56" />
            </span>
          </div>
          <!-- 吃饭 -->
          <div v-else-if="activity === 'eating'" class="pet-stand eating">
            <span class="pet-emoji">
              <PetAvatar :species="pet.species" :level="pet.level" :size="56" />
            </span>
            <span class="bowl">🥣</span>
            <span class="cloth-badge" v-if="equippedClothes">{{ equippedClothes.item?.icon }}</span>
          </div>
          <!-- 玩耍 -->
          <div v-else-if="activity === 'playing'" class="pet-stand playing">
            <span class="pet-emoji wiggle">
              <PetAvatar :species="pet.species" :level="pet.level" :size="56" />
            </span>
            <span class="play-fx">🎉</span>
            <span class="cloth-badge" v-if="equippedClothes">{{ equippedClothes.item?.icon }}</span>
          </div>
          <!-- 默认站立 -->
          <div v-else class="pet-stand">
            <span class="pet-emoji bob">
              <PetAvatar :species="pet.species" :level="pet.level" :size="56" />
            </span>
            <span class="cloth-badge" v-if="equippedClothes">{{ equippedClothes.item?.icon }}</span>
          </div>
          <div class="pet-name">{{ pet.name }}</div>
        </div>

        <!-- 右侧家具 -->
        <div class="furniture-col right">
          <div
            v-for="(f, idx) in rightFurniture"
            :key="f.id"
            class="furniture-item"
            :title="f.item?.name"
            :style="{ animationDelay: `${idx * 0.15}s` }"
          >{{ f.item?.icon }}</div>
        </div>
      </div>
    </div>

    <!-- 草地 -->
    <div class="grass"></div>
  </div>
</template>

<style scoped>
.scene {
  position: relative;
  height: 360px;
  border-radius: 16px;
  overflow: hidden;
  background: linear-gradient(180deg, #b8e3ff 0%, #c5e6ff 60%, #88c97c 60%, #6cb35e 100%);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}

.badge-row {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  gap: 6px;
  z-index: 10;
  flex-wrap: wrap;
  justify-content: flex-end;
  max-width: 60%;
}

.sky {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 60%;
  pointer-events: none;
}

.sun {
  position: absolute;
  top: 14px;
  left: 24px;
  font-size: 28px;
  animation: sunSpin 30s linear infinite;
}
@keyframes sunSpin { to { transform: rotate(360deg); } }

.cloud {
  position: absolute;
  font-size: 26px;
  animation: cloudFloat 20s ease-in-out infinite;
  opacity: 0.9;
}
.cloud-1 { top: 22px; left: 30%; }
.cloud-2 { top: 38px; left: 65%; animation-delay: -10s; }
@keyframes cloudFloat {
  0%, 100% { transform: translateX(-15px); }
  50% { transform: translateX(15px); }
}

.grass {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 36px;
  background: repeating-linear-gradient(
    90deg,
    transparent 0 14px,
    rgba(255, 255, 255, 0.18) 14px 16px
  );
  pointer-events: none;
}

/* 流浪 */
.homeless {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding-bottom: 36px;
}
.pet-emoji-big {
  font-size: 80px;
  line-height: 1;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.18));
}
.pet-name-big {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  background: rgba(255, 255, 255, 0.85);
  padding: 4px 14px;
  border-radius: 14px;
}
.homeless-tip {
  text-align: center;
  font-size: 13px;
  color: #606266;
  background: rgba(255, 255, 255, 0.85);
  padding: 8px 14px;
  border-radius: 8px;
  line-height: 1.6;
}

/* —— 主舞台 —— */
.stage {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  padding-bottom: 36px;       /* 留草地 */
}

.house-area {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  pointer-events: none;
}

.house-emoji {
  font-size: 130px;            /* 大 emoji 作为家的可视化 */
  line-height: 1;
  filter: drop-shadow(0 6px 8px rgba(0, 0, 0, 0.2));
  animation: houseFloat 4s ease-in-out infinite;
  pointer-events: auto;
  cursor: help;
}

@keyframes houseFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.house-name-tag {
  margin-top: -8px;
  display: inline-block;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 2px 12px;
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* —— 草地分区：左家具 / 宠物 / 右家具 —— */
.floor {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1.4fr 1fr;
  align-items: end;
  padding: 0 24px;
  gap: 8px;
}

.furniture-col {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: end;
}
.furniture-col.left { justify-content: flex-start; }
.furniture-col.right { justify-content: flex-end; }

.furniture-item {
  font-size: 40px;
  line-height: 1;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.18));
  animation: pop-in 0.4s ease both;
  cursor: help;
}

@keyframes pop-in {
  0% { transform: scale(0); opacity: 0; }
  60% { transform: scale(1.1); }
  100% { transform: scale(1); opacity: 1; }
}

/* —— 宠物 —— */
.pet-zone {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.pet-stand {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.pet-emoji {
  font-size: 56px;
  line-height: 1;
  filter: drop-shadow(0 3px 4px rgba(0, 0, 0, 0.2));
  display: inline-block;
}

.bob { animation: bob 2.4s ease-in-out infinite; }
.bob-slow { animation: bob 4s ease-in-out infinite; }
@keyframes bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.wiggle { animation: wiggle 0.6s ease-in-out infinite; }
@keyframes wiggle {
  0%, 100% { transform: rotate(-6deg); }
  50% { transform: rotate(6deg); }
}

.cloth-badge {
  position: absolute;
  top: -4px;
  left: -8px;
  font-size: 24px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  padding: 1px;
}

.zzz {
  position: absolute;
  top: -16px;
  right: -10px;
  font-size: 22px;
  animation: zzz-float 1.6s ease-in-out infinite;
}
@keyframes zzz-float {
  0%, 100% { transform: translateY(0); opacity: 0.8; }
  50% { transform: translateY(-6px); opacity: 1; }
}

.pet-stand.sleeping { transform: rotate(8deg); }

.bowl {
  font-size: 30px;
  margin-bottom: 6px;
}

.play-fx {
  position: absolute;
  top: -6px;
  right: -14px;
  font-size: 24px;
  animation: pop-in 0.6s ease both, bob 1s ease-in-out infinite 0.6s;
}

.pet-name {
  margin-top: 4px;
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  background: rgba(255, 255, 255, 0.9);
  display: inline-block;
  padding: 1px 10px;
  border-radius: 10px;
}
</style>
