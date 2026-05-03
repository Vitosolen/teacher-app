/**
 * 单条打分后的撤回 toast：右下角弹通知，5 秒内可撤回（删除该 behavior）
 *
 * 用法：
 *   showScoreUndoToast({
 *     studentName: '小明',
 *     ruleLabel: '回答问题',
 *     score: 1,
 *     behaviorId: 123,
 *     onUndo: async () => { 重新拉数据 },
 *   })
 */
import { h } from 'vue'
import { ElButton, ElMessage, ElNotification } from 'element-plus'
import { behaviorsApi } from '@/api/behaviors'

export interface ScoreUndoOpts {
  studentName: string
  ruleLabel: string
  score: number
  behaviorId: number
  onUndo?: () => void | Promise<void>
}

export function showScoreUndoToast(opts: ScoreUndoOpts) {
  const sign = opts.score >= 0 ? '+' : ''
  const isPositive = opts.score > 0

  let undone = false
  const handler = ElNotification({
    title: `${opts.studentName}：${sign}${opts.score} ${opts.ruleLabel}`,
    type: isPositive ? 'success' : 'warning',
    duration: 5000,
    position: 'bottom-right',
    message: h(
      'div',
      { style: 'display: flex; align-items: center; gap: 8px;' },
      [
        h('span', { style: 'color: #909399; font-size: 12px;' }, '5 秒内可撤回 →'),
        h(
          ElButton,
          {
            text: true,
            type: 'primary',
            size: 'small',
            onClick: async (e: Event) => {
              e.stopPropagation()
              if (undone) return
              undone = true
              try {
                await behaviorsApi.remove(opts.behaviorId)
                handler.close()
                ElMessage.info(`已撤回 ${opts.studentName} 的 ${sign}${opts.score} 分`)
                await opts.onUndo?.()
              } catch {
                undone = false
              }
            },
          },
          () => '🔁 撤回',
        ),
      ],
    ),
  })
}
