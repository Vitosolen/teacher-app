import { http } from './http'
import type { ClassItem, Student } from '@/types/domain'

export const classesApi = {
  list() {
    return http.get<ClassItem[]>('/classes').then((r) => r.data)
  },
  create(payload: { name: string; grade?: string }) {
    return http.post<ClassItem>('/classes', payload).then((r) => r.data)
  },
  update(id: number, payload: { name?: string; grade?: string }) {
    return http.patch<ClassItem>(`/classes/${id}`, payload).then((r) => r.data)
  },
  remove(id: number) {
    return http.delete(`/classes/${id}`).then((r) => r.data)
  },
  randomPick(id: number, count: number) {
    return http
      .post<Student[]>(`/classes/${id}/random-pick`, { count })
      .then((r) => r.data)
  },
}
