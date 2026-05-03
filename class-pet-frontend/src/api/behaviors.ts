import { http } from './http'
import type { Behavior, BehaviorWithPet } from '@/types/domain'

export interface BehaviorCreatePayload {
  student_id: number
  // 用规则打分时三者可省略
  score_rule_id?: number
  score?: number
  category?: string
  reason?: string
}

export interface BehaviorBatchPayload {
  student_ids: number[]
  score_rule_id?: number
  score?: number
  category?: string
  reason?: string
}

export interface BehaviorBatchResult {
  results: BehaviorWithPet[]
  total_students: number
  total_leveled_up: number
}

export const behaviorsApi = {
  create(payload: BehaviorCreatePayload) {
    return http.post<BehaviorWithPet>('/behaviors', payload).then((r) => r.data)
  },
  createBatch(payload: BehaviorBatchPayload) {
    return http.post<BehaviorBatchResult>('/behaviors/batch', payload).then((r) => r.data)
  },
  update(id: number, payload: { category?: string; reason?: string }) {
    return http.patch<Behavior>(`/behaviors/${id}`, payload).then((r) => r.data)
  },
  remove(id: number) {
    return http.delete(`/behaviors/${id}`).then((r) => r.data)
  },
  listByStudent(studentId: number, limit = 50) {
    return http
      .get<Behavior[]>(`/students/${studentId}/behaviors`, { params: { limit } })
      .then((r) => r.data)
  },
}
