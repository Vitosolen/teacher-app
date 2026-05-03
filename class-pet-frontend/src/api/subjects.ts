import { http } from './http'
import type { Subject } from '@/types/domain'

export const subjectsApi = {
  list() {
    return http.get<Subject[]>('/subjects').then((r) => r.data)
  },
  create(payload: { name: string; color?: string; sort_order?: number }) {
    return http.post<Subject>('/subjects', payload).then((r) => r.data)
  },
  update(id: number, payload: { name?: string; color?: string; sort_order?: number }) {
    return http.patch<Subject>(`/subjects/${id}`, payload).then((r) => r.data)
  },
  remove(id: number) {
    return http.delete(`/subjects/${id}`).then((r) => r.data)
  },
}
