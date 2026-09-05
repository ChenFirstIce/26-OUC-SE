import type { AssessmentAssignment, AssessmentDraft, AssessmentSubmission, AnswerValue, Patient } from "../types/assessment";
const apiBase = import.meta.env.VITE_API_BASE_URL ?? "/api";
async function request<T>(path: string, init?: RequestInit): Promise<T> { const response = await fetch(`${apiBase}${path}`, { ...init, headers: { "Content-Type": "application/json", ...init?.headers } }); if (!response.ok) { const payload = await response.json().catch(() => null) as { error?: { message?: string } } | null; throw new Error(payload?.error?.message ?? `请求失败（${response.status}）`); } return response.status === 204 ? undefined as T : response.json() as Promise<T>; }
export const repository = {
  getCurrentPatient: () => request<Patient>("/patients/current"),
  setCurrentPatient: (patientId: string) => request<Patient>("/patients/current", { method: "PUT", body: JSON.stringify({ patientId }) }),
  getPatients: () => request<Patient[]>("/patients"),
  getAssignments: (patientId: string) => request<AssessmentAssignment[]>(`/patients/${encodeURIComponent(patientId)}/assignments`),
  createAssignment: (patientId: string, assessmentId: string) => request<AssessmentAssignment>("/assignments", { method: "POST", body: JSON.stringify({ patientId, assessmentId }) }),
  getDraft: (assignmentId: string) => request<AssessmentDraft | null>(`/assignments/${encodeURIComponent(assignmentId)}/draft`),
  saveDraft: (input: { assignmentId: string; patientId: string; assessmentId: string; startedAt: string; questionId: string; value: AnswerValue }) => request<AssessmentDraft>(`/assignments/${encodeURIComponent(input.assignmentId)}/draft`, { method: "PUT", body: JSON.stringify(input) }),
  submitAssessment: (input: { assignmentId: string; patientId: string; assessmentId: string; startedAt: string; answers: Array<{ questionId: string; value: AnswerValue }> }) => request<AssessmentSubmission>(`/assignments/${encodeURIComponent(input.assignmentId)}/submit`, { method: "POST", body: JSON.stringify(input) }),
  getLatestSubmission: (assignmentId: string) => request<AssessmentSubmission | null>(`/assignments/${encodeURIComponent(assignmentId)}/submission`),
  getSubmissions: (patientId?: string) => request<AssessmentSubmission[]>(`/submissions${patientId ? `?patientId=${encodeURIComponent(patientId)}` : ""}`),
  resetAllDemoData: () => request<void>("/demo", { method: "DELETE" }),
};
