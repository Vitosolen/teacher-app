<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { shopApi } from '@/api/shop'
import type { OwnedItem, Pet } from '@/types/domain'

const props = defineProps<{ pet: Pet }>()
const emit = defineEmits<{
  'pet-updated': [{ hunger: number; mood: number }]
  'equipment-changed': [OwnedItem[]]   // 通知父组件最新的装备清单（用于场景渲染）
}>()

const owned = ref<OwnedItem[]>([])
const loading = ref(false)

const foods = computed(() => owned.value.filter((o) => o.item?.item_type === '食品'))
const clothes = computed(() => owned.value.filter((o) => o.item?.item_type === '衣服'))
const toys = computed(() => owned.value.filter((o) => o.item?.item_type === '玩具'))
const houses = computed(() => owned.value.filter((o) => o.item?.item_type === '房子'))
const furniture = computed(() => owned.value.filter((o) => o.item?.item_type === '家具'))

const equippedClothes = computed(() => clothes.value.find((o) => o.equipped))
const equippedHouse = computed(() => houses.value.find((o) => o.equipped))
const placedFurniture = computed(() => furniture.value.filter((o) => o.equipped))

async function load() {
  loading.value = true
  try {
    owned.value = await shopApi.listOwned(props.pet.id, false)
    emit('equipment-changed', owned.value)
  } finally {
    loading.value = false
  }
}

async function consume(o: OwnedItem) {
  const r = await shopApi.consume(props.pet.id, o.id)
  ElMessage.success(`使用了 ${o.item?.icon} ${o.item?.name}：饥饿 ${r.hunger}，心情 ${r.mood}`)
  emit('pet-updated', { hunger: r.hunger, mood: r.mood })
  await load()
}

async function equip(o: OwnedItem) {
  const list = await shopApi.equip(props.pet.id, o.id)
  owned.value = list
  emit('equipment-changed', list)
  ElMessage.success(`已装备 ${o.item?.icon} ${o.item?.name}`)
}

async function unequip(o: OwnedItem) {
  const list = await shopApi.unequip(props.pet.id, o.id)
  owned.value = list
  emit('equipment-changed', list)
  ElMessage.success('已卸下')
}

watch(() => props.pet.id, load)
onMounted(load)
defineExpose({ load })
</script>

<template>
  <div class="equip-panel" v-loading="loading">
    <div v-if="owned.length === 0" class="empty-tip">
      还没有任何物品。前往「积分商城」给宠物兑换吧。
    </div>

    <div v-else>
      <!-- 房子 -->
      <div v-if="houses.length > 0" class="row">
        <div class="row-title">
          🏠 房子（{{ houses.length }}）
          <span v-if="equippedHouse" class="equipped-tag">
            当前住在：{{ equippedHouse.item?.icon }} {{ equippedHouse.item?.name }}
          </span>
        </div>
        <div class="items">
          <div
            v-for="o in houses"
            :key="o.id"
            class="item-pill"
            :class="{ active: o.equipped }"
          >
            <span class="pill-icon">{{ o.item?.icon }}</span>
            <span class="pill-name">{{ o.item?.name }}</span>
            <el-button v-if="o.equipped" size="small" @click="unequip(o)">收起</el-button>
            <el-button v-else size="small" type="primary" plain @click="equip(o)">入住</el-button>
          </div>
        </div>
      </div>

      <!-- 家具 -->
      <div v-if="furniture.length > 0" class="row">
        <div class="row-title">
          🛋️ 家具（{{ furniture.length }}） <span class="equipped-tag" v-if="placedFurniture.length">
            已摆放 {{ placedFurniture.length }} 件
          </span>
        </div>
        <div class="items">
          <div
            v-for="o in furniture"
            :key="o.id"
            class="item-pill"
            :class="{ active: o.equipped }"
          >
            <span class="pill-icon">{{ o.item?.icon }}</span>
            <span class="pill-name">{{ o.item?.name }}</span>
            <el-button v-if="o.equipped" size="small" @click="unequip(o)">收起</el-button>
            <el-button v-else size="small" type="primary" plain @click="equip(o)">摆放</el-button>
          </div>
        </div>
      </div>

      <!-- 衣服 -->
      <div v-if="clothes.length > 0" class="row">
        <div class="row-title">
          👗 衣服（{{ clothes.length }}）
          <span v-if="equippedClothes" class="equipped-tag">
            正在穿戴：{{ equippedClothes.item?.icon }} {{ equippedClothes.item?.name }}
          </span>
        </div>
        <div class="items">
          <div
            v-for="o in clothes"
            :key="o.id"
            class="item-pill"
            :class="{ active: o.equipped }"
          >
            <span class="pill-icon">{{ o.item?.icon }}</span>
            <span class="pill-name">{{ o.item?.name }}</span>
            <el-button v-if="o.equipped" size="small" @click="unequip(o)">卸下</el-button>
            <el-button v-else size="small" type="primary" plain @click="equip(o)">装备</el-button>
          </div>
        </div>
      </div>

      <!-- 食品 -->
      <div v-if="foods.length > 0" class="row">
        <div class="row-title">🍽️ 食品（{{ foods.length }}）</div>
        <div class="items">
          <div v-for="o in foods" :key="o.id" class="item-pill">
            <span class="pill-icon">{{ o.item?.icon }}</span>
            <span class="pill-name">{{ o.item?.name }}</span>
            <el-button size="small" type="success" @click="consume(o)">喂食</el-button>
          </div>
        </div>
      </div>

      <!-- 玩具 -->
      <div v-if="toys.length > 0" class="row">
        <div class="row-title">🎮 玩具（{{ toys.length }}）</div>
        <div class="items">
          <div v-for="o in toys" :key="o.id" class="item-pill">
            <span class="pill-icon">{{ o.item?.icon }}</span>
            <span class="pill-name">{{ o.item?.name }}</span>
            <el-button size="small" type="warning" @click="consume(o)">玩耍</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.empty-tip {
  text-align: center;
  color: #909399;
  padding: 16px;
  font-size: 13px;
}

.row {
  margin-bottom: 16px;
}

.row-title {
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
  font-weight: 500;
}

.equipped-tag {
  margin-left: 8px;
  color: #67c23a;
  font-size: 12px;
}

.items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.item-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: #f4f6fa;
  border-radius: 20px;
  border: 2px solid transparent;
}

.item-pill.active {
  background: #f0f9eb;
  border-color: #67c23a;
}

.pill-icon {
  font-size: 18px;
}

.pill-name {
  font-size: 13px;
  color: #303133;
}
</style>
