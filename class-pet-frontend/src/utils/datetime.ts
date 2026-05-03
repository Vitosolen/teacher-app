/**
 * 后端使用 datetime.utcnow() 写入时间，序列化的 ISO 字符串不带 'Z' 后缀
 * （形如 "2026-05-03T12:00:00.123456"），浏览器 new Date() 默认会按
 * 本地时区解析，导致显示偏移 8 小时。
 *
 * 这里统一封装：把字符串当作 UTC 解析。
 */

export function parseBackendTime(s: string | null | undefined): Date | null {
  if (!s) return null
  const normalized = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(s) ? s : s + 'Z'
  const d = new Date(normalized)
  return isNaN(d.getTime()) ? null : d
}

export function fmtDateTime(s: string | null | undefined): string {
  const d = parseBackendTime(s)
  if (!d) return ''
  return d.toLocaleString('zh-CN', { hour12: false })
}

export function fmtDate(s: string | null | undefined): string {
  const d = parseBackendTime(s)
  if (!d) return ''
  return d.toLocaleDateString('zh-CN')
}

export function fmtShortDate(s: string | null | undefined): string {
  const d = parseBackendTime(s)
  if (!d) return ''
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

/** 是否当天 */
export function isSameDay(a: string | null | undefined, b: Date = new Date()): boolean {
  const d = parseBackendTime(a)
  if (!d) return false
  return d.getFullYear() === b.getFullYear()
    && d.getMonth() === b.getMonth()
    && d.getDate() === b.getDate()
}
