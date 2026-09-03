import { Link } from "react-router-dom";
import { GlassCard, StatusPill, SurfaceCard } from "../components/ui";
import { getAssessmentDefinition } from "../data/assessments";
import { repository } from "../repositories/mockRepository";

export function HistoryPage() {
  const patient = repository.getCurrentPatient();
  const submissions = repository.getSubmissions(patient.id);

  return (
    <div className="grid gap-5">
      <GlassCard className="p-6">
        <p className="text-sm font-medium text-[var(--brand)]">历史记录</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight">已完成评估</h2>
        <p className="mt-3 text-lg leading-8 text-slate-600">
          这里展示当前演示患者已提交的量表记录和结构化结果入口。
        </p>
      </GlassCard>

      {submissions.length === 0 ? (
        <SurfaceCard className="p-6 text-lg text-slate-600">
          当前还没有已完成评估。请先到任务中心完成至少一项量表。
        </SurfaceCard>
      ) : (
        <section className="grid gap-4">
          {submissions.map((submission) => {
            const definition = getAssessmentDefinition(submission.assessmentId);
            return (
              <SurfaceCard key={submission.assignmentId} className="p-6">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-medium text-[var(--brand)]">已完成</p>
                    <h3 className="mt-2 text-2xl font-semibold tracking-tight">
                      {definition?.title ?? submission.assessmentId}
                    </h3>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <StatusPill tone="brand">总分 {submission.result.rawScore}</StatusPill>
                      <StatusPill>
                        用时 {Math.max(1, Math.round(submission.metrics.durationMs / 1000))} 秒
                      </StatusPill>
                      <StatusPill>提交于 {submission.completedAt.slice(0, 16).replace("T", " ")}</StatusPill>
                    </div>
                  </div>
                  <Link
                    to={`/assessment/${submission.assessmentId}/complete?assignmentId=${submission.assignmentId}`}
                    className="inline-flex min-h-14 items-center justify-center rounded-full bg-[var(--brand)] px-6 py-3 text-lg font-medium text-white transition hover:bg-[var(--brand-dark)]"
                  >
                    查看结果
                  </Link>
                </div>
              </SurfaceCard>
            );
          })}
        </section>
      )}
    </div>
  );
}
