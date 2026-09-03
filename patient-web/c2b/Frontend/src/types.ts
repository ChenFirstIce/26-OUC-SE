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

export interface OpenAnswerAnalysis {
  candidateScore: number;
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

export interface TrailNode {
  id: string;
  label: string;
  x: number;
  y: number;
}

export interface TrailEvent {
  nodeId: string;
  timestampMs: number;
  correct: boolean;
}

export interface TrailResult {
  clickedSequence: string[];
  events: TrailEvent[];
  durationMs: number;
  errorCount: number;
  completed: boolean;
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
