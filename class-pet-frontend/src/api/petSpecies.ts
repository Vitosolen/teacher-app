import { http } from './http'
import type { PetSpecies, PetSpeciesAsset } from '@/types/domain'

export const petSpeciesApi = {
  list() {
    return http.get<PetSpecies[]>('/pet-species').then((r) => r.data)
  },
  create(payload: { code: string; name: string; description?: string; sort_order?: number }) {
    return http.post<PetSpecies>('/pet-species', payload).then((r) => r.data)
  },
  update(id: number, payload: { name?: string; description?: string; sort_order?: number }) {
    return http.patch<PetSpecies>(`/pet-species/${id}`, payload).then((r) => r.data)
  },
  remove(id: number) {
    return http.delete(`/pet-species/${id}`).then((r) => r.data)
  },
  // 资源
  createAsset(speciesId: number, payload: { level: number; emoji: string; image_url?: string | null }) {
    return http
      .post<PetSpeciesAsset>(`/pet-species/${speciesId}/assets`, payload)
      .then((r) => r.data)
  },
  updateAsset(
    speciesId: number,
    assetId: number,
    payload: { emoji?: string; image_url?: string | null },
  ) {
    return http
      .patch<PetSpeciesAsset>(`/pet-species/${speciesId}/assets/${assetId}`, payload)
      .then((r) => r.data)
  },
  removeAsset(speciesId: number, assetId: number) {
    return http
      .delete(`/pet-species/${speciesId}/assets/${assetId}`)
      .then((r) => r.data)
  },
}
