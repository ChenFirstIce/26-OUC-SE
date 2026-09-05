import assert from "node:assert/strict";
import test from "node:test";
import { scoreSubmission } from "./assessments.mjs";

test("SCD-Q9 supports half-point answers", () => {
  const answers = Array.from({ length: 9 }, (_, index) => ({
    questionId: `q${index + 1}`,
    value: [4, 5, 7].includes(index + 1) ? "sometimes" : true,
  }));
  assert.equal(scoreSubmission("scd-q9", answers).result.rawScore, 7.5);
});

test("GDS-15 reverse-scores positive wording", () => {
  const answers = Array.from({ length: 15 }, (_, index) => ({ questionId: `q${index + 1}`, value: true }));
  assert.equal(scoreSubmission("gds-15", answers).result.rawScore, 10);
});

test("ESS sums 0-3 choices", () => {
  const answers = Array.from({ length: 8 }, (_, index) => ({ questionId: `q${index + 1}`, value: String(index % 4) }));
  assert.equal(scoreSubmission("ess", answers).result.rawScore, 12);
});

test("Edinburgh computes the handedness index", () => {
  const answers = Array.from({ length: 10 }, (_, index) => ({ questionId: `q${index + 1}`, value: "right" }));
  assert.equal(scoreSubmission("edinburgh-handedness", answers).result.rawScore, 100);
});

test("submission must include every expected question", () => {
  assert.throws(() => scoreSubmission("ess", [{ questionId: "q1", value: "0" }]), /INCOMPLETE_ANSWERS/);
});
