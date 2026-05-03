/**
 * 兼容层：保留旧 `import { getPetEmoji, getSpeciesLabel } from '@/composables/useSpecies'`
 * 内部改为读取 Pinia store，自动从后端字典拉物种 + 等级资源。
 *
 * SPECIES_LIST / SpeciesDef 等老导出已废弃；新代码请直接用 usePetSpeciesStore + AdoptPetDialog 从后端拉数据。
 */
import { usePetSpeciesStore } from '@/stores/petSpecies'

export function getPetEmoji(species: string | undefined, level: number): string {
  return usePetSpeciesStore().getPetEmoji(species, level)
}

export function getPetImage(species: string | undefined, level: number): string | null {
  return usePetSpeciesStore().getPetImage(species, level)
}

export function getSpeciesLabel(species: string | undefined): string {
  return usePetSpeciesStore().getSpeciesLabel(species)
}
