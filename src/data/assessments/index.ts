import type { AnswerValue, AssessmentDefinition } from "../../types/assessment";
import { scdQ9Definition } from "./scd-q9";

export const assessmentDefinitions: Record<string, AssessmentDefinition> = {
  [scdQ9Definition.id]: scdQ9Definition,
};

export function getAssessmentDefinition(id: string) {
  return assessmentDefinitions[id];
}

export function scoreAnswer(questionId: string, value: AnswerValue) {
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

  throw new Error(`Unsupported answer value for ${questionId}`);
}
