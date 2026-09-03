import { getAssessmentDefinition, scoreAnswer } from "../data/assessments";
import {
  ensureStorageSeed,
  getAssignmentsStorage,
  getCurrentPatientId,
  getDemoPatients,
  getDraftsStorage,
  getSubmissionsStorage,
  resetDemoStorage,
  setAssignmentsStorage,
  setCurrentPatientId,
  setDraftsStorage,
  setSubmissionsStorage,
} from "../lib/storage";
import type {
  AssessmentAssignment,
  AssessmentDraft,
  AssessmentSubmission,
  AnswerValue,
  Patient,
  ScoredAnswer,
} from "../types/assessment";

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}`;
}

function toScoredAnswer(
  assessmentId: string,
  questionId: string,
  value: AnswerValue,
): ScoredAnswer {
  return {
    questionId,
    value,
    score: scoreAnswer(assessmentId, questionId, value),
  };
}

export const repository = {
  getCurrentPatient(): Patient {
    ensureStorageSeed();
    const patientId = getCurrentPatientId();
    return getDemoPatients().find((patient) => patient.id === patientId) ?? getDemoPatients()[0];
  },

  setCurrentPatient(patientId: string) {
    setCurrentPatientId(patientId);
  },

  getPatients() {
    ensureStorageSeed();
    return getDemoPatients();
  },

  getAssignments(patientId: string) {
    return getAssignmentsStorage()
      .filter((assignment) => assignment.patientId === patientId)
      .sort((left, right) => right.createdAt.localeCompare(left.createdAt));
  },

  createAssignment(patientId: string, assessmentId: string) {
    const nextAssignment: AssessmentAssignment = {
      assignmentId: makeId("assignment"),
      patientId,
      assessmentId,
      createdAt: new Date().toISOString(),
      status: "pending",
    };
    const assignments = [nextAssignment, ...getAssignmentsStorage()];
    setAssignmentsStorage(assignments);
    return nextAssignment;
  },

  getActiveAssignment(patientId: string, assessmentId: string, assignmentId?: string) {
    const assignments = this.getAssignments(patientId);

    if (assignmentId) {
      return assignments.find((assignment) => assignment.assignmentId === assignmentId);
    }

    return assignments.find(
      (assignment) =>
        assignment.assessmentId === assessmentId &&
        assignment.status !== "completed",
    );
  },

  getDraft(assignmentId: string) {
    return getDraftsStorage().find((draft) => draft.assignmentId === assignmentId);
  },

  saveDraft(input: {
    assignmentId: string;
    patientId: string;
    assessmentId: string;
    startedAt: string;
    questionId: string;
    value: AnswerValue;
  }) {
    const drafts = getDraftsStorage();
    const scoredAnswer = toScoredAnswer(
      input.assessmentId,
      input.questionId,
      input.value,
    );
    const existingDraft = drafts.find((draft) => draft.assignmentId === input.assignmentId);
    const answers = existingDraft ? [...existingDraft.answers] : [];
    const answerIndex = answers.findIndex((answer) => answer.questionId === input.questionId);

    if (answerIndex >= 0) {
      answers[answerIndex] = scoredAnswer;
    } else {
      answers.push(scoredAnswer);
    }

    const nextDraft: AssessmentDraft = {
      assignmentId: input.assignmentId,
      patientId: input.patientId,
      assessmentId: input.assessmentId,
      startedAt: existingDraft?.startedAt ?? input.startedAt,
      updatedAt: new Date().toISOString(),
      answers,
    };

    const nextDrafts = drafts.filter((draft) => draft.assignmentId !== input.assignmentId);
    nextDrafts.unshift(nextDraft);
    setDraftsStorage(nextDrafts);

    const assignments: AssessmentAssignment[] = getAssignmentsStorage().map((assignment) =>
      assignment.assignmentId === input.assignmentId
        ? {
            ...assignment,
            status: "in_progress",
            startedAt: assignment.startedAt ?? input.startedAt,
          }
        : assignment,
    );
    setAssignmentsStorage(assignments);

    return nextDraft;
  },

  submitAssessment(input: {
    assignmentId: string;
    patientId: string;
    assessmentId: string;
    startedAt: string;
    answers: Array<{ questionId: string; value: AnswerValue }>;
  }) {
    const definition = getAssessmentDefinition(input.assessmentId);
    if (!definition) {
      throw new Error("Assessment definition not found.");
    }

    const completedAt = new Date().toISOString();
    const answers = input.answers.map((answer) =>
      toScoredAnswer(input.assessmentId, answer.questionId, answer.value),
    );
    const submission: AssessmentSubmission = {
      assignmentId: input.assignmentId,
      patientId: input.patientId,
      assessmentId: input.assessmentId,
      startedAt: input.startedAt,
      completedAt,
      answers,
      result: definition.scoreAnswers(answers),
      metrics: {
        durationMs:
          new Date(completedAt).getTime() - new Date(input.startedAt).getTime(),
      },
    };

    const submissions = getSubmissionsStorage();
    submissions.unshift(submission);
    setSubmissionsStorage(submissions);

    const assignments: AssessmentAssignment[] = getAssignmentsStorage().map((assignment) =>
      assignment.assignmentId === input.assignmentId
        ? {
            ...assignment,
            status: "completed",
            startedAt: assignment.startedAt ?? input.startedAt,
            completedAt,
          }
        : assignment,
    );
    setAssignmentsStorage(assignments);

    const drafts = getDraftsStorage().filter((draft) => draft.assignmentId !== input.assignmentId);
    setDraftsStorage(drafts);

    return submission;
  },

  getLatestSubmission(assignmentId: string) {
    return getSubmissionsStorage().find(
      (submission) => submission.assignmentId === assignmentId,
    );
  },

  getSubmissions(patientId?: string) {
    const submissions = getSubmissionsStorage().sort((left, right) =>
      right.completedAt.localeCompare(left.completedAt),
    );

    if (!patientId) {
      return submissions;
    }

    return submissions.filter((submission) => submission.patientId === patientId);
  },

  resetAllDemoData() {
    resetDemoStorage();
  },
};
