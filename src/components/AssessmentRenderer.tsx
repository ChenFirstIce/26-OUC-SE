import { QuestionRenderer } from "./QuestionRenderer";
import type { AssessmentDefinition, AnswerValue } from "../types/assessment";

interface Props {
  definition: AssessmentDefinition;
  currentIndex: number;
  answers: Record<string, AnswerValue>;
  onAnswerChange: (questionId: string, value: AnswerValue) => void;
}

export function AssessmentRenderer({
  definition,
  currentIndex,
  answers,
  onAnswerChange,
}: Props) {
  const question = definition.questions[currentIndex];

  return (
    <section className="rounded-[32px] border border-[var(--line)] bg-white/92 p-5 shadow-[0_10px_30px_rgba(15,23,42,0.04)] sm:p-8">
      <p className="text-sm font-medium text-[var(--brand)]">
        第 {currentIndex + 1} 题，共 {definition.questions.length} 题
      </p>
      <h2 className="mt-3 text-2xl font-semibold leading-tight tracking-tight sm:text-3xl">
        {question.title}
      </h2>
      {question.description ? (
        <p className="mt-3 text-base leading-7 text-slate-600">{question.description}</p>
      ) : null}
      <div className="mt-6">
        <QuestionRenderer
          question={question}
          value={answers[question.id] ?? null}
          onChange={(value) => onAnswerChange(question.id, value)}
        />
      </div>
    </section>
  );
}
