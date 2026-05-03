<script setup lang="ts">
/**
 * 宠物物种管理：增删改查 + 等级资源（emoji / image_url）
 *
 * 物种是全局共享，所有老师都能看到和修改。
 * 等级资源支持任意挡（如只配 1/3/5/10），中间等级走 fallback。
 */
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadRawFile } from 'element-plus'
import { petSpeciesApi } from '@/api/petSpecies'
import { usePetSpeciesStore } from '@/stores/petSpecies'
import { http } from '@/api/http'
import type { PetSpecies, PetSpeciesAsset } from '@/types/domain'

const store = usePetSpeciesStore()
const list = computed<PetSpecies[]>(() => store.list)
const loading = ref(false)

// —— 物种弹窗 ——
const speciesDialog = ref(false)
const speciesIsEdit = ref(false)
const speciesForm = ref({ id: 0, code: '', name: '', description: '', sort_order: 0 })

// —— 资源弹窗 ——
const assetDialog = ref(false)
const assetSpeciesId = ref<number>(0)
const assetSpeciesName = ref('')
const assetIsEdit = ref(false)
const assetForm = ref({ id: 0, level: 1, emoji: '🥚', image_url: '' })

async function reload() {
  loading.value = true
  try {
    await store.load()
  } finally {
    loading.value = false
  }
}

// —— 物种 ——

function openCreateSpecies() {
  speciesIsEdit.value = false
  speciesForm.value = {
    id: 0, code: '', name: '', description: '',
    sort_order: list.value.length + 1,
  }
  speciesDialog.value = true
}

function openEditSpecies(s: PetSpecies) {
  speciesIsEdit.value = true
  speciesForm.value = {
    id: s.id, code: s.code, name: s.name,
    description: s.description, sort_order: s.sort_order,
  }
  speciesDialog.value = true
}

async function saveSpecies() {
  if (!speciesForm.value.code.trim() || !speciesForm.value.name.trim()) {
    ElMessage.warning('code 和名称都必填')
    return
  }
  if (speciesIsEdit.value) {
    await petSpeciesApi.update(speciesForm.value.id, {
      name: speciesForm.value.name.trim(),
      description: speciesForm.value.description,
      sort_order: speciesForm.value.sort_order,
    })
    ElMessage.success('已保存')
  } else {
    await petSpeciesApi.create({
      code: speciesForm.value.code.trim(),
      name: speciesForm.value.name.trim(),
      description: speciesForm.value.description,
      sort_order: speciesForm.value.sort_order,
    })
    ElMessage.success('已创建')
  }
  speciesDialog.value = false
  await reload()
}

async function removeSpecies(s: PetSpecies) {
  await ElMessageBox.confirm(
    `确认删除物种「${s.name}」(code=${s.code})？连带删除所有等级资源。\n注意：已领养该物种的学生宠物不会被删除，但显示时找不到资源会回退到 🥚。`,
    '危险操作',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
  )
  await petSpeciesApi.remove(s.id)
  ElMessage.success('已删除')
  await reload()
}

// —— 资源（等级 emoji）——

function openAddAsset(s: PetSpecies) {
  assetIsEdit.value = false
  assetSpeciesId.value = s.id
  assetSpeciesName.value = s.name
  // 默认下一个等级
  const maxLevel = s.assets.reduce((m, a) => Math.max(m, a.level), 0)
  assetForm.value = { id: 0, level: maxLevel + 1, emoji: '🥚', image_url: '' }
  assetDialog.value = true
}

function openEditAsset(s: PetSpecies, a: PetSpeciesAsset) {
  assetIsEdit.value = true
  assetSpeciesId.value = s.id
  assetSpeciesName.value = s.name
  assetForm.value = {
    id: a.id, level: a.level, emoji: a.emoji,
    image_url: a.image_url ?? '',
  }
  assetDialog.value = true
}

