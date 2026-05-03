import { http } from './http'
import type { Homework, HomeworkDetail, HomeworkRecord, StudentScore } from '@/types/domain'

export const homeworksApi = {
  list(params: { class_id?: number; subject_id?: number; type?: string } = {}) {
    return http.get<Homework[]>('/homeworks', { params }).then((r) => r.data)
  },
  create(payload: {
    class_id: number
    subject_id: number
    type?: string
    title: string
    content?: string
    due_date?: string | null
  }) {
    return http.post<Homework>('/homeworks', payload).then((r) => r.data)
  },
  get(id: number) {
    return http.get<HomeworkDetail>(`/homeworks/${id}`).then((r) => r.data)
  },
  remove(id: number) {
    return http.delete(`/homeworks/${id}`).then((r) => r.data)
  },
  addRecords(homeworkId: number, studentIds: number[]) {
    return http
      .post<HomeworkRecord[]>(`/homeworks/${homeworkId}/records`, { student_ids: studentIds })
      .then((r) => r.data)
  },
  listStudentScores(
    studentId: number,
    params: { subject_id?: number; type?: 'homework' | 'exam'; limit?: number } = {},
  ) {
    return http
      .get<StudentScore[]>(`/students/${studentId}/scores`, { params })
      .then((r) => r.data)
  },
  updateRecord(
    recordId: number,
    payload: {
      score?: number | null
      comment?: string
      status?: string
      corrected?: boolean
    },
  ) {
    return http
      .patch<HomeworkRecord>(`/homework-records/${recordId}`, payload)
      .then((r) => r.data)
  },
}
