import { http } from './http'
import type { Pet } from '@/types/domain'

export const petsApi = {
  get(id: number) {
    return http.get<Pet>(`/pets/${id}`).then((r) => r.data)
  },
  rename(id: number, name: string) {
    return http.patch<Pet>(`/pets/${id}`, { name }).then((r) => r.data)
  },
}
