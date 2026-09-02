import { Link, useSearchParams, useParams } from "react-router-dom";
import { getAssessmentDefinition } from "../data/assessments";
import { repository } from "../repositories/mockRepository";

export function AssessmentCompletePage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const assignmentId = searchParams.get("assignmentId") ?? "";
  const definition = id ? getAssessmentDefinition(id) : undefined;
  const submission = repository.getLatestSubmission(assignmentId);

  if (!definition || !submission) {
    return (
      <div className="rounded-[28px] bg-white p-6 text-lg text-slate-600 shadow-sm ring-1 ring-slate-200">
        未找到提交记录。
      </div>
    );
  }

  return (
    <section className="rounded-[28px] bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
      <p className="text-sm font-medium text-teal-700">评估已完成</p>
      <h2 className="mt-2 text-3xl font-semibold">{definition.title}</h2>
      <p className="mt-3 text-lg leading-8 text-slate-600">
        你的回答已经记录，结果将供专业人员进一步参考。
      </p>
      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        <div className="rounded-2xl bg-slate-50 p-4">
          <div className="text-sm text-slate-500">初步总分</div>
          <div className="mt-2 text-3xl font-semibold">{submission.result.rawScore}</div>
        </div>
        <div className="rounded-2xl bg-slate-50 p-4">
          <div className="text-sm text-slate-500">回答题数</div>
          <div className="mt-2 text-3xl font-semibold">{submission.answers.length}</div>
        </div>
        <div className="rounded-2xl bg-slate-50 p-4">
          <div className="text-sm text-slate-500">总耗时</div>
          <div className="mt-2 text-3xl font-semibold">
            {Math.max(1, Math.round(submission.metrics.durationMs / 1000))} 秒
          </div>
        </div>
      </div>
      <div className="mt-6 rounded-2xl bg-slate-50 p-4">
        <p className="text-sm font-medium text-slate-500">Submission 结构化数据</p>
        <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-all text-sm leading-6 text-slate-700">
          {JSON.stringify(submission, null, 2)}
        </pre>
      </div>
      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <Link
          to="/home"
          className="inline-flex min-h-14 items-center justify-center rounded-2xl bg-teal-600 px-5 py-4 text-lg font-medium text-white transition hover:bg-teal-700"
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
    </section>
  );
}
