import { useCallback, useEffect, useState } from "react";
import { ActionButton, GlassCard, SurfaceCard } from "../components/ui";
import { repository } from "../repositories/apiRepository";
import type { AssessmentAssignment, AssessmentSubmission, Patient } from "../types/assessment";

const assessmentOptions = [
  { id: "scd-q9", label: "SCD-Q9 主观认知下降筛查" },
  { id: "gds-15", label: "GDS-15 老年抑郁量表" },
  { id: "ess", label: "ESS 爱泼沃斯嗜睡量表" },
  { id: "edinburgh-handedness", label: "爱丁堡利手量表" },
] as const;

export function AdminPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string>(
    assessmentOptions[0]?.id ?? "",
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [assignments, setAssignments] = useState<AssessmentAssignment[]>([]);
  const [submissions, setSubmissions] = useState<AssessmentSubmission[]>([]);

  const reload = useCallback(async (patientId?: string) => {
    const loadedPatients = await repository.getPatients();
    const resolvedPatientId = patientId || selectedPatientId || loadedPatients[0]?.id || "";
    setPatients(loadedPatients);
    if (!selectedPatientId && resolvedPatientId) setSelectedPatientId(resolvedPatientId);
    setAssignments(resolvedPatientId ? await repository.getAssignments(resolvedPatientId) : []);
    setSubmissions(await repository.getSubmissions());
  }, [selectedPatientId]);

  useEffect(() => { void reload(); }, [reload]);

  async function handleCreateAssignment() {
    setIsSubmitting(true);
    try {
      await repository.setCurrentPatient(selectedPatientId);
      const assignment = await repository.createAssignment(
        selectedPatientId,
        selectedAssessmentId,
      );
      const label =
        assessmentOptions.find((option) => option.id === selectedAssessmentId)?.label ??
        selectedAssessmentId;
      setMessage(`已派发 ${label}，任务编号：${assignment.assignmentId}`);
      await reload(selectedPatientId);
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "派发失败");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCreateBatchAssignments() {
    setIsSubmitting(true);
    try {
      await repository.setCurrentPatient(selectedPatientId);
      for (const option of assessmentOptions) {
        await repository.createAssignment(selectedPatientId, option.id);
      }
      setMessage("已为当前患者派发 SCD-Q9、GDS-15、ESS、爱丁堡利手量表四项演示任务。");
      await reload(selectedPatientId);
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "批量派发失败");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleResetDemoData() {
    try {
      await repository.resetAllDemoData();
      await reload("P001");
      setMessage("已重置演示任务、草稿和提交记录。");
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "重置失败");
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
      <GlassCard className="p-6">
        <p className="text-sm font-medium text-[var(--gold)]">Admin / Test Mode</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight">派发演示任务</h2>
        <p className="mt-3 text-lg leading-8 text-slate-600">
          当前支持派发 `SCD-Q9`、`GDS-15`、`ESS`、`爱丁堡利手量表`，用于打通首批 A 类量表业务闭环。
        </p>
        <label className="mt-6 block text-base font-medium text-slate-700" htmlFor="patient">
          选择患者
        </label>
        <select
          id="patient"
          value={selectedPatientId}
          onChange={(event) => { setSelectedPatientId(event.target.value); void reload(event.target.value); }}
          className="mt-2 min-h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-lg"
        >
          {patients.map((patient) => (
            <option key={patient.id} value={patient.id}>
              {patient.name}（{patient.id}）
            </option>
          ))}
        </select>
        <label className="mt-6 block text-base font-medium text-slate-700" htmlFor="assessment">
          选择量表
        </label>
        <select
          id="assessment"
          value={selectedAssessmentId}
          onChange={(event) => setSelectedAssessmentId(event.target.value)}
          className="mt-2 min-h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-lg"
        >
          {assessmentOptions.map((option) => (
            <option key={option.id} value={option.id}>
              {option.label}
            </option>
          ))}
        </select>
        <ActionButton
          type="button"
          disabled={isSubmitting}
          onClick={handleCreateAssignment}
          variant="navy"
          className="mt-6 w-full"
        >
          {isSubmitting ? "派发中..." : "派发当前量表"}
        </ActionButton>
        <ActionButton
          type="button"
          disabled={isSubmitting}
          onClick={handleCreateBatchAssignments}
          variant="secondary"
          className="mt-3 w-full"
        >
          派发全部 A 类演示量表
        </ActionButton>
        <ActionButton
          type="button"
          variant="secondary"
          className="mt-3 w-full"
          onClick={handleResetDemoData}
        >
          重置全部演示数据
        </ActionButton>
        {message ? (
          <p className="mt-4 rounded-2xl bg-[var(--brand-soft)] px-4 py-3 text-base text-[var(--brand-dark)]">
            {message}
          </p>
        ) : null}
      </GlassCard>

      <SurfaceCard className="p-6">
        <h3 className="text-2xl font-semibold tracking-tight">当前任务</h3>
        <div className="mt-4 grid gap-3">
          {assignments.length === 0 ? (
            <p className="text-lg text-slate-600">当前患者还没有任务。</p>
          ) : (
            assignments.map((assignment) => (
              <div
                key={assignment.assignmentId}
                className="rounded-[24px] border border-slate-200 bg-slate-50 px-4 py-4 text-base text-slate-700"
              >
                <div className="font-medium text-slate-900">{assignment.assessmentId}</div>
                <div className="mt-1 text-sm text-slate-500">状态：{assignment.status}</div>
                <div className="mt-1 text-sm text-slate-500">
                  任务号：{assignment.assignmentId}
                </div>
              </div>
            ))
          )}
        </div>
      </SurfaceCard>

      <SurfaceCard className="p-6 xl:col-span-2">
        <h3 className="text-2xl font-semibold tracking-tight">最近提交 JSON</h3>
        <div className="mt-4 grid gap-3">
          {submissions.length === 0 ? (
            <p className="text-lg text-slate-600">当前还没有提交记录。</p>
          ) : (
            submissions.slice(0, 3).map((submission) => (
              <div key={submission.assignmentId} className="rounded-[24px] bg-slate-50 p-4">
                <div className="text-sm text-slate-500">
                  {submission.assessmentId} / {submission.assignmentId}
                </div>
                <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-all text-sm leading-6 text-slate-700">
                  {JSON.stringify(submission, null, 2)}
                </pre>
              </div>
            ))
          )}
        </div>
      </SurfaceCard>
    </div>
  );
}
