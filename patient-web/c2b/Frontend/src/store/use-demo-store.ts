import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { BostonAnswer, DemoSubmission, InterviewMessage, TaskStatus, TaskType, TrailResult } from "../types";

interface DemoState {
  statuses: Record<TaskType, TaskStatus>;
  interviewMessages: InterviewMessage[];
  interviewProgress: number;
  interviewStartedAt?: string;
  mocaMessages: InterviewMessage[];
  mocaProgress: number;
  mocaStartedAt?: string;
  openAnswers: Record<string, string>;
  bostonAnswers: BostonAnswer[];
  trailDraft?: TrailResult;
  submissions: Partial<Record<TaskType, DemoSubmission>>;
  setStatus: (task: TaskType, status: TaskStatus) => void;
  setInterview: (messages: InterviewMessage[], progress: number, startedAt?: string) => void;
  setMoca: (messages: InterviewMessage[], progress: number, startedAt?: string) => void;
  setOpenAnswer: (questionId: string, answer: string) => void;
  setBostonAnswers: (answers: BostonAnswer[]) => void;
  setTrailDraft: (result?: TrailResult) => void;
  saveSubmission: (task: TaskType, submission: DemoSubmission) => void;
  resetTask: (task: TaskType) => void;
}

const initialStatuses: Record<TaskType, TaskStatus> = {
  scd_interview: "not_started",
  moca_open_answer: "not_started",
  boston_naming: "not_started",
  trail_making: "not_started",
};

export const useDemoStore = create<DemoState>()(
  persist(
    (set) => ({
      statuses: initialStatuses,
      interviewMessages: [],
      interviewProgress: 0,
      mocaMessages: [],
      mocaProgress: 0,
      openAnswers: {},
      bostonAnswers: [],
      submissions: {},
      setStatus: (task, status) => set((state) => ({ statuses: { ...state.statuses, [task]: status } })),
      setInterview: (messages, progress, startedAt) => set({ interviewMessages: messages, interviewProgress: progress, interviewStartedAt: startedAt }),
      setMoca: (messages, progress, startedAt) => set({ mocaMessages: messages, mocaProgress: progress, mocaStartedAt: startedAt }),
      setOpenAnswer: (questionId, answer) => set((state) => ({ openAnswers: { ...(state.openAnswers ?? {}), [questionId]: answer } })),
      setBostonAnswers: (bostonAnswers) => set({ bostonAnswers }),
      setTrailDraft: (trailDraft) => set({ trailDraft }),
      saveSubmission: (task, submission) => set((state) => ({
        submissions: { ...state.submissions, [task]: submission },
        statuses: { ...state.statuses, [task]: "completed" },
      })),
      resetTask: (task) => set((state) => ({
        statuses: { ...state.statuses, [task]: "not_started" },
        submissions: { ...state.submissions, [task]: undefined },
        ...(task === "scd_interview" ? { interviewMessages: [], interviewProgress: 0, interviewStartedAt: undefined } : {}),
        ...(task === "moca_open_answer" ? { mocaMessages: [], mocaProgress: 0, mocaStartedAt: undefined, openAnswers: {} } : {}),
        ...(task === "boston_naming" ? { bostonAnswers: [] } : {}),
        ...(task === "trail_making" ? { trailDraft: undefined } : {}),
      })),
    }),
    { name: "ad-patient-demo-v1" },
  ),
);
