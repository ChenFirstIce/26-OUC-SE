import { useEffect, useState } from "react";
import { Link, useSearchParams, useParams } from "react-router-dom";
import { GlassCard, MetricCard, SurfaceCard } from "../components/ui";
import { getAssessmentDefinition } from "../data/assessments";
import { repository } from "../repositories/apiRepository";
import type { AssessmentSubmission } from "../types/assessment";

export function AssessmentCompletePage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const assignmentId = searchParams.get("assignmentId") ?? "";
  const definition = id ? getAssessmentDefinition(id) : undefined;
  const [submission, setSubmission] = useState<AssessmentSubmission | null | undefined>(undefined);

  useEffect(() => {
    if (!assignmentId) { setSubmission(null); return; }
    void repository.getLatestSubmission(assignmentId).then(setSubmission).catch(() => setSubmission(null));
  }, [assignmentId]);

  if (submission === undefined) return <SurfaceCard className="p-6 text-lg text-slate-600">正在加载提交结果...</SurfaceCard>;

  if (!definition || !submission) {
    return (
      <SurfaceCard className="p-6 text-lg text-slate-600">
        未找到提交记录。
      </SurfaceCard>
    );
  }

  return (
    <GlassCard className="p-6 sm:p-8">
      <p className="text-sm font-medium text-[var(--brand)]">评估已完成</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">{definition.title}</h2>
      <p className="mt-3 text-lg leading-8 text-slate-600">
        你的回答已经记录，结果将供专业人员进一步参考。
      </p>
      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        <MetricCard
          label={definition.resultLabel ?? "初步总分"}
          value={submission.result.rawScore}
          emphasized
        />
        <MetricCard label="回答题数" value={submission.answers.length} />
        <MetricCard
          label="总耗时"
          value={`${Math.max(1, Math.round(submission.metrics.durationMs / 1000))} 秒`}
        />
      </div>
      <div className="mt-6 rounded-[24px] bg-slate-50 p-4">
        <p className="text-sm font-medium text-slate-500">Submission 结构化数据</p>
        <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-all text-sm leading-6 text-slate-700">
          {JSON.stringify(submission, null, 2)}
        </pre>
      </div>
      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <Link
          to="/home"
          className="inline-flex min-h-14 items-center justify-center rounded-2xl bg-[var(--brand)] px-5 py-4 text-lg font-medium text-white transition hover:bg-[var(--brand-dark)]"
        >
          返回任务中心
        </Link>
        <Link
          to="/admin"
          className="inline-flex min-h-14 items-center justify-center rounded-2xl bg-slate-100 px-5 py-4 text-lg font-medium text-slate-800 transition hover:bg-slate-200"
        >
          返回管理员页面
        </Link>
      </div>
    </GlassCard>
  );
}
