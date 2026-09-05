import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams, useParams } from "react-router-dom";
import { AssessmentRenderer } from "../components/AssessmentRenderer";
import { ActionButton, GlassCard, SurfaceCard } from "../components/ui";
import { getAssessmentDefinition } from "../data/assessments";
import { repository } from "../repositories/apiRepository";
import type { AnswerValue, AssessmentAssignment, Patient } from "../types/assessment";

export function AssessmentPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const assignmentId = searchParams.get("assignmentId") ?? undefined;
  const definition = id ? getAssessmentDefinition(id) : undefined;
  const [patient, setPatient] = useState<Patient | null>(null);
  const [assignment, setAssignment] = useState<AssessmentAssignment | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, AnswerValue>>({});
  const [startedAt, setStartedAt] = useState(() => new Date().toISOString());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) { setLoaded(true); return; }
    void repository.getCurrentPatient().then(async (currentPatient) => {
      const assignments = await repository.getAssignments(currentPatient.id);
      const currentAssignment = assignments.find((item) => assignmentId ? item.assignmentId === assignmentId : item.assessmentId === id && item.status !== "completed") ?? null;
      setPatient(currentPatient);
      setAssignment(currentAssignment);
      if (currentAssignment) {
        const draft = await repository.getDraft(currentAssignment.assignmentId);
        if (draft) {
          setAnswers(Object.fromEntries(draft.answers.map((answer) => [answer.questionId, answer.value])));
          setStartedAt(draft.startedAt);
        }
      }
      setLoaded(true);
    }).catch((reason: unknown) => { setError(reason instanceof Error ? reason.message : "加载失败"); setLoaded(true); });
  }, [assignmentId, id]);

  const questionIds = useMemo(
    () => definition?.questions.map((question) => question.id) ?? [],
    [definition],
  );
  const answeredCount = questionIds.filter((questionId) => answers[questionId] !== undefined).length;
  const progress = definition ? Math.round((answeredCount / definition.questions.length) * 100) : 0;

  useEffect(() => {
    if (!loaded || !assignment || !definition || !patient) {
      return;
    }

    const questionId = questionIds[currentIndex];
    const value = answers[questionId];

    if (value === undefined) {
      return;
    }

    void repository.saveDraft({
      assignmentId: assignment.assignmentId,
      patientId: patient.id,
      assessmentId: definition.id,
      startedAt,
      questionId,
      value,
    }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "草稿保存失败"));
  }, [answers, assignment, currentIndex, definition, loaded, patient, questionIds, startedAt]);

  if (!loaded) return <SurfaceCard className="p-6 text-lg text-slate-600">正在加载评估...</SurfaceCard>;
  if (error) return <SurfaceCard className="p-6 text-lg text-red-700">{error}</SurfaceCard>;

  if (!id || !definition) {
    return (
      <SurfaceCard className="p-6 text-lg text-slate-600">
        未找到量表定义。
      </SurfaceCard>
    );
  }

  if (!assignment || !patient) {
    return (
      <SurfaceCard className="p-6 text-lg text-slate-600">
        当前没有可继续的任务，请先到管理员页面派发量表。
      </SurfaceCard>
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

  async function handleSubmit() {
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
      await repository.submitAssessment({
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
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "提交失败");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="grid gap-5">
      <GlassCard className="p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-[var(--brand)]">正在评估</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight">{resolvedDefinition.title}</h2>
            <p className="mt-2 text-base leading-7 text-slate-600">{resolvedDefinition.intro}</p>
          </div>
          <div className="min-w-40 rounded-[24px] bg-white px-4 py-4 ring-1 ring-slate-200">
            <div className="text-right text-sm text-slate-500">进度 {progress}%</div>
            <div className="mt-2 h-3 rounded-full bg-slate-100">
              <div
                className="h-3 rounded-full bg-[var(--brand)] transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      </GlassCard>

      <AssessmentRenderer
        definition={resolvedDefinition}
        currentIndex={currentIndex}
        answers={answers}
        onAnswerChange={handleAnswerChange}
      />

      <SurfaceCard className="bg-white/92 p-5 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:justify-between">
          <ActionButton
            type="button"
            disabled={currentIndex === 0}
            onClick={() => setCurrentIndex((value) => Math.max(0, value - 1))}
            variant="secondary"
          >
            上一题
          </ActionButton>
          {isLastQuestion ? (
            <ActionButton
              type="button"
              disabled={!canMoveNext || isSubmitting}
              onClick={handleSubmit}
            >
              {isSubmitting ? "提交中..." : "完成并提交"}
            </ActionButton>
          ) : (
            <ActionButton
              type="button"
              disabled={!canMoveNext}
              onClick={() =>
                setCurrentIndex((value) =>
                  Math.min(resolvedDefinition.questions.length - 1, value + 1),
                )
              }
            >
              下一题
            </ActionButton>
          )}
        </div>
      </SurfaceCard>
    </div>
  );
}
