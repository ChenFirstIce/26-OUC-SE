export type MocaOpenTaskType = 'payment' | 'abstraction'

export interface MocaOpenTask {
  id: string
  type: MocaOpenTaskType
  title: string
  prompt: string
  maxScore: number
  hint: string
}

export const mocaOpenTasks: MocaOpenTask[] = [
  {
    id: 'moca_payment_13',
    type: 'payment',
    title: '付款方式',
    prompt: '如果买东西需要付 13 元，请写出 3 种不同的付款方式。',
    maxScore: 3,
    hint: '例如可使用 10 元、5 元、2 元、1 元等面额组合。',
  },
  {
    id: 'moca_abstraction',
    type: 'abstraction',
    title: '抽象分类',
    prompt: '请分别说明以下三组词语的共同类别：火车/轮船、锣鼓/笛子、南方/北方。',
    maxScore: 3,
    hint: '每组回答其共同类别即可。',
  },
]
