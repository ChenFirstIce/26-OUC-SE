import { describe, expect, it } from "vitest";
import { bostonQuestions, trailNodes, trailSequence } from "../data/demo-data";

describe("演示任务配置", () => {
  it("Boston 题目具有唯一编号与完整占位内容", () => {
    expect(bostonQuestions.length).toBeGreaterThan(0);
    expect(new Set(bostonQuestions.map((item) => item.id)).size).toBe(bostonQuestions.length);
    for (const item of bostonQuestions) {
      expect(item.expectedAnswer).not.toHaveLength(0);
      expect(item.image).toMatch(/^data:image\/svg\+xml/);
    }
  });

  it("STT 正确序列中的每个节点均存在且不重复", () => {
    const ids = trailNodes.map((node) => node.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(new Set(trailSequence).size).toBe(trailSequence.length);
    expect(trailSequence.every((id) => ids.includes(id))).toBe(true);
  });
});
