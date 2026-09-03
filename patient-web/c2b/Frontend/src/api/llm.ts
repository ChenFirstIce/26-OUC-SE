import { z } from "zod";
import { ApiError, type InterviewReply, type OpenAnswerAnalysis } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";
const useMock = import.meta.env.VITE_USE_MOCK_API !== "false";

const interviewReplySchema = z.object({
  reply: z.string().min(1),
  progress: z.number().min(0).max(1),
  completed: z.boolean(),
});

const openAnswerSchema = z.object({
  recorded: z.literal(true),
  analysis: z.object({
    candidateScore: z.number(),
    explanation: z.string(),
  }),
});

const mockReplies: InterviewReply[] = [
  { reply: "这种变化大约从什么时候开始？请按您的实际感受回答。", progress: 0.4, completed: false },
  { reply: "这种变化是否影响过您的日常安排？可以简单举一个例子。", progress: 0.7, completed: false },
  { reply: "感谢您的回答，本次演示访谈已完成。您的回答将由专业人员进一步查看。", progress: 1, completed: true },
];

let mockTurn = 0;

const delay = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

async function parseResponse(response: Response): Promise<unknown> {
  if (!response.ok) {
    if (response.status === 429) throw new ApiError("RATE_LIMITED", "请求较多，请稍后重试。", true);
    if (response.status === 503) throw new ApiError("MODEL_UNAVAILABLE", "智能服务暂时不可用。", true);
    throw new ApiError("INTERNAL_ERROR", "服务暂时出现问题。", response.status >= 500);
  }
  return response.json();
}

export function resetMockInterview(): void {
  mockTurn = 0;
}

export async function sendInterviewMessage(sessionId: string, message: string, mockTurnHint?: number): Promise<InterviewReply> {
  if (useMock) {
    await delay(700);
    const turn = mockTurnHint ?? mockTurn;
    const reply = mockReplies[Math.min(turn, mockReplies.length - 1)];
    mockTurn = turn + 1;
    return reply;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/llm/session/${encodeURIComponent(sessionId)}/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    return interviewReplySchema.parse(await parseResponse(response));
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof z.ZodError) throw new ApiError("INVALID_MODEL_OUTPUT", "服务返回内容无法识别。", true);
    throw new ApiError("NETWORK_ERROR", "网络连接失败，请检查网络后重试。", true);
  }
}

export async function analyzeOpenAnswer(payload: {
  assignmentId: string;
  questionId: string;
  answer: string;
}): Promise<{ recorded: true; analysis: OpenAnswerAnalysis }> {
  if (useMock) {
    await delay(900);
    return {
      recorded: true,
      analysis: { candidateScore: 1, explanation: "DEMO 内部分析：回答表达了两个对象的共同类别。" },
    };
  }

  try {
    const response = await fetch(`${API_BASE_URL}/llm/open-answer/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return openAnswerSchema.parse(await parseResponse(response));
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof z.ZodError) throw new ApiError("INVALID_MODEL_OUTPUT", "服务返回内容无法识别。", true);
    throw new ApiError("NETWORK_ERROR", "网络连接失败，请检查网络后重试。", true);
  }
}
