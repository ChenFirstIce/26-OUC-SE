export type QuestionType =
  | "boolean"
  | "single-choice"
  | "multiple-choice"
  | "scale"
  | "number"
  | "text"
  | "date"
  | "time";

export type AnswerValue = boolean | string | string[] | number | null;

export interface QuestionOption {
  label: string;
  value: string;
}

export interface AssessmentQuestion {
  id: string;
  type: QuestionType;
  title: string;
  description?: string;
  options?: QuestionOption[];
}

export interface ScoredAnswer {
  questionId: string;
  value: AnswerValue;
  score: number;
}

export interface AssessmentResult {
  rawScore: number;
}

export interface AssessmentMetrics {
  durationMs: number;
}

export interface AssessmentDefinition {
  id: string;
  title: string;
  estimatedMinutes: string;
  intro: string;
  questions: AssessmentQuestion[];
  scoreAnswers: (answers: ScoredAnswer[]) => AssessmentResult;
}

export type AssignmentStatus = "pending" | "in_progress" | "completed";

export interface AssessmentAssignment {
  assignmentId: string;
  patientId: string;
  assessmentId: string;
  createdAt: string;
  status: AssignmentStatus;
  startedAt?: string;
  completedAt?: string;
}

export interface AssessmentDraft {
  assignmentId: string;
  patientId: string;
  assessmentId: string;
  startedAt: string;
  updatedAt: string;
  answers: ScoredAnswer[];
}

export interface AssessmentSubmission {
  assignmentId: string;
  patientId: string;
  assessmentId: string;
  startedAt: string;
  completedAt: string;
  answers: ScoredAnswer[];
  result: AssessmentResult;
  metrics: AssessmentMetrics;
}

export interface Patient {
  id: string;
  name: string;
}
