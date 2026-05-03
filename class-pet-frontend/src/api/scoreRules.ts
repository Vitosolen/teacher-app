import { http } from './http'
import type { ScoreRule } from '@/types/domain'

export interface ScoreRulePayload {
  label: string
  category: string
  score: number
  sort_order?: number
  active?: boolean
}

export const scoreRulesApi = {
  list() {
    return http.get<ScoreRule[]>('/score-rules').then((r) => r.data)
  },
  create(payload: ScoreRulePayload) {
    return http.post<ScoreRule>('/score-rules', payload).then((r) => r.data)
  },
  update(id: number, payload: Partial<ScoreRulePayload>) {
    return http.patch<ScoreRule>(`/score-rules/${id}`, payload).then((r) => r.data)
  },
  remove(id: number) {
    return http.delete(`/score-rules/${id}`).then((r) => r.data)
  },
}
