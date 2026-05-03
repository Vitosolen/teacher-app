<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { shopApi } from '@/api/shop'
import { classesApi } from '@/api/classes'
import { studentsApi } from '@/api/students'
import type { ShopItem, Student, ClassItem } from '@/types/domain'

const items = ref<ShopItem[]>([])
const classes = ref<ClassItem[]>([])
const students = ref<Student[]>([])

const selectedClassId = ref<number | undefined>(undefined)
const selectedStudentId = ref<number | undefined>(undefined)
const activeTab = ref('全部')
const loading = ref(false)

const selectedStudent = computed(() =>
  students.value.find((s) => s.id === selectedStudentId.value),
)

// Tabs 按商品里出现的 item_type 动态生成（保留指定顺序）
const TAB_ORDER = ['食品', '衣服', '玩具', '房子', '家具']
const tabs = computed(() => {
  const present = new Set(items.value.map((i) => i.item_type))
  const ordered = TAB_ORDER.filter((t) => present.has(t))
  return ['全部', ...ordered]
})

const filteredItems = computed(() => {
  if (activeTab.value === '全部') return items.value
  return items.value.filter((i) => i.item_type === activeTab.value)
})

async function load() {
  loading.value = true
  try {
    const [shop, cls] = await Promise.all([shopApi.listItems(), classesApi.list()])
    items.value = shop
    classes.value = cls
    if (cls.length > 0 && !selectedClassId.value) {
      selectedClassId.value = cls[0].id
      await loadStudents()
    }
  } finally {
    loading.value = false
  }
}

async function loadStudents() {
  if (!selectedClassId.value) {
    students.value = []
    selectedStudentId.value = undefined
    return
  }
  students.value = await studentsApi.listByClass(selectedClassId.value)
  if (students.value.length > 0 && !selectedStudentId.value) {
    selectedStudentId.value = students.value[0].id
  } else if (!students.value.find((s) => s.id === selectedStudentId.value)) {
    selectedStudentId.value = students.value[0]?.id
  }
}

async function onClassChange() {
  selectedStudentId.value = undefined
  await loadStudents()
}

async function buy(item: ShopItem) {
  if (!selectedStudentId.value || !selectedStudent.value) {
    ElMessage.warning('请先选择学生')
    return
  }
  if (selectedStudent.value.points < item.price) {
    ElMessage.error(
      `${selectedStudent.value.name} 积分不足：当前 ${selectedStudent.value.points}，需要 ${item.price}`,
    )
    return
  }
  await ElMessageBox.confirm(
    `确认为「${selectedStudent.value.name}」兑换「${item.icon} ${item.name}」？将扣除 ${item.price} 积分。`,
    '兑换确认',
    {
      confirmButtonText: '兑换',
      cancelButtonText: '取消',
      type: 'info',
    },
  )
  const r = await shopApi.redeem(item.id, selectedStudentId.value)
  // 更新本地积分
  if (selectedStudent.value) {
    selectedStudent.value.points = r.student_points
  }
  ElMessage.success(`兑换成功！剩余积分 ${r.student_points}`)
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">🛒 积分商城</h2>
    </div>

    <div class="picker-row">
      <el-select v-model="selectedClassId" placeholder="选择班级" style="width: 200px" @change="onClassChange">
        <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-select v-model="selectedStudentId" placeholder="选择学生" style="width: 200px" :disabled="students.length === 0">
        <el-option
          v-for="s in students"
          :key="s.id"
          :label="`${s.name} · 💰 ${s.points}`"
          :value="s.id"
        />
      </el-select>
      <div class="balance" v-if="selectedStudent">
        当前积分余额：<span class="balance-num">💰 {{ selectedStudent.points }}</span>
      </div>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane v-for="t in tabs" :key="t" :label="t" :name="t" />
    </el-tabs>

    <div class="shop-grid" v-loading="loading">
      <el-card
        v-for="item in filteredItems"
        :key="item.id"
        shadow="hover"
        class="shop-card"
        :body-style="{ padding: '16px' }"
      >
        <div class="item-icon">{{ item.icon }}</div>
        <div class="item-name">{{ item.name }}</div>
        <div class="item-type">
          <el-tag size="small" effect="plain">{{ item.item_type }}</el-tag>
        </div>
        <div class="item-desc">{{ item.description }}</div>
        <div class="item-effect" v-if="item.effect_hunger || item.effect_mood">
          <span v-if="item.effect_hunger">🍖 +{{ item.effect_hunger }} </span>
          <span v-if="item.effect_mood">😊 +{{ item.effect_mood }}</span>
        </div>
        <div class="item-bottom">
          <span class="price">💰 {{ item.price }}</span>
          <el-button
            type="primary"
            size="small"
            :disabled="!selectedStudent || selectedStudent.points < item.price"
            @click="buy(item)"
          >兑换</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.picker-row {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
}

.balance {
  margin-left: auto;
  color: #606266;
  font-size: 14px;
}

.balance-num {
  color: #e6a23c;
  font-weight: 600;
  font-size: 16px;
}

.shop-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.shop-card {
  text-align: center;
  transition: transform 0.15s;
}

.shop-card:hover {
  transform: translateY(-2px);
}

.item-icon {
  font-size: 56px;
  line-height: 1;
}

.item-name {
  font-size: 16px;
  font-weight: 600;
  margin-top: 8px;
  color: #303133;
}

.item-type {
  margin: 4px 0;
}

.item-desc {
  font-size: 12px;
  color: #909399;
  min-height: 32px;
  margin: 4px 0;
}

.item-effect {
  font-size: 12px;
  color: #67c23a;
  margin-bottom: 8px;
}

.item-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px dashed #ebeef5;
  padding-top: 8px;
  margin-top: 8px;
}

.price {
  color: #e6a23c;
  font-weight: 600;
}
</style>