async function saveAsset() {
  if (!assetForm.value.emoji.trim()) {
    ElMessage.warning('emoji 必填')
    return
  }
  const payload = {
    emoji: assetForm.value.emoji.trim(),
    image_url: assetForm.value.image_url.trim() || null,
  }
  if (assetIsEdit.value) {
    await petSpeciesApi.updateAsset(assetSpeciesId.value, assetForm.value.id, payload)
    ElMessage.success('已保存')
  } else {
    await petSpeciesApi.createAsset(assetSpeciesId.value, {
      level: assetForm.value.level,
      ...payload,
    })
    ElMessage.success('已添加')
  }
  assetDialog.value = false
  await reload()
}

// —— 上传图片 ——

const uploading = ref(false)
const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'image/gif']
const MAX_BYTES = 20 * 1024 * 1024

async function uploadImage(file: UploadRawFile): Promise<boolean> {
  if (!ALLOWED_TYPES.includes(file.type)) {
    ElMessage.error('只支持 PNG / JPG / WEBP / GIF')
    return false
  }
  if (file.size > MAX_BYTES) {
    ElMessage.error(`文件超过 ${MAX_BYTES / 1024 / 1024}MB`)
    return false
  }
  uploading.value = true
  try {
    // 新建模式：先创建资源拿到 id，再上传（用户感觉是一步操作）
    let assetId = assetForm.value.id
    if (!assetId) {
      const created = await petSpeciesApi.createAsset(assetSpeciesId.value, {
        level: assetForm.value.level,
        emoji: assetForm.value.emoji.trim() || '🥚',
        image_url: null,
      })
      assetId = created.id
      assetForm.value.id = created.id
      assetIsEdit.value = true   // 切到编辑态，避免后续"保存"时再创建一遍
    }
    const fd = new FormData()
    fd.append('file', file)
    const r = await http.post(
      `/pet-species/${assetSpeciesId.value}/assets/${assetId}/upload`,
      fd,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    assetForm.value.image_url = r.data.image_url
    ElMessage.success('图片已上传')
    await reload()
  } finally {
    uploading.value = false
  }
  return false  // 阻止 el-upload 自动上传
}

function clearImage() {
  assetForm.value.image_url = ''
}

// —— 拖拽排序 ——
//
// 用原生 HTML5 drag-and-drop：
// - dragstart: 记录起拖位置
// - dragover: 可视化目标位置 + preventDefault 允许 drop
// - drop: 移动数组 + 批量 PATCH sort_order
const dragFromIdx = ref<number | null>(null)
const dragOverIdx = ref<number | null>(null)
const reordering = ref(false)

function onDragStart(idx: number, e: DragEvent) {
  dragFromIdx.value = idx
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    // Firefox 必须 setData 否则 drag 不生效
    e.dataTransfer.setData('text/plain', String(idx))
  }
}

function onDragOver(idx: number, e: DragEvent) {
  e.preventDefault()
  dragOverIdx.value = idx
}

function onDragLeave(idx: number) {
  if (dragOverIdx.value === idx) dragOverIdx.value = null
}

async function onDrop(idx: number, e: DragEvent) {
  e.preventDefault()
  const from = dragFromIdx.value
  dragFromIdx.value = null
  dragOverIdx.value = null
  if (from === null || from === idx) return

  // 本地乐观重排
  const arr = [...store.list]
  const [moved] = arr.splice(from, 1)
  arr.splice(idx, 0, moved)
  store.list = arr

  // 后端逐个 PATCH 新的 sort_order（10 ~ 10*N）
  reordering.value = true
  try {
    for (let i = 0; i < arr.length; i++) {
      const target = (i + 1) * 10
      if (arr[i].sort_order !== target) {
        await petSpeciesApi.update(arr[i].id, { sort_order: target })
        arr[i].sort_order = target
      }
    }
    ElMessage.success('顺序已保存')
  } finally {
    reordering.value = false
  }
}

