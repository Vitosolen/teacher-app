import { http } from './http'
import type { ShopItem, OwnedItem, RedeemResult, ConsumeResult } from '@/types/domain'

export const shopApi = {
  listItems(itemType?: string) {
    return http
      .get<ShopItem[]>('/shop-items', { params: itemType ? { item_type: itemType } : {} })
      .then((r) => r.data)
  },
  redeem(itemId: number, studentId: number) {
    return http
      .post<RedeemResult>(`/shop-items/${itemId}/redeem`, { student_id: studentId })
      .then((r) => r.data)
  },
  listOwned(petId: number, includeConsumed = false) {
    return http
      .get<OwnedItem[]>(`/pets/${petId}/owned-items`, {
        params: { include_consumed: includeConsumed },
      })
      .then((r) => r.data)
  },
  equip(petId: number, ownedItemId: number) {
    return http
      .post<OwnedItem[]>(`/pets/${petId}/equip`, { owned_item_id: ownedItemId })
      .then((r) => r.data)
  },
  unequip(petId: number, ownedItemId: number) {
    return http
      .post<OwnedItem[]>(`/pets/${petId}/unequip`, { owned_item_id: ownedItemId })
      .then((r) => r.data)
  },
  consume(petId: number, ownedItemId: number) {
    return http
      .post<ConsumeResult>(`/pets/${petId}/consume`, { owned_item_id: ownedItemId })
      .then((r) => r.data)
  },
}
