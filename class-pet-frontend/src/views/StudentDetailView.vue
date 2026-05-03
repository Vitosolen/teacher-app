<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { studentsApi } from '@/api/students'
import { behaviorsApi } from '@/api/behaviors'
import { petsApi } from '@/api/pets'
import PetCard from '@/components/PetCard.vue'
import PetSceneView from '@/components/PetSceneView.vue'
import BehaviorQuickPanel from '@/components/BehaviorQuickPanel.vue'
import BehaviorTimeline from '@/components/BehaviorTimeline.vue'
import PetEquipPanel from '@/components/PetEquipPanel.vue'
import AdoptPetDialog from '@/components/AdoptPetDialog.vue'
import ScoreTrendPanel from '@/components/ScoreTrendPanel.vue'
import type { Student, Behavior, BehaviorWithPet, OwnedItem } from '@/types/domain'

const props = defineProps<{ id: string | number }>()
const router = useRouter()

const studentId = computed(() => Number(props.id))
const student = ref<Student | null>(null)
const behaviors = ref<Behavior[]>([])
const ownedItems = ref<OwnedItem[]>([])
const loading = ref(false)
const equipPanelRef = ref<InstanceType<typeof PetEquipPanel> | null>(null)
const adoptDialog = ref(false)

function onEquipmentChanged(list: OwnedItem[]) {
  ownedItems.value = list
}

function onAdopted(updated: Student) {
  student.value = updated
}

function onBehaviorUpdated(b: Behavior) {
  const idx = behaviors.value.findIndex((x) => x.id === b.id)
  if (idx >= 0) behaviors.value[idx] = b
}

async function onBehaviorRemoved(b: Behavior) {
  behaviors.value = behaviors.value.filter((x) => x.id !== b.id)
  // 删除加分记录会回滚 student.points，重拉一下学生最新积分
  if (b.score > 0 && student.value) {
    try {
      const fresh = await studentsApi.get(studentId.value)
      student.value = fresh
    } catch {
      // 静默：不致命
    }
  }
}

async function loadAll() {
  loading.value = true
  try {
    const [s, bs] = await Promise.all([
      studentsApi.get(studentId.value),
      behaviorsApi.listByStudent(studentId.value, 50),
    ])
    student.value = s
    behaviors.value = bs
  } finally {
    loading.value = false
  }
}

// 收到打分事件：用返回的最新宠物状态局部更新 + 同步积分余额
function onBehaviorSubmitted(r: BehaviorWithPet) {
  if (student.value && student.value.pet) {
    student.value = {
      ...student.value,
      pet: r.pet,
      points: r.student_points,
    }
  }
  behaviors.value = [r.behavior, ...behaviors.value].slice(0, 50)
}

// 喂食/玩耍后，宠物 hunger/mood 改变，同步到本地 student.pet
function onPetUpdated(payload: { hunger: number; mood: number }) {
  if (student.value && student.value.pet) {
    student.value = {
      ...student.value,
      pet: { ...student.value.pet, hunger: payload.hunger, mood: payload.mood },
    }
  }
}

async function renamePet() {
  if (!student.value?.pet) return
  const pet = student.value.pet
  try {
    const { value } = await ElMessageBox.prompt('新的宠物名', '改名', {
      inputValue: pet.name,
      inputValidator: (v) => (v && v.trim().length > 0 ? true : '名字不能为空'),
      confirmButtonText: '保存',
      cancelButtonText: '取消',
    })
    const updated = await petsApi.rename(pet.id, value.trim())
    if (student.value) {
      student.value = { ...student.value, pet: updated }
    }
    ElMessage.success('已改名')
  } catch {
    // 用户取消
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="page" v-loading="loading">
    <div class="page-header">
      <div>
        <el-button text @click="router.back()">← 返回</el-button>
        <h2 class="page-title" style="display: inline; margin-left: 8px">
          {{ student?.name ?? '学生' }}
          <span class="meta" v-if="student?.student_no">· 学号 {{ student.student_no }}</span>
        </h2>
      </div>
      <div class="points-display" v-if="student">
        💰 积分余额 <span class="points-num">{{ student.points }}</span>
      </div>
    </div>

    <!-- 顶部全宽：宠物世界场景（房子 + 宠物 + 装备 + 家具） -->
    <PetSceneView
      v-if="student?.pet"
      :pet="student.pet"
      :owned-items="ownedItems"
      class="scene-top"
    />

    <!-- 没领养宠物时显示大入口 -->
    <div v-else-if="student" class="adopt-hero">
      <div class="adopt-emoji">🐾</div>
      <div class="adopt-title">{{ student.name }} 还没有宠物</div>
      <div class="adopt-sub">领养一只虚拟宠物，行为打分会让它成长进化</div>
      <el-button type="primary" size="large" @click="adoptDialog = true">🐾 立即领养</el-button>
    </div>

    <div v-if="student" class="layout">
      <div class="col-pet">
        <PetCard v-if="student.pet" :pet="student.pet" />
        <div class="pet-actions" v-if="student.pet">
          <el-button size="small" plain @click="renamePet">给宠物改名</el-button>
        </div>

        <div class="panel">
          <div class="panel-title">快捷打分</div>
          <BehaviorQuickPanel
            :student-id="student.id"
            :student-name="student.name"
            @submitted="onBehaviorSubmitted"
            @undone="loadAll"
          />
        </div>

        <div class="panel" v-if="student.pet">
          <div class="panel-title">物品栏</div>
          <PetEquipPanel
            ref="equipPanelRef"
            :pet="student.pet"
            @pet-updated="onPetUpdated"
            @equipment-changed="onEquipmentChanged"
          />
        </div>
      </div>

      <div class="col-timeline">
        <div class="panel">
          <div class="panel-title">📊 成绩趋势分析</div>
          <ScoreTrendPanel :student-id="student.id" />
        </div>
        <div class="panel">
          <div class="panel-title">行为记录（最近 50 条）</div>
          <BehaviorTimeline
            :behaviors="behaviors"
            @updated="onBehaviorUpdated"
            @removed="onBehaviorRemoved"
          />
        </div>
      </div>
    </div>

    <!-- 领养弹窗 -->
    <AdoptPetDialog
      v-if="student && !student.pet"
      v-model="adoptDialog"
      :student-id="student.id"
      :student-name="student.name"
      @adopted="onAdopted"
    />
  </div>
</template>

<style scoped>
.meta {
  color: #909399;
  font-size: 14px;
  font-weight: normal;
  margin-left: 8px;
}

.points-display {
  color: #606266;
  font-size: 14px;
}

.points-num {
  font-weight: 700;
  font-size: 18px;
  color: #e6a23c;
  margin-left: 4px;
}

.scene-top {
  margin-bottom: 20px;
}

.adopt-hero {
  text-align: center;
  padding: 60px 20px;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #fff8f0 0%, #fdf3ff 100%);
  border-radius: 16px;
  border: 2px dashed #d4b8e0;
}

.adopt-emoji {
  font-size: 64px;
  margin-bottom: 12px;
}

.adopt-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}

.adopt-sub {
  font-size: 14px;
  color: #909399;
  margin-bottom: 20px;
}

.layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 24px;
  align-items: start;
}

.col-pet,
.col-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pet-actions {
  display: flex;
  justify-content: center;
}

.panel {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
