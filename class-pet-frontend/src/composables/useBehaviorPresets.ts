import type { BehaviorPreset } from '@/types/domain'

// 课堂高频行为预设按钮配置
export const POSITIVE_PRESETS: BehaviorPreset[] = [
  { label: '主动回答', score: 3, category: '学习', reason: '主动回答问题', type: 'positive' },
  { label: '作业优秀', score: 5, category: '学习', reason: '作业全对', type: 'positive' },
  { label: '帮助同学', score: 4, category: '积极', reason: '帮助同学', type: 'positive' },
  { label: '认真听讲', score: 2, category: '学习', reason: '专注听课', type: 'positive' },
  { label: '突出表现', score: 10, category: '积极', reason: '本节课表现突出', type: 'positive' },
]

export const NEGATIVE_PRESETS: BehaviorPreset[] = [
  { label: '上课讲话', score: -2, category: '纪律', reason: '上课讲话', type: 'negative' },
  { label: '迟到', score: -3, category: '纪律', reason: '迟到', type: 'negative' },
  { label: '未交作业', score: -5, category: '学习', reason: '未交作业', type: 'negative' },
  { label: '违纪严重', score: -10, category: '纪律', reason: '严重违纪', type: 'negative' },
]
