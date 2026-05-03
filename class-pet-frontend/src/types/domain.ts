// 与后端 schema 对齐的领域类型

export interface Teacher {
  id: number
  username: string
  display_name: string
  created_at: string
}

export interface ClassItem {
  id: number
  name: string
  grade: string
  teacher_id: number
  created_at: string
  student_count: number
}

export interface Pet {
  id: number
  student_id: number
  name: string
  species: string
  level: number
  exp: number
  hunger: number
  mood: number
  status: string  // 健康/饥饿/难过/虚弱
  exp_to_next_level: number
  last_updated_at: string
  created_at: string
}

export interface Student {
  id: number
  class_id: number
  name: string
  student_no: string
  points: number
  created_at: string
  pet: Pet | null
}

export interface Behavior {
  id: number
  student_id: number
  teacher_id: number
  score: number
  category: string
  reason: string
  score_rule_id: number | null
  created_at: string
}

export interface BehaviorWithPet {
  behavior: Behavior
  pet: Pet
  student_points: number
  leveled_up: boolean
  levels_gained: number
}

// 老的本地预设（迭代 2 起改为后端 score_rules，保留类型给临时降级用）
export interface BehaviorPreset {
  label: string
  score: number
  category: string
  reason: string
  type: 'positive' | 'negative'
}

// ========== 迭代 2 新增类型 ==========

export interface Subject {
  id: number
  teacher_id: number
  name: string
  color: string
  sort_order: number
  created_at: string
}

export interface ScoreRule {
  id: number
  teacher_id: number
  label: string
  category: string
  score: number
  sort_order: number
  active: boolean
  created_at: string
}

export interface Homework {
  id: number
  class_id: number
  class_name: string
  subject_id: number
  subject_name: string
  subject_color: string
  type: string             // homework / exam
  title: string
  content: string
  due_date: string | null
  created_at: string
  total_count: number
  graded_count: number
  correction_pending_count: number
}

export interface HomeworkRecord {
  id: number
  homework_id: number
  student_id: number
  student_name: string
  student_no: string
  status: string  // 未提交/已提交/已批改
  score: number | null
  comment: string
  scored_at: string | null
  needs_correction: boolean
  corrected: boolean
  corrected_at: string | null
  created_at: string
}

export interface HomeworkDetail extends Homework {
  records: HomeworkRecord[]
}

export interface StudentScore {
  record_id: number
  homework_id: number
  homework_title: string
  homework_type: string  // homework / exam
  subject_id: number
  subject_name: string
  subject_color: string
  score: number
  status: string
  needs_correction: boolean
  corrected: boolean
  scored_at: string | null
  comment: string
}

export interface ShopItem {
  id: number
  name: string
  item_type: string  // 衣服/食品/玩具
  price: number
  icon: string
  description: string
  effect_hunger: number
  effect_mood: number
  consumable: boolean
  sort_order: number
}

export interface OwnedItem {
  id: number
  pet_id: number
  shop_item_id: number
  item: ShopItem
  equipped: boolean
  acquired_at: string
  consumed_at: string | null
}

export interface RedeemResult {
  student_points: number
  owned_item: OwnedItem
}

export interface ConsumeResult {
  pet_id: number
  hunger: number
  mood: number
  owned_item_id: number
}

// ========== 单词听写 ==========

export interface WordGroup {
  id: number
  teacher_id: number
  name: string
  description: string
  lang: string         // en-US / zh-CN / en-GB / ja-JP ...
  sort_order: number
  created_at: string
  word_count: number
}

export interface Word {
  id: number
  group_id: number
  text: string
  translation: string
  sort_order: number
  created_at: string
}

export interface WordGroupDetail extends WordGroup {
  words: Word[]
}

// ========== 宠物物种字典 ==========

export interface PetSpeciesAsset {
  id: number
  species_id: number
  level: number
  emoji: string
  image_url: string | null
  created_at: string
}

export interface PetSpecies {
  id: number
  code: string
  name: string
  description: string
  sort_order: number
  created_at: string
  assets: PetSpeciesAsset[]
}
