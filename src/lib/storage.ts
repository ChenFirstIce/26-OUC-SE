import type {
  AssessmentAssignment,
  AssessmentDraft,
  AssessmentSubmission,
  Patient,
} from "../types/assessment";

const STORAGE_KEYS = {
  currentPatientId: "patient-app/current-patient-id",
  assignments: "patient-app/assignments",
  drafts: "patient-app/drafts",
  submissions: "patient-app/submissions",
};

const demoPatient: Patient = {
  id: "P001",
  name: "演示患者",
};

function readJson<T>(key: string, fallback: T) {
  const raw = window.localStorage.getItem(key);
  if (!raw) {
    return fallback;
  }

  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeJson(key: string, value: unknown) {
  window.localStorage.setItem(key, JSON.stringify(value));
}

export function ensureStorageSeed() {
  if (!window.localStorage.getItem(STORAGE_KEYS.currentPatientId)) {
    window.localStorage.setItem(STORAGE_KEYS.currentPatientId, demoPatient.id);
  }

  if (!window.localStorage.getItem(STORAGE_KEYS.assignments)) {
    writeJson(STORAGE_KEYS.assignments, []);
  }

  if (!window.localStorage.getItem(STORAGE_KEYS.drafts)) {
    writeJson(STORAGE_KEYS.drafts, []);
  }

  if (!window.localStorage.getItem(STORAGE_KEYS.submissions)) {
    writeJson(STORAGE_KEYS.submissions, []);
  }
}

export function getDemoPatients() {
  return [demoPatient];
}

export function getCurrentPatientId() {
  ensureStorageSeed();
  return window.localStorage.getItem(STORAGE_KEYS.currentPatientId) ?? demoPatient.id;
}

export function setCurrentPatientId(patientId: string) {
  window.localStorage.setItem(STORAGE_KEYS.currentPatientId, patientId);
}

export function getAssignmentsStorage() {
  ensureStorageSeed();
  return readJson<AssessmentAssignment[]>(STORAGE_KEYS.assignments, []);
}

export function setAssignmentsStorage(assignments: AssessmentAssignment[]) {
  writeJson(STORAGE_KEYS.assignments, assignments);
}

export function getDraftsStorage() {
  ensureStorageSeed();
  return readJson<AssessmentDraft[]>(STORAGE_KEYS.drafts, []);
}

export function setDraftsStorage(drafts: AssessmentDraft[]) {
  writeJson(STORAGE_KEYS.drafts, drafts);
}

export function getSubmissionsStorage() {
  ensureStorageSeed();
  return readJson<AssessmentSubmission[]>(STORAGE_KEYS.submissions, []);
}

export function setSubmissionsStorage(submissions: AssessmentSubmission[]) {
  writeJson(STORAGE_KEYS.submissions, submissions);
}

export function resetDemoStorage() {
  window.localStorage.removeItem(STORAGE_KEYS.assignments);
  window.localStorage.removeItem(STORAGE_KEYS.drafts);
  window.localStorage.removeItem(STORAGE_KEYS.submissions);
  window.localStorage.setItem(STORAGE_KEYS.currentPatientId, demoPatient.id);
  ensureStorageSeed();
}
