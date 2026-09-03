import type { AnswerValue, AssessmentDefinition } from "../../types/assessment";
import { edinburghHandednessDefinition } from "./edinburgh-handedness";
import { essDefinition } from "./ess";
import { gds15Definition } from "./gds-15";
import { scdQ9Definition } from "./scd-q9";

export const assessmentDefinitions: Record<string, AssessmentDefinition> = {
  [edinburghHandednessDefinition.id]: edinburghHandednessDefinition,
  [gds15Definition.id]: gds15Definition,
  [essDefinition.id]: essDefinition,
  [scdQ9Definition.id]: scdQ9Definition,
};

export function getAssessmentDefinition(id: string) {
  return assessmentDefinitions[id];
}

export function scoreAnswer(
  assessmentId: string,
  questionId: string,
  value: AnswerValue,
) {
  const definition = getAssessmentDefinition(assessmentId);
  if (!definition) {
    throw new Error(`Assessment definition not found for ${assessmentId}`);
  }

  return definition.scoreQuestion(questionId, value);
}
