import type {
  AnswerValue,
  AssessmentDefinition,
  AssessmentQuestion,
  ScoredAnswer,
} from "../../types/assessment";

const questions: AssessmentQuestion[] = [
  { id: "q1", type: "boolean", title: "你对你的生活基本满意吗？" },
  { id: "q2", type: "boolean", title: "你是否已经放弃了许多爱好与兴趣？" },
  { id: "q3", type: "boolean", title: "你是否觉得生活空虚？" },
  { id: "q4", type: "boolean", title: "你是否感到厌倦？" },
  { id: "q5", type: "boolean", title: "你是否大部分时间精力充沛？" },
  { id: "q6", type: "boolean", title: "你是否害怕会有不幸的事落到你头上？" },
  { id: "q7", type: "boolean", title: "你是否大部分时间感到幸福？" },
  { id: "q8", type: "boolean", title: "你是否经常感到孤立无援？" },
  { id: "q9", type: "boolean", title: "你是否愿意呆在家里而不愿去室外做些新鲜事？" },
  { id: "q10", type: "boolean", title: "你是否觉得记忆力比以前差？" },
  { id: "q11", type: "boolean", title: "你觉得现在活着很开心吗？" },
  { id: "q12", type: "boolean", title: "你是否觉得像现在这样活着毫无意义？" },
  { id: "q13", type: "boolean", title: "你觉得生活充满活力吗？" },
  { id: "q14", type: "boolean", title: "你是否觉得你的处境已毫无希望？" },
  { id: "q15", type: "boolean", title: "你是否觉得大多数人比你强得多？" },
];

const depressedWhenYes = new Set([
  "q2",
  "q3",
  "q4",
  "q6",
  "q8",
  "q9",
  "q10",
  "q12",
  "q14",
  "q15",
]);

function sumScores(answers: ScoredAnswer[]) {
  return answers.reduce((total, answer) => total + answer.score, 0);
}

function scoreQuestion(questionId: string, value: AnswerValue) {
  if (typeof value !== "boolean") {
    throw new Error(`Unsupported GDS-15 answer value for ${questionId}`);
  }

  return depressedWhenYes.has(questionId) ? (value ? 1 : 0) : value ? 0 : 1;
}

export const gds15Definition: AssessmentDefinition = {
  id: "gds-15",
  title: "GDS-15 老年抑郁量表",
  estimatedMinutes: "3-5 分钟",
  intro: "请选择过去一周内最适合你的答案。此页面只记录回答和初步分数，不提供诊断结论。",
  questions,
  scoreQuestion,
  scoreAnswers: (answers) => ({
    rawScore: sumScores(answers),
  }),
};
