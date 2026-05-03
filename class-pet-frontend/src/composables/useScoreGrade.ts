/**
 * 成绩等级判定（三、四年级标准，0-100 分制）
 *
 *   A [85-100]   B (75-85]   C (60-75]   D [0-60]
 *     A1 [96-100]  B1 (82-85]  C1 (70-75]  D1 (50-60]
 *     A2 (90-96]   B2 (78-82]  C2 (65-70]  D2 (40-50]
 *     A3 (85-90]   B3 (75-78]  C3 (60-65]  D3 [0-40]
 *
 * 边界规则：每段为左开右闭 (low, high]，例 90 分属于 A2、85 分属于 A3。
 */

export interface GradeInfo {
  /** 主等级 A/B/C/D */
  grade: 'A' | 'B' | 'C' | 'D'
  /** 细分等级 A1/A2/A3/B1... */
  sub: string
  /** Element Plus el-tag 类型 */
  tagType: 'success' | 'primary' | 'warning' | 'danger'
  /** 主等级的整体区间描述 */
  range: string
}

const GRADE_TABLE: Array<{ min: number; sub: string; grade: GradeInfo['grade']; tagType: GradeInfo['tagType']; range: string }> = [
  { min: 96, sub: 'A1', grade: 'A', tagType: 'success', range: '[85-100]' },
  { min: 90, sub: 'A2', grade: 'A', tagType: 'success', range: '[85-100]' },
  { min: 85, sub: 'A3', grade: 'A', tagType: 'success', range: '[85-100]' },
  { min: 82, sub: 'B1', grade: 'B', tagType: 'primary', range: '(75-85]' },
  { min: 78, sub: 'B2', grade: 'B', tagType: 'primary', range: '(75-85]' },
  { min: 75, sub: 'B3', grade: 'B', tagType: 'primary', range: '(75-85]' },
  { min: 70, sub: 'C1', grade: 'C', tagType: 'warning', range: '(60-75]' },
  { min: 65, sub: 'C2', grade: 'C', tagType: 'warning', range: '(60-75]' },
  { min: 60, sub: 'C3', grade: 'C', tagType: 'warning', range: '(60-75]' },
  { min: 50, sub: 'D1', grade: 'D', tagType: 'danger', range: '[0-60]' },
  { min: 40, sub: 'D2', grade: 'D', tagType: 'danger', range: '[0-60]' },
  { min: 0,  sub: 'D3', grade: 'D', tagType: 'danger', range: '[0-60]' },
]

export function getGrade(score: number | null | undefined): GradeInfo | null {
  if (score === null || score === undefined) return null
  if (Number.isNaN(score)) return null
  for (const row of GRADE_TABLE) {
    if (score >= row.min) {
      return { grade: row.grade, sub: row.sub, tagType: row.tagType, range: row.range }
    }
  }
  return null
}

/** 是否达到 A 等级（业务上：达 A 不需订正） */
export function isAGrade(score: number | null | undefined): boolean {
  return getGrade(score)?.grade === 'A'
}
