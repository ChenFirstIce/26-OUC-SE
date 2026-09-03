import type {
  AnswerValue,
  AssessmentDefinition,
  AssessmentQuestion,
  ScoredAnswer,
} from "../../types/assessment";

const questions: AssessmentQuestion[] = [
  { id: "q1", type: "boolean", title: "你认为自己有记忆问题吗？" },
  { id: "q2", type: "boolean", title: "你回忆 3-5 天前的对话有困难吗？" },
  { id: "q3", type: "boolean", title: "你觉得自己近两年有记忆问题吗？" },
  {
    id: "q4",
    type: "single-choice",
    title: "下列问题经常发生吗：忘记对个人来说重要的日期（如生日等）？",
    options: [
      { label: "经常", value: "often" },
      { label: "偶尔", value: "sometimes" },
      { label: "从未", value: "never" },
    ],
  },
  {
    id: "q5",
    type: "single-choice",
    title: "下列问题经常发生吗：忘记常用号码？",
    options: [
      { label: "经常", value: "often" },
      { label: "偶尔", value: "sometimes" },
      { label: "从未", value: "never" },
    ],
  },
  {
    id: "q6",
    type: "boolean",
    title: "总的来说，你是否认为自己对要做的事或要说的话容易忘记？",
  },
  {
    id: "q7",
    type: "single-choice",
    title: "下列问题经常发生吗：到了商店忘记要买什么？",
    options: [
      { label: "经常", value: "often" },
      { label: "偶尔", value: "sometimes" },
      { label: "从未", value: "never" },
    ],
  },
  { id: "q8", type: "boolean", title: "你认为自己的记忆力比 5 年前要差吗？" },
  {
    id: "q9",
    type: "boolean",
    title: "你认为自己越来越记不住东西放哪儿了吗？",
  },
];

function sumScores(answers: ScoredAnswer[]) {
  return answers.reduce((total, answer) => total + answer.score, 0);
}

function scoreQuestion(questionId: string, value: AnswerValue) {
  if (typeof value === "boolean") {
    return value ? 1 : 0;
  }

  if (typeof value === "string") {
    const scale: Record<string, number> = {
      often: 1,
      sometimes: 0.5,
      never: 0,
    };

    return scale[value] ?? 0;
  }

  throw new Error(`Unsupported SCD-Q9 answer value for ${questionId}`);
}

export const scdQ9Definition: AssessmentDefinition = {
  id: "scd-q9",
  title: "SCD-Q9 主观认知下降筛查",
  estimatedMinutes: "3-5 分钟",
  intro:
    "请根据你最近的实际感受作答。此页面只记录回答和初步分数，不提供诊断结论。",
  questions,
  scoreQuestion,
  scoreAnswers: (answers) => ({
    rawScore: sumScores(answers),
  }),
};
