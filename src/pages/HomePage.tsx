import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { MetricCard, GlassCard, StatusPill, SurfaceCard } from "../components/ui";
import { getAssessmentDefinition } from "../data/assessments";
import { repository } from "../repositories/apiRepository";
import type { AssessmentAssignment, Patient } from "../types/assessment";

export function HomePage() {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [assignments, setAssignments] = useState<AssessmentAssignment[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void repository.getCurrentPatient().then(async (current) => {
      setPatient(current);
      setAssignments(await repository.getAssignments(current.id));
    }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "加载失败"));
  }, []);

  const stats = useMemo(
    () => ({
      pending: assignments.filter((item) => item.status === "pending").length,
      inProgress: assignments.filter((item) => item.status === "in_progress").length,
      completed: assignments.filter((item) => item.status === "completed").length,
    }),
    [assignments],
  );

  if (error) return <SurfaceCard className="p-6 text-lg text-red-700">{error}</SurfaceCard>;
  if (!patient) return <SurfaceCard className="p-6 text-lg text-slate-600">正在加载任务...</SurfaceCard>;

  return (
    <div className="grid gap-5">
      <GlassCard className="overflow-hidden p-6">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium text-[var(--brand)]">患者任务中心</p>
            <h2 className="mt-2 text-4xl font-semibold tracking-tight">{patient.name}</h2>
            <p className="mt-3 max-w-2xl text-lg leading-8 text-slate-600">
              请从下方任务开始评估。系统会自动保存草稿，并在提交后记录初步分数。
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <MetricCard label="待完成" value={stats.pending} emphasized />
            <MetricCard label="进行中" value={stats.inProgress} />
            <MetricCard label="已完成" value={stats.completed} />
          </div>
        </div>
      </GlassCard>

      <section className="grid gap-4">
        {assignments.length === 0 ? (
          <SurfaceCard className="p-6 text-lg text-slate-600">
            暂无任务。请先到管理员模式派发 SCD-Q9。
          </SurfaceCard>
        ) : (
          assignments.map((assignment) => {
            const definition = getAssessmentDefinition(assignment.assessmentId);
            if (!definition) {
              return null;
            }

            const actionLabel =
              assignment.status === "completed"
                ? "查看完成页"
                : assignment.status === "in_progress"
                  ? "继续评估"
                  : "查看说明";

            const target =
              assignment.status === "completed"
                ? `/assessment/${assignment.assessmentId}/complete?assignmentId=${assignment.assignmentId}`
                : assignment.status === "in_progress"
                  ? `/assessment/${assignment.assessmentId}?assignmentId=${assignment.assignmentId}`
                  : `/assessment/${assignment.assessmentId}/intro?assignmentId=${assignment.assignmentId}`;

            return (
              <SurfaceCard key={assignment.assignmentId} className="p-6">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-medium text-[var(--brand)]">
                      {assignment.status === "pending"
                        ? "待完成"
                        : assignment.status === "in_progress"
                          ? "进行中"
                          : "已完成"}
                    </p>
                    <h3 className="mt-2 text-2xl font-semibold tracking-tight">{definition.title}</h3>
                    <p className="mt-2 text-base leading-7 text-slate-600">
                      预计时长 {definition.estimatedMinutes}
                    </p>
                    <div className="mt-4 flex flex-wrap gap-2 text-sm text-slate-500">
                      <StatusPill>任务号 {assignment.assignmentId}</StatusPill>
                      <StatusPill tone="brand">自动保存草稿</StatusPill>
                    </div>
                  </div>
                  <Link
                    to={target}
                    className="inline-flex min-h-14 items-center justify-center rounded-full bg-[var(--brand)] px-6 py-3 text-lg font-medium text-white transition hover:bg-[var(--brand-dark)]"
                  >
                    {actionLabel}
                  </Link>
                </div>
              </SurfaceCard>
            );
          })
        )}
      </section>
    </div>
  );
}
