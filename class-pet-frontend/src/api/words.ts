import { http } from './http'
import type { WordGroup, WordGroupDetail, Word } from '@/types/domain'

export const wordsApi = {
  // 词库
  listGroups() {
    return http.get<WordGroup[]>('/word-groups').then((r) => r.data)
  },
  createGroup(payload: { name: string; description?: string; lang?: string; sort_order?: number }) {
    return http.post<WordGroup>('/word-groups', payload).then((r) => r.data)
  },
  getGroup(id: number) {
    return http.get<WordGroupDetail>(`/word-groups/${id}`).then((r) => r.data)
  },
  updateGroup(id: number, payload: Partial<{ name: string; description: string; lang: string; sort_order: number }>) {
    return http.patch<WordGroup>(`/word-groups/${id}`, payload).then((r) => r.data)
  },
  removeGroup(id: number) {
    return http.delete(`/word-groups/${id}`).then((r) => r.data)
  },
  // 单词
  createWord(groupId: number, payload: { text: string; translation?: string; sort_order?: number }) {
    return http.post<Word>(`/word-groups/${groupId}/words`, payload).then((r) => r.data)
  },
  batchCreateWords(groupId: number, lines: string[]) {
    return http
      .post<Word[]>(`/word-groups/${groupId}/words/batch`, { lines })
      .then((r) => r.data)
  },
  updateWord(id: number, payload: Partial<{ text: string; translation: string; sort_order: number }>) {
    return http.patch<Word>(`/words/${id}`, payload).then((r) => r.data)
  },
  removeWord(id: number) {
    return http.delete(`/words/${id}`).then((r) => r.data)
  },
}
