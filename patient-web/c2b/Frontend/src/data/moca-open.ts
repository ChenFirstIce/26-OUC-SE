export type MocaOpenTaskType = "payment" | "abstraction";

export interface MocaOpenTask {
  id: string;
  type: MocaOpenTaskType;
  title: string;
  prompt: string;
  maxScore: number;
  hint: string;
}

export interface MocaOpenAnswer {
  questionId: string;
  taskType: MocaOpenTaskType;
  prompt: string;
  answer: string;
  candidateScore: number;
  explanation: string;
}

export interface MocaOpenAnalysis {
  items: MocaOpenAnswer[];
  candidateTotal: number;
  maxScore: number;
  explanation: string;
}

export const mocaOpenTasks: MocaOpenTask[] = [
  {
    id: "moca_payment_13",
    type: "payment",
    title: "付款方式",
    prompt: "如果买东西需要付 13 元，请写出 3 种不同的付款方式。",
    maxScore: 3,
    hint: "例如可使用 10 元、5 元、2 元、1 元等面额组合。",
  },
  {
    id: "moca_abstraction",
    type: "abstraction",
    title: "抽象分类",
    prompt: "请分别说明以下三组词语的共同类别：火车/轮船、锣鼓/笛子、南方/北方。",
    maxScore: 3,
    hint: "每组回答其共同类别即可。",
  },
];

const normalize = (value: string) =>
  value
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[（(].*?[）)]/g, "");

const chineseNumbers: Record<string, number> = { 一: 1, 二: 2, 两: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7, 八: 8, 九: 9, 十: 10, 十一: 11, 十二: 12, 十三: 13 };
const countPattern = String.raw`\d+|十三|十二|十一|十|一|二|两|三|四|五|六|七|八|九`;

const toCount = (value: string) => Number(value) || chineseNumbers[value] || 1;

function paymentSegmentTotal(segment: string): number {
  let total = 0;
  let rest = segment;
  const quantified = new RegExp(`(${countPattern})(?:张|个|枚)?([125]|10)(?:元|块)`, "g");
  for (const match of rest.matchAll(quantified)) {
    total += toCount(match[1]) * Number(match[2]);
  }
  rest = rest.replace(quantified, "");
  for (const match of rest.matchAll(/([125]|10)(?:元|块)/g)) total += Number(match[1]);
  return total;
}

function scorePayment(answer: string): Pick<MocaOpenAnswer, "candidateScore" | "explanation"> {
  const normalized = normalize(answer);
  const segments = normalized.split(/[;；。,\n，、]/).map((segment) => segment.trim()).filter(Boolean);
  const validWays = new Set(segments.filter((segment) => paymentSegmentTotal(segment) === 13));
  const candidateScore = Math.min(3, validWays.size);
  return {
    candidateScore,
    explanation: `识别到 ${candidateScore} 种不同且总额为 13 元的付款方式，候选计 ${candidateScore}/3 分。`,
  };
}

const abstractionRules = [
  { label: "火车/轮船", words: ["交通", "运输", "交通工具", "运输工具", "工具", "出行", "车船"] },
  { label: "锣鼓/笛子", words: ["乐器", "音乐", "器乐", "演奏", "奏乐"] },
  { label: "南方/北方", words: ["方向", "方位", "位置", "地理方位", "地域"] },
];

function scoreAbstraction(answer: string): Pick<MocaOpenAnswer, "candidateScore" | "explanation"> {
  const normalized = normalize(answer);
  const hits = abstractionRules.filter((rule) => rule.words.some((word) => normalized.includes(word)));
  return {
    candidateScore: hits.length,
    explanation: hits.length
      ? `识别到 ${hits.map((rule) => rule.label).join("、")} 的类别概括，候选计 ${hits.length}/3 分。`
      : "未识别到可计分的共同类别概括，候选计 0/3 分。",
  };
}

export function analyzeMocaOpenAnswers(answers: Record<string, string>): MocaOpenAnalysis {
  const items = mocaOpenTasks.map((task) => {
    const answer = (answers[task.id] ?? "").trim();
    const scored = task.type === "payment" ? scorePayment(answer) : scoreAbstraction(answer);
    return { questionId: task.id, taskType: task.type, prompt: task.prompt, answer, ...scored };
  });
  const candidateTotal = items.reduce((total, item) => total + item.candidateScore, 0);
  const maxScore = mocaOpenTasks.reduce((total, item) => total + item.maxScore, 0);
  return {
    items,
    candidateTotal,
    maxScore,
    explanation: `MoCA-B 开放题候选总分 ${candidateTotal}/${maxScore}，需由专业人员结合原始回答复核。`,
  };
}