function onDragEnd() {
  dragFromIdx.value = null
  dragOverIdx.value = null
}

async function removeAsset(s: PetSpecies, a: PetSpeciesAsset) {
  await ElMessageBox.confirm(
    `删除「${s.name}」 Lv.${a.level} 的资源（${a.emoji}）？该等级会回退到上一档。`,
    '提示',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
  )
  await petSpeciesApi.removeAsset(s.id, a.id)
  ElMessage.success('已删除')
  await reload()
}

onMounted(reload)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">🐾 宠物物种管理</h2>
      <el-button type="primary" @click="openCreateSpecies">+ 新建物种</el-button>
    </div>

    <p class="hint">
      物种是<strong>全局共享</strong>资源，所有老师可见。<br>
      等级资源可以任意配置（例如只配 Lv1/Lv3/Lv5），<strong>中间等级自动 fallback</strong> 到上一档可用资源。<br>
      <strong>code</strong> 一旦创建不可修改（关系到已领养宠物的数据完整性）。<br>
      <strong>🖐️ 拖动卡片</strong>调整物种展示顺序（影响领养弹窗顺序）。
    </p>

    <el-empty v-if="!loading && list.length === 0" description="还没有物种，先新建一个" />

    <div class="species-list" v-loading="loading || reordering">
      <el-card
        v-for="(s, idx) in list"
        :key="s.id"
        class="species-card"
        :class="{ dragging: dragFromIdx === idx, 'drag-over': dragOverIdx === idx && dragFromIdx !== idx }"
        shadow="hover"
        :body-style="{ padding: 0 }"
        draggable="true"
        @dragstart="onDragStart(idx, $event)"
        @dragover="onDragOver(idx, $event)"
        @dragleave="onDragLeave(idx)"
        @drop="onDrop(idx, $event)"
        @dragend="onDragEnd"
      >
        <div class="card-header">
          <div class="header-left">
            <div class="big-avatar">
              <img
                v-if="s.assets[s.assets.length - 1]?.image_url"
                :src="s.assets[s.assets.length - 1]!.image_url!"
                alt="cover"
              />
              <span v-else class="big-emoji">
                {{ s.assets[s.assets.length - 1]?.emoji ?? '🥚' }}
              </span>
            </div>
            <div>
              <div class="title">{{ s.name }}</div>
              <div class="code">code: <code>{{ s.code }}</code></div>
              <div class="desc" v-if="s.description">{{ s.description }}</div>
            </div>
          </div>
          <div class="header-actions">
            <el-button text size="small" @click="openEditSpecies(s)">编辑</el-button>
            <el-button text size="small" type="danger" @click="removeSpecies(s)">删除</el-button>
          </div>
        </div>

        <div class="assets-area">
          <div class="assets-title">
            等级资源（{{ s.assets.length }}）
            <el-button text size="small" type="primary" @click="openAddAsset(s)">+ 添加等级</el-button>
          </div>
          <el-empty v-if="s.assets.length === 0" description="还没配置资源" :image-size="40" />
          <div v-else class="assets-grid">
            <div v-for="a in s.assets" :key="a.id" class="asset-pill">
              <span class="lv">Lv.{{ a.level }}</span>
              <img v-if="a.image_url" :src="a.image_url" class="asset-img" alt="" />
              <span v-else class="emoji">{{ a.emoji }}</span>
              <el-button text size="small" @click="openEditAsset(s, a)">改</el-button>
              <el-button text size="small" type="danger" @click="removeAsset(s, a)">×</el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 物种弹窗 -->
    <el-dialog
      v-model="speciesDialog"
      :title="speciesIsEdit ? '编辑物种' : '新建物种'"
      width="460"
    >
      <el-form label-position="top">
        <el-form-item label="code（创建后不可改）">
          <el-input
            v-model="speciesForm.code"
            placeholder="例如：dragon、cat、phoenix"
            :disabled="speciesIsEdit"
          />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="speciesForm.name" placeholder="例如：小龙" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="speciesForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="speciesForm.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="speciesDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSpecies">保存</el-button>
      </template>
    </el-dialog>

    <!-- 资源弹窗 -->
    <el-dialog
      v-model="assetDialog"
      :title="assetIsEdit ? `编辑「${assetSpeciesName}」资源` : `给「${assetSpeciesName}」添加等级资源`"
      width="420"
    >
      <el-form label-position="top">
        <el-form-item label="等级（≥）">
          <el-input-number v-model="assetForm.level" :min="1" :max="999" :disabled="assetIsEdit" />
          <div class="form-tip">该资源在宠物等级 ≥ 此值时启用，直到下一档资源覆盖</div>
        </el-form-item>
        <el-form-item label="Emoji">
          <el-input v-model="assetForm.emoji" placeholder="🐲" maxlength="8" />
        </el-form-item>
        <el-form-item label="图片（可选，留空时用上面的 emoji）">
          <div class="upload-area">
            <div v-if="assetForm.image_url" class="image-preview">
              <img :src="assetForm.image_url" alt="preview" />
              <div class="image-actions">
                <el-button text size="small" type="danger" @click="clearImage">清除</el-button>
              </div>
            </div>
            <el-upload
              :show-file-list="false"
              :before-upload="uploadImage"
              accept="image/png,image/jpeg,image/webp,image/gif"
              :disabled="uploading"
            >
              <el-button :loading="uploading" type="primary" plain>
                {{ assetForm.image_url ? '替换图片' : '📤 上传图片' }}
              </el-button>
            </el-upload>
            <div class="form-tip">PNG / JPG / WEBP / GIF，最大 20MB · 上传时自动保存等级资源</div>
          </div>
          <el-input v-model="assetForm.image_url" placeholder="或手填 URL（如 /static/pets/x.png）" style="margin-top: 8px" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assetDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAsset">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.hint {
  background: #f4f6fa;
  color: #606266;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 24px;
  line-height: 1.6;
}

