import { Link, useParams, useSearchParams } from "react-router-dom";
import { GlassCard, StatusPill, SurfaceCard } from "../components/ui";
import { getAssessmentDefinition } from "../data/assessments";
import { repository } from "../repositories/mockRepository";

export function AssessmentIntroPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const assignmentId = searchParams.get("assignmentId") ?? undefined;
  const patient = repository.getCurrentPatient();
  const definition = id ? getAssessmentDefinition(id) : undefined;
  const assignment = id
    ? repository.getActiveAssignment(patient.id, id, assignmentId)
    : undefined;

  if (!definition || !assignment) {
    return (
      <SurfaceCard className="p-6 text-lg text-slate-600">
        未找到任务说明，请先回到任务中心重新进入。
      </SurfaceCard>
    );
  }

  return (
    <GlassCard className="p-6 sm:p-8">
      <p className="text-sm font-medium text-[var(--brand)]">评估说明</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">{definition.title}</h2>
      <p className="mt-4 text-lg leading-8 text-slate-600">{definition.intro}</p>

      <div className="mt-6 flex flex-wrap gap-3">
        <StatusPill>预计时长 {definition.estimatedMinutes}</StatusPill>
        <StatusPill tone="brand">共 {definition.questions.length} 题</StatusPill>
        <StatusPill>任务号 {assignment.assignmentId}</StatusPill>
      </div>

      <div className="mt-8 rounded-[24px] bg-slate-50 p-5 text-base leading-7 text-slate-700">
        <p>开始前请注意：</p>
        <ul className="mt-3 grid gap-2">
          <li>请根据近期实际情况作答。</li>
          <li>系统会自动保存当前作答进度。</li>
          <li>完成后只展示记录结果，不展示诊断结论。</li>
        </ul>
      </div>

      <div className="mt-8 flex flex-col gap-3 sm:flex-row">
        <Link
          to={`/assessment/${definition.id}?assignmentId=${assignment.assignmentId}`}
          className="inline-flex min-h-14 items-center justify-center rounded-2xl bg-[var(--brand)] px-5 py-4 text-lg font-medium text-white transition hover:bg-[var(--brand-dark)]"
        >
          开始评估
        </Link>
        <Link
          to="/home"
          className="inline-flex min-h-14 items-center justify-center rounded-2xl bg-slate-100 px-5 py-4 text-lg font-medium text-slate-800 transition hover:bg-slate-200"
        >
          返回任务中心
        </Link>
      </div>
    </GlassCard>
  );
}
