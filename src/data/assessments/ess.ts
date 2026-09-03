import type {
  AnswerValue,
  AssessmentDefinition,
  AssessmentQuestion,
  ScoredAnswer,
} from "../../types/assessment";

const scaleOptions = [
  { label: "0 分", value: "0", description: "不会打瞌睡" },
  { label: "1 分", value: "1", description: "打瞌睡的可能性很小" },
  { label: "2 分", value: "2", description: "打瞌睡的可能性中等" },
  { label: "3 分", value: "3", description: "很可能打瞌睡" },
] as const;

const questions: AssessmentQuestion[] = [
  {
    id: "q1",
    type: "single-choice",
    title: "坐着阅读书刊时",
    description: "请选择在该情境下打瞌睡或睡着的可能性。",
    options: [...scaleOptions],
  },
  {
    id: "q2",
    type: "single-choice",
    title: "看电视时",
    description: "请选择在该情境下打瞌睡或睡着的可能性。",
    options: [...scaleOptions],
  },
  {
    id: "q3",
    type: "single-choice",
    title: "在沉闷公共场所坐着不动时（如剧场、开会）",
    description: "请选择在该情境下打瞌睡或睡着的可能性。",
    options: [...scaleOptions],
  },
  {
    id: "q4",
    type: "single-choice",
    title: "连续乘坐汽车 1 小时无间断",
    description: "请选择在该情境下打瞌睡或睡着的可能性。",
    options: [...scaleOptions],
  },
  {
    id: "q5",
    type: "single-choice",
    title: "条件允许情况下，下午躺下休息时",
    description: "请选择在该情境下打瞌睡或睡着的可能性。",
    options: [...scaleOptions],
  },
  {
    id: "q6",
    type: "single-choice",
    title: "坐着与人谈话时",
    description: "请选择在该情境下打瞌睡或睡着的可能性。",
    options: [...scaleOptions],
  },
  {
    id: "q7",
    type: "single-choice",
    title: "未饮酒午餐后安静地坐着",
    description: "请选择在该情境下打瞌睡或睡着的可能性。",
    options: [...scaleOptions],
  },
  {
    id: "q8",
    type: "single-choice",
    title: "遇到堵车，在停车的几分钟里",
    description: "请选择在该情境下打瞌睡或睡着的可能性。",
    options: [...scaleOptions],
  },
];

function sumScores(answers: ScoredAnswer[]) {
  return answers.reduce((total, answer) => total + answer.score, 0);
}

function scoreQuestion(questionId: string, value: AnswerValue) {
  if (typeof value !== "string") {
    throw new Error(`Unsupported ESS answer value for ${questionId}`);
  }

  const score = Number(value);
  if (Number.isNaN(score)) {
    throw new Error(`Unsupported ESS answer value for ${questionId}`);
  }

  return score;
}

export const essDefinition: AssessmentDefinition = {
  id: "ess",
  title: "ESS 爱泼沃斯嗜睡量表",
  estimatedMinutes: "3-4 分钟",
  intro: "请根据最近几个月的通常生活情况作答。此页面只记录回答和初步分数，不提供诊断结论。",
  questions,
  scoreQuestion,
  scoreAnswers: (answers) => ({
    rawScore: sumScores(answers),
  }),
};
