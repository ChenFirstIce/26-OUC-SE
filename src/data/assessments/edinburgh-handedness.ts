import type {
  AnswerValue,
  AssessmentDefinition,
  AssessmentQuestion,
  ScoredAnswer,
} from "../../types/assessment";

const handOptions = [
  { label: "左手", value: "left", description: "该动作主要使用左手完成" },
  { label: "右手", value: "right", description: "该动作主要使用右手完成" },
  { label: "双手", value: "both", description: "左右手都可完成" },
] as const;

const questions: AssessmentQuestion[] = [
  { id: "q1", type: "single-choice", title: "写字", options: [...handOptions] },
  { id: "q2", type: "single-choice", title: "画画", options: [...handOptions] },
  { id: "q3", type: "single-choice", title: "扔东西", options: [...handOptions] },
  { id: "q4", type: "single-choice", title: "用剪子", options: [...handOptions] },
  { id: "q5", type: "single-choice", title: "刷牙", options: [...handOptions] },
  { id: "q6", type: "single-choice", title: "用刀子", options: [...handOptions] },
  { id: "q7", type: "single-choice", title: "用勺子", options: [...handOptions] },
  { id: "q8", type: "single-choice", title: "梳头", options: [...handOptions] },
  { id: "q9", type: "single-choice", title: "划火柴", options: [...handOptions] },
  { id: "q10", type: "single-choice", title: "打开瓶盖", options: [...handOptions] },
];

function scoreQuestion(questionId: string, value: AnswerValue) {
  if (typeof value !== "string") {
    throw new Error(`Unsupported Edinburgh handedness answer value for ${questionId}`);
  }

  if (value === "right") {
    return 2;
  }

  if (value === "both") {
    return 1;
  }

  if (value === "left") {
    return 0;
  }

  throw new Error(`Unsupported Edinburgh handedness answer value for ${questionId}`);
}

function scoreAnswers(answers: ScoredAnswer[]) {
  let leftTotal = 0;
  let rightTotal = 0;

  answers.forEach((answer) => {
    if (answer.value === "right") {
      rightTotal += 2;
      return;
    }

    if (answer.value === "left") {
      leftTotal += 2;
      return;
    }

    if (answer.value === "both") {
      leftTotal += 1;
      rightTotal += 1;
    }
  });

  const denominator = rightTotal + leftTotal;
  const rawScore =
    denominator === 0 ? 0 : Math.round((100 * (rightTotal - leftTotal)) / denominator);

  return { rawScore };
}

export const edinburghHandednessDefinition: AssessmentDefinition = {
  id: "edinburgh-handedness",
  title: "爱丁堡利手量表",
  estimatedMinutes: "2-3 分钟",
  intro: "请按你平时最常使用的手作答。此页面只记录回答和利手指数，不提供诊断结论。",
  resultLabel: "利手指数",
  questions,
  scoreQuestion,
  scoreAnswers,
};