.hint code {
  background: #fff;
  padding: 1px 4px;
  border-radius: 3px;
  font-family: ui-monospace, monospace;
}

.species-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}

.species-card {
  overflow: hidden;
  cursor: grab;
  transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
}

.species-card:active {
  cursor: grabbing;
}

/* 正在拖动：半透明 */
.species-card.dragging {
  opacity: 0.4;
}

/* 拖到此卡上方：左侧高亮指示插入位置 */
.species-card.drag-over {
  box-shadow: -4px 0 0 0 #409eff, 0 4px 16px rgba(64, 158, 255, 0.3);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  background: linear-gradient(135deg, #fef9e7 0%, #fff3d6 100%);
  border-bottom: 1px solid #ebeef5;
}

.header-left {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.big-avatar {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.big-avatar img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.18));
}

.big-emoji {
  font-size: 48px;
  line-height: 1;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.15));
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.code {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.code code {
  background: rgba(255, 255, 255, 0.8);
  padding: 0 4px;
  border-radius: 3px;
}

.desc {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
}

.assets-area {
  padding: 12px 16px 14px;
}

.assets-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #303133;
  font-weight: 500;
  margin-bottom: 8px;
}

.assets-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.asset-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #f4f6fa;
  border-radius: 16px;
  padding: 2px 4px 2px 10px;
}

.asset-pill .lv {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.asset-pill .emoji {
  font-size: 22px;
}

.asset-img {
  width: 28px;
  height: 28px;
  object-fit: contain;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.upload-area {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.image-preview {
  position: relative;
  width: 80px;
  height: 80px;
  border: 1px dashed #c0c4cc;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  margin-bottom: 4px;
}

.image-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.image-actions {
  position: absolute;
  bottom: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 4px 0 0 0;
  padding: 0 4px;
}
</style>
