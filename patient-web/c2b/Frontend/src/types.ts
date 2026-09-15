export type TaskStatus = "not_started" | "in_progress" | "completed" | "failed";
export type TaskType = "scd_interview" | "moca_open_answer" | "boston_naming" | "trail_making";

export interface TaskMetrics {
  startedAt: string;
  completedAt?: string;
  durationMs?: number;
}

export interface DemoSubmission<TAnswer = unknown, TResult = unknown> {
  assignmentId: string;
  taskId: string;
  taskType: TaskType;
  answers: TAnswer;
  result: TResult;
  metrics: TaskMetrics;
}

export interface InterviewMessage {
  id: string;
  role: "assistant" | "user";
  content: string;
  createdAt: string;
}

export interface InterviewReply {
  reply: string;
  progress: number;
  completed: boolean;
}

export interface OpenAnswerItemAnalysis {
  questionId: string;
  taskType: "payment" | "abstraction";
  prompt: string;
  answer: string;
  candidateScore: number;
  explanation: string;
}

export interface OpenAnswerAnalysis {
  items: OpenAnswerItemAnalysis[];
  candidateTotal: number;
  maxScore: number;
  explanation: string;
}

export interface BostonAnswer {
  questionId: string;
  answer: string;
  startedAt: string;
  submittedAt: string;
  durationMs: number;
  hintUsed: boolean;
  provisionalScore: 0 | 1;
}

export type SttForm = "A" | "B";
export type SttPhase = "practice" | "test";
export type SttShape = "square" | "circle";
export type SttAgeBand = "50-59" | "60-69" | "70-79";

export interface SttCoordinateSystem {
  width: number;
  height: number;
  origin: "top-left";
  point: "shape-center";
  unit: "px";
}

export interface TrailNode {
  id: string;
  label: string;
  shape: SttShape;
  x: number;
  y: number;
  sourceX: number;
  sourceY: number;
  isTarget: boolean;
  order?: number;
}

export interface TrailEvent {
  nodeId: string;
  label: string;
  shape: SttShape;
  expectedNodeId: string;
  timestampMs: number;
  correct: boolean;
}

export interface TrailResult {
  form: SttForm;
  phase: SttPhase;
  ageBand: SttAgeBand;
  thresholdSeconds: number;
  clickedSequence: string[];
  events: TrailEvent[];
  durationMs: number;
  errorCount: number;
  completed: boolean;
  abnormal?: boolean;
  interpretation?: string;
}

export type ApiErrorCode =
  | "NETWORK_ERROR"
  | "RATE_LIMITED"
  | "MODEL_UNAVAILABLE"
  | "INVALID_MODEL_OUTPUT"
  | "INTERNAL_ERROR";

export class ApiError extends Error {
  constructor(
    public readonly code: ApiErrorCode,
    message: string,
    public readonly retryable: boolean,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
