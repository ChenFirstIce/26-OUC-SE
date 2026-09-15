import { describe, expect, it } from "vitest";
import { bostonQuestions, trailNodes, trailSequence } from "../data/demo-data";
import { analyzeMocaOpenAnswers, mocaOpenTasks } from "../data/moca-open";
import { getSttThreshold, sttCoordinateSystem, sttTasks } from "../data/stt-scale";

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

  it("STT JSON 坐标被缩放到网页画布范围，并保留 PDF 坐标来源", () => {
    expect(sttCoordinateSystem).toMatchObject({ width: 1489, height: 2105, origin: "top-left" });
    for (const task of [sttTasks.A.practice, sttTasks.A.test, sttTasks.B.practice, sttTasks.B.test]) {
      expect(task.sequence.every((id) => task.nodes.some((node) => node.id === id))).toBe(true);
      expect(task.nodes.every((node) => node.x >= 0 && node.x <= 100 && node.y >= 0 && node.y <= 100)).toBe(true);
      expect(task.nodes.every((node) => node.sourceX > 0 && node.sourceY > 0)).toBe(true);
    }
  });

  it("STT-A/STT-B 正式任务和年龄阈值完整", () => {
    expect(sttTasks.A.test.sequence).toHaveLength(25);
    expect(sttTasks.B.test.sequence).toHaveLength(25);
    expect(sttTasks.B.test.nodes.length).toBeGreaterThan(sttTasks.B.test.sequence.length);
    expect(getSttThreshold("A", "50-59")).toBe(70);
    expect(getSttThreshold("B", "70-79")).toBe(240);
  });

  it("MoCA-B 开放题包含付款方式和抽象分类两个结构化子任务", () => {
    expect(mocaOpenTasks.map((task) => task.id)).toEqual(["moca_payment_13", "moca_abstraction"]);
    expect(new Set(mocaOpenTasks.map((task) => task.id)).size).toBe(mocaOpenTasks.length);
    expect(mocaOpenTasks.reduce((total, task) => total + task.maxScore, 0)).toBe(6);
  });

  it("MoCA-B 本地规则覆盖付款方式、同义抽象表达和空回答", () => {
    expect(analyzeMocaOpenAnswers({
      moca_payment_13: "10元+2元+1元；5元+5元+2元+1元；13张1元",
      moca_abstraction: "火车和轮船都是交通工具；锣鼓和笛子都是乐器；南方和北方都是方位。",
    }).candidateTotal).toBe(6);
    expect(analyzeMocaOpenAnswers({
      moca_payment_13: "我不知道",
      moca_abstraction: "",
    }).candidateTotal).toBe(0);
  });
});
