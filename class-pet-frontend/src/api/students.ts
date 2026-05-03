import { http } from './http'
import type { Student } from '@/types/domain'

export const studentsApi = {
  listByClass(classId: number) {
    return http.get<Student[]>(`/classes/${classId}/students`).then((r) => r.data)
  },
  create(classId: number, payload: { name: string; student_no?: string }) {
    return http.post<Student>(`/classes/${classId}/students`, payload).then((r) => r.data)
  },
  update(id: number, payload: { name?: string; student_no?: string }) {
    return http.patch<Student>(`/students/${id}`, payload).then((r) => r.data)
  },
  adoptPet(id: number, payload: { name: string; species: string }) {
    return http.post<Student>(`/students/${id}/adopt-pet`, payload).then((r) => r.data)
  },
  batchCreate(classId: number, names: string[]) {
    return http
      .post<Student[]>(`/classes/${classId}/students/batch`, { names })
      .then((r) => r.data)
  },
  get(id: number) {
    return http.get<Student>(`/students/${id}`).then((r) => r.data)
  },
  remove(id: number) {
    return http.delete(`/students/${id}`).then((r) => r.data)
  },
}
