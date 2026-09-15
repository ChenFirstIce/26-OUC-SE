import sequenceSource from "../../../../stt_sequences_with_coordinates.json";
import thresholdSource from "../../../../stt_age_thresholds.json";
import type { SttAgeBand, SttCoordinateSystem, SttForm, SttPhase, TrailNode } from "../types";

type SourceNode = {
  label: string;
  shape: "square" | "circle";
  x: number;
  y: number;
};

type SequenceSource = {
  coordinate_system: SttCoordinateSystem;
  STT_A_practice: SourceNode[];
  STT_A_test: SourceNode[];
  STT_B_practice: SourceNode[];
  STT_B_test: SourceNode[];
  STT_B_practice_all_nodes: SourceNode[];
  STT_B_test_all_nodes: SourceNode[];
};

type ThresholdSource = {
  STT_A_thresholds: Record<SttAgeBand, number>;
  STT_B_thresholds: Record<SttAgeBand, number>;
  unit: "seconds";
  interpretation: string;
};

const sequences = sequenceSource as SequenceSource;
const thresholds = thresholdSource as ThresholdSource;

const coordinateKey = (node: SourceNode) => `${node.shape}-${node.label}-${node.x}-${node.y}`;

const toNode = (node: SourceNode, index: number, correctKeys: Set<string>): TrailNode => ({
  id: coordinateKey(node),
  label: node.label,
  shape: node.shape,
  x: Number(((node.x / sequences.coordinate_system.width) * 100).toFixed(4)),
  y: Number(((node.y / sequences.coordinate_system.height) * 100).toFixed(4)),
  sourceX: node.x,
  sourceY: node.y,
  isTarget: correctKeys.has(coordinateKey(node)),
  order: correctKeys.has(coordinateKey(node)) ? index + 1 : undefined,
});

function makeTask(form: SttForm, phase: SttPhase, targetNodes: SourceNode[], displayNodes = targetNodes) {
  const correctKeys = new Set(targetNodes.map(coordinateKey));
  return {
    id: `${form}-${phase}`,
    form,
    phase,
    nodes: displayNodes.map((node, index) => toNode(node, index, correctKeys)),
    sequence: targetNodes.map(coordinateKey),
  };
}

export const sttCoordinateSystem = sequences.coordinate_system;

export const sttTasks = {
  A: {
    practice: makeTask("A", "practice", sequences.STT_A_practice),
    test: makeTask("A", "test", sequences.STT_A_test),
  },
  B: {
    practice: makeTask("B", "practice", sequences.STT_B_practice, sequences.STT_B_practice_all_nodes),
    test: makeTask("B", "test", sequences.STT_B_test, sequences.STT_B_test_all_nodes),
  },
} as const;

export const sttAgeBands: Array<{ value: SttAgeBand; label: string }> = [
  { value: "50-59", label: "50-59 岁" },
  { value: "60-69", label: "60-69 岁" },
  { value: "70-79", label: "70-79 岁" },
];

export const sttThresholds = {
  A: thresholds.STT_A_thresholds,
  B: thresholds.STT_B_thresholds,
  unit: thresholds.unit,
  interpretation: "达到或超过对应年龄阈值为异常",
};

export function getSttThreshold(form: SttForm, ageBand: SttAgeBand) {
  return sttThresholds[form][ageBand];
}

export function interpretSttResult(form: SttForm, ageBand: SttAgeBand, durationMs: number) {
  const thresholdSeconds = getSttThreshold(form, ageBand);
  const durationSeconds = durationMs / 1000;
  return {
    thresholdSeconds,
    durationSeconds,
    abnormal: durationSeconds >= thresholdSeconds,
    text: durationSeconds >= thresholdSeconds ? "达到异常阈值" : "未达到异常阈值",
  };
}
