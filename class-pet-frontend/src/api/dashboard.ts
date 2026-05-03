import { http } from './http'

export interface DashboardData {
  overview: {
    class_count: number
    student_count: number
    adopted_count: number
    unadopted_count: number
  }
  today: {
    behavior_count: number
    points_granted: number
    minus_count: number
  }
  todo: {
    ungraded_homework_records: number
    correction_pending: number
  }
  points_rank: Array<{
    id: number
    name: string
    points: number
    class_name: string
  }>
  level_rank: Array<{
    pet_id: number
    student_id: number   // 用于跳学生详情，避免误用 pet_id
    pet_name: string
    species: string
    level: number
    exp: number
    student_name: string
    class_name: string
  }>
  trend_7d: Array<{ date: string; count: number }>
  recent_classes: Array<{
    id: number
    name: string
    grade: string
    student_count: number
  }>
}

export const dashboardApi = {
  get() {
    return http.get<DashboardData>('/dashboard').then((r) => r.data)
  },
}
