// STT 形状连线完整数据：A/B 卷（练习 + 正式）节点坐标与年龄阈值判读。
// 数据来源：仓库根目录 stt_sequences_with_coordinates.json / stt_age_thresholds.json
// （由 main 分支 STT 补全工作提供，正式使用前仍需专业人员确认施测流程）。
import sequenceSource from '../../../stt_sequences_with_coordinates.json'
import thresholdSource from '../../../stt_age_thresholds.json'

export type SttShape = 'square' | 'circle'
export type SttForm = 'A' | 'B'
export type SttPhase = 'practice' | 'test'
export type SttAgeBand = '50-59' | '60-69' | '70-79'

export type SttNode = {
  /** 节点唯一键：形状-标签-坐标，用于区分 B 卷同标签不同形状的节点 */
  id: string
  label: string
  shape: SttShape
  /** 相对画布的百分比坐标（0-100），由源像素坐标换算 */
  x: number
  y: number
}

export type SttStage = {
  id: string
  form: SttForm
  phase: SttPhase
  title: string
  /** 全部待点击节点（B 卷包含干扰节点） */
  nodes: SttNode[]
  /** 正确点击顺序（节点 id 序列） */
  sequence: string[]
}

type SourceNode = { label: string; shape: SttShape; x: number; y: number }

const sequences = sequenceSource as {
  coordinate_system: { width: number; height: number; origin: string; unit: string }
  STT_A_practice: SourceNode[]
  STT_A_test: SourceNode[]
  STT_B_practice: SourceNode[]
  STT_B_test: SourceNode[]
  STT_B_practice_all_nodes: SourceNode[]
  STT_B_test_all_nodes: SourceNode[]
}

const thresholds = thresholdSource as {
  STT_A_thresholds: Record<SttAgeBand, number>
  STT_B_thresholds: Record<SttAgeBand, number>
  unit: string
  interpretation: string
}

export const sttAgeBands: Array<{ value: SttAgeBand; label: string }> = [
  { value: '50-59', label: '50-59 岁' },
  { value: '60-69', label: '60-69 岁' },
  { value: '70-79', label: '70-79 岁' },
]

export const sttThresholds = {
  A: thresholds.STT_A_thresholds,
  B: thresholds.STT_B_thresholds,
  unit: thresholds.unit,
  interpretation: thresholds.interpretation,
}

const coordinateKey = (node: SourceNode) => `${node.shape}-${node.label}-${node.x}-${node.y}`

const toNode = (node: SourceNode): SttNode => ({
  id: coordinateKey(node),
  label: node.label,
  shape: node.shape,
  x: Number(((node.x / sequences.coordinate_system.width) * 100).toFixed(4)),
  y: Number(((node.y / sequences.coordinate_system.height) * 100).toFixed(4)),
})

function makeStage(form: SttForm, phase: SttPhase, target: SourceNode[], display: SourceNode[] = target): SttStage {
  return {
    id: `${form}-${phase}`,
    form,
    phase,
    title: phase === 'practice' ? `${form} 卷练习` : `${form} 卷正式测试`,
    nodes: display.map(toNode),
    sequence: target.map(coordinateKey),
  }
}

/** A 卷：练习 8 节点 + 正式 25 节点；B 卷：练习/正式各含干扰节点的完整图版 */
export const sttStages: Record<SttForm, { practice: SttStage; test: SttStage }> = {
  A: {
    practice: makeStage('A', 'practice', sequences.STT_A_practice),
    test: makeStage('A', 'test', sequences.STT_A_test),
  },
  B: {
    practice: makeStage('B', 'practice', sequences.STT_B_practice, sequences.STT_B_practice_all_nodes),
    test: makeStage('B', 'test', sequences.STT_B_test, sequences.STT_B_test_all_nodes),
  },
}

export function getThreshold(form: SttForm, ageBand: SttAgeBand): number {
  return sttThresholds[form][ageBand]
}

/** 按年龄阈值判读正式测试用时：达到或超过阈值为异常 */
export function interpretDuration(form: SttForm, ageBand: SttAgeBand, durationMs: number) {
  const thresholdSeconds = getThreshold(form, ageBand)
  const durationSeconds = durationMs / 1000
  return {
    thresholdSeconds,
    durationSeconds: Number(durationSeconds.toFixed(1)),
    abnormal: durationSeconds >= thresholdSeconds,
  }
}
