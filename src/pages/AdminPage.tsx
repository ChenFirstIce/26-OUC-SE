import { useState } from "react";
import { repository } from "../repositories/mockRepository";

export function AdminPage() {
  const patients = repository.getPatients();
  const [selectedPatientId, setSelectedPatientId] = useState(patients[0]?.id ?? "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  const assignments = repository.getAssignments(selectedPatientId);

  function handleCreateAssignment() {
    setIsSubmitting(true);
    try {
      repository.setCurrentPatient(selectedPatientId);
      const assignment = repository.createAssignment(selectedPatientId, "scd-q9");
      setMessage(`已派发 SCD-Q9，任务编号：${assignment.assignmentId}`);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="grid gap-5">
      <section className="rounded-[28px] bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <p className="text-sm font-medium text-teal-700">Admin / Test Mode</p>
        <h2 className="mt-2 text-3xl font-semibold">派发演示任务</h2>
        <p className="mt-3 text-lg leading-8 text-slate-600">
          第一版只派发 SCD-Q9，用于打通患者端核心业务流程。
        </p>
        <label className="mt-6 block text-base font-medium text-slate-700" htmlFor="patient">
          选择患者
        </label>
        <select
          id="patient"
          value={selectedPatientId}
          onChange={(event) => setSelectedPatientId(event.target.value)}
          className="mt-2 min-h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-lg"
        >
          {patients.map((patient) => (
            <option key={patient.id} value={patient.id}>
              {patient.name}（{patient.id}）
            </option>
          ))}
        </select>
        <button
          type="button"
          disabled={isSubmitting}
          onClick={handleCreateAssignment}
          className="mt-6 min-h-14 rounded-2xl bg-teal-600 px-5 py-4 text-lg font-medium text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-teal-300"
        >
          {isSubmitting ? "派发中..." : "派发任务"}
        </button>
        {message ? (
          <p className="mt-4 rounded-2xl bg-teal-50 px-4 py-3 text-base text-teal-800">
            {message}
          </p>
        ) : null}
      </section>

      <section className="rounded-[28px] bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h3 className="text-2xl font-semibold">当前任务</h3>
        <div className="mt-4 grid gap-3">
          {assignments.length === 0 ? (
            <p className="text-lg text-slate-600">当前患者还没有任务。</p>
          ) : (
            assignments.map((assignment) => (
              <div
                key={assignment.assignmentId}
                className="rounded-2xl bg-slate-50 px-4 py-4 text-base text-slate-700"
              >
                {assignment.assessmentId} / {assignment.status} / {assignment.assignmentId}
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
