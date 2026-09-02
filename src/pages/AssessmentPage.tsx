import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams, useParams } from "react-router-dom";
import { AssessmentRenderer } from "../components/AssessmentRenderer";
import { getAssessmentDefinition } from "../data/assessments";
import { repository } from "../repositories/mockRepository";
import type { AnswerValue } from "../types/assessment";

export function AssessmentPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const assignmentId = searchParams.get("assignmentId") ?? undefined;
  const patient = repository.getCurrentPatient();
  const definition = id ? getAssessmentDefinition(id) : undefined;
  const assignment = id
    ? repository.getActiveAssignment(patient.id, id, assignmentId)
    : undefined;
  const draft = assignment ? repository.getDraft(assignment.assignmentId) : undefined;

  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, AnswerValue>>(() =>
    Object.fromEntries(
      draft?.answers.map((answer) => [answer.questionId, answer.value]) ?? [],
    ),
  );
  const [startedAt] = useState(() => draft?.startedAt ?? new Date().toISOString());
  const [isSubmitting, setIsSubmitting] = useState(false);

  const questionIds = useMemo(
    () => definition?.questions.map((question) => question.id) ?? [],
    [definition],
  );
  const answeredCount = questionIds.filter((questionId) => answers[questionId] !== undefined).length;
  const progress = definition ? Math.round((answeredCount / definition.questions.length) * 100) : 0;

  useEffect(() => {
    if (!assignment || !definition) {
      return;
    }

    const questionId = questionIds[currentIndex];
    const value = answers[questionId];

    if (value === undefined) {
      return;
    }

    repository.saveDraft({
      assignmentId: assignment.assignmentId,
      patientId: patient.id,
      assessmentId: definition.id,
      startedAt,
      questionId,
      value,
    });
  }, [answers, assignment, currentIndex, definition, patient.id, questionIds, startedAt]);

  if (!id || !definition) {
    return (
      <div className="rounded-[28px] bg-white p-6 text-lg text-slate-600 shadow-sm ring-1 ring-slate-200">
        未找到量表定义。
      </div>
    );
  }

  if (!assignment) {
    return (
      <div className="rounded-[28px] bg-white p-6 text-lg text-slate-600 shadow-sm ring-1 ring-slate-200">
        当前没有可继续的任务，请先到管理员页面派发 SCD-Q9。
      </div>
    );
  }

  const resolvedDefinition = definition;
  const resolvedAssignment = assignment;
  const isLastQuestion = currentIndex === resolvedDefinition.questions.length - 1;
  const currentQuestionId = resolvedDefinition.questions[currentIndex].id;
  const canMoveNext = answers[currentQuestionId] !== undefined;

  function handleAnswerChange(questionId: string, value: AnswerValue) {
    setAnswers((current) => ({
      ...current,
      [questionId]: value,
    }));
  }

  function handleSubmit() {
    if (isSubmitting) {
      return;
    }

    const hasAllAnswers = resolvedDefinition.questions.every(
      (question) => answers[question.id] !== undefined,
    );
    if (!hasAllAnswers) {
      return;
    }

    setIsSubmitting(true);
    try {
      repository.submitAssessment({
        assignmentId: resolvedAssignment.assignmentId,
        patientId: patient.id,
        assessmentId: resolvedDefinition.id,
        startedAt,
        answers: resolvedDefinition.questions.map((question) => ({
          questionId: question.id,
          value: answers[question.id] ?? null,
        })),
      });
      navigate(
        `/assessment/${resolvedDefinition.id}/complete?assignmentId=${resolvedAssignment.assignmentId}`,
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="grid gap-5">
      <section className="rounded-[28px] bg-white p-5 shadow-sm ring-1 ring-slate-200 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-teal-700">正在评估</p>
            <h2 className="mt-2 text-3xl font-semibold">{resolvedDefinition.title}</h2>
            <p className="mt-2 text-base leading-7 text-slate-600">{resolvedDefinition.intro}</p>
          </div>
          <div className="min-w-32">
            <div className="text-right text-sm text-slate-500">进度 {progress}%</div>
            <div className="mt-2 h-3 rounded-full bg-slate-100">
              <div
                className="h-3 rounded-full bg-teal-600 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      </section>

      <AssessmentRenderer
        definition={resolvedDefinition}
        currentIndex={currentIndex}
        answers={answers}
        onAnswerChange={handleAnswerChange}
      />

      <section className="rounded-[28px] bg-white p-5 shadow-sm ring-1 ring-slate-200 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:justify-between">
          <button
            type="button"
            disabled={currentIndex === 0}
            onClick={() => setCurrentIndex((value) => Math.max(0, value - 1))}
            className="min-h-14 rounded-2xl bg-slate-100 px-5 py-4 text-lg font-medium text-slate-800 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
          >
            上一题
          </button>
          {isLastQuestion ? (
            <button
              type="button"
              disabled={!canMoveNext || isSubmitting}
              onClick={handleSubmit}
              className="min-h-14 rounded-2xl bg-teal-600 px-5 py-4 text-lg font-medium text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-teal-300"
            >
              {isSubmitting ? "提交中..." : "完成并提交"}
            </button>
          ) : (
            <button
              type="button"
              disabled={!canMoveNext}
              onClick={() =>
                setCurrentIndex((value) =>
                  Math.min(resolvedDefinition.questions.length - 1, value + 1),
                )
              }
              className="min-h-14 rounded-2xl bg-teal-600 px-5 py-4 text-lg font-medium text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-teal-300"
            >
              下一题
            </button>
          )}
        </div>
      </section>
    </div>
  );
}
