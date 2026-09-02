import { useMemo } from "react";
import { Link } from "react-router-dom";
import { getAssessmentDefinition } from "../data/assessments";
import { repository } from "../repositories/mockRepository";

export function HomePage() {
  const patient = repository.getCurrentPatient();
  const assignments = repository.getAssignments(patient.id);

  const stats = useMemo(
    () => ({
      pending: assignments.filter((item) => item.status === "pending").length,
      inProgress: assignments.filter((item) => item.status === "in_progress").length,
      completed: assignments.filter((item) => item.status === "completed").length,
    }),
    [assignments],
  );

  return (
    <div className="grid gap-5">
      <section className="rounded-[28px] bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <p className="text-sm font-medium text-teal-700">患者任务中心</p>
        <h2 className="mt-2 text-3xl font-semibold">{patient.name}</h2>
        <p className="mt-3 text-lg leading-8 text-slate-600">
          请从下方任务开始评估。系统会自动保存草稿，并在提交后记录初步分数。
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="text-sm text-slate-500">待完成</div>
            <div className="mt-2 text-3xl font-semibold">{stats.pending}</div>
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="text-sm text-slate-500">进行中</div>
            <div className="mt-2 text-3xl font-semibold">{stats.inProgress}</div>
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="text-sm text-slate-500">已完成</div>
            <div className="mt-2 text-3xl font-semibold">{stats.completed}</div>
          </div>
        </div>
      </section>

      <section className="grid gap-4">
        {assignments.length === 0 ? (
          <div className="rounded-[28px] bg-white p-6 text-lg text-slate-600 shadow-sm ring-1 ring-slate-200">
            暂无任务。请先到管理员模式派发 SCD-Q9。
          </div>
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
                  : "开始评估";

            const target =
              assignment.status === "completed"
                ? `/assessment/${assignment.assessmentId}/complete?assignmentId=${assignment.assignmentId}`
                : `/assessment/${assignment.assessmentId}?assignmentId=${assignment.assignmentId}`;

            return (
              <article
                key={assignment.assignmentId}
                className="rounded-[28px] bg-white p-6 shadow-sm ring-1 ring-slate-200"
              >
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-medium text-teal-700">
                      {assignment.status === "pending"
                        ? "待完成"
                        : assignment.status === "in_progress"
                          ? "进行中"
                          : "已完成"}
                    </p>
                    <h3 className="mt-2 text-2xl font-semibold">{definition.title}</h3>
                    <p className="mt-2 text-base leading-7 text-slate-600">
                      预计时长 {definition.estimatedMinutes}
                    </p>
                  </div>
                  <Link
                    to={target}
                    className="inline-flex min-h-12 items-center justify-center rounded-full bg-teal-600 px-5 py-3 text-lg font-medium text-white transition hover:bg-teal-700"
                  >
                    {actionLabel}
                  </Link>
                </div>
              </article>
            );
          })
        )}
      </section>
    </div>
  );
}
