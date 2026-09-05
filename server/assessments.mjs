const assessmentRules = {
  "scd-q9": { questionIds: Array.from({ length: 9 }, (_, i) => `q${i + 1}`), score(id, value) { if (["q4", "q5", "q7"].includes(id)) return { often: 1, sometimes: 0.5, never: 0 }[value]; return typeof value === "boolean" ? (value ? 1 : 0) : undefined; } },
  "gds-15": { questionIds: Array.from({ length: 15 }, (_, i) => `q${i + 1}`), score(id, value) { if (typeof value !== "boolean") return undefined; const positive = new Set(["q2", "q3", "q4", "q6", "q8", "q9", "q10", "q12", "q14", "q15"]); return positive.has(id) ? (value ? 1 : 0) : value ? 0 : 1; } },
  ess: { questionIds: Array.from({ length: 8 }, (_, i) => `q${i + 1}`), score(_id, value) { const score = typeof value === "string" ? Number(value) : NaN; return Number.isInteger(score) && score >= 0 && score <= 3 ? score : undefined; } },
  "edinburgh-handedness": { questionIds: Array.from({ length: 10 }, (_, i) => `q${i + 1}`), score(_id, value) { return { left: 0, both: 1, right: 2 }[value]; }, result(answers) { let left = 0; let right = 0; for (const answer of answers) { if (answer.value === "left") left += 2; if (answer.value === "right") right += 2; if (answer.value === "both") { left += 1; right += 1; } } const total = left + right; return { rawScore: total === 0 ? 0 : Math.round((100 * (right - left)) / total) }; } },
};
export function hasAssessment(id) { return Object.hasOwn(assessmentRules, id); }
export function scoreSubmission(id, rawAnswers) {
  const rule = assessmentRules[id];
  if (!rule) throw new Error("ASSESSMENT_NOT_FOUND");
  if (!Array.isArray(rawAnswers)) throw new Error("ANSWERS_REQUIRED");
  const values = new Map();
  for (const answer of rawAnswers) { if (!answer || typeof answer.questionId !== "string") throw new Error("INVALID_ANSWER"); if (values.has(answer.questionId)) throw new Error("DUPLICATE_ANSWER"); values.set(answer.questionId, answer.value); }
  if (values.size !== rule.questionIds.length || rule.questionIds.some((questionId) => !values.has(questionId))) throw new Error("INCOMPLETE_ANSWERS");
  const answers = rule.questionIds.map((questionId) => { const value = values.get(questionId); const score = rule.score(questionId, value); if (typeof score !== "number" || Number.isNaN(score)) throw new Error("INVALID_ANSWER_VALUE"); return { questionId, value, score }; });
  return { answers, result: rule.result ? rule.result(answers) : { rawScore: answers.reduce((sum, answer) => sum + answer.score, 0) } };
}
