import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Bot, CheckCircle2, LoaderCircle, MessageCircleMore, RotateCcw, Send, UserRound } from "lucide-react";
import { resetMockInterview, sendInterviewMessage } from "../api/llm";
import { Button, Card, DemoNotice, Progress } from "../components/ui";
import { scdInitialMessage } from "../data/demo-data";
import { useDemoStore } from "../store/use-demo-store";
import { ApiError, type DemoSubmission, type InterviewMessage } from "../types";

const makeMessage = (role: InterviewMessage["role"], content: string): InterviewMessage => ({
  id: crypto.randomUUID(), role, content, createdAt: new Date().toISOString(),
});

export function ScdInterviewPage() {
  const storedMessages = useDemoStore((state) => state.interviewMessages);
  const storedProgress = useDemoStore((state) => state.interviewProgress);
  const storedStartedAt = useDemoStore((state) => state.interviewStartedAt);
  const status = useDemoStore((state) => state.statuses.scd_interview);
  const setStatus = useDemoStore((state) => state.setStatus);
  const setInterview = useDemoStore((state) => state.setInterview);
  const saveSubmission = useDemoStore((state) => state.saveSubmission);
  const resetTask = useDemoStore((state) => state.resetTask);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string>();
  const bottomRef = useRef<HTMLDivElement>(null);
  const messages = useMemo(
    () => storedMessages.length ? storedMessages : [makeMessage("assistant", scdInitialMessage)],
    [storedMessages],
  );
  const progress = storedMessages.length ? storedProgress : 0.15;
  const startedAt = storedStartedAt ?? new Date().toISOString();

  useEffect(() => {
    if (!storedMessages.length && status !== "completed") {
      setInterview(messages, progress, startedAt);
      setStatus("scd_interview", "in_progress");
    }
  }, [messages, progress, setInterview, setStatus, startedAt, status, storedMessages.length]);

  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), [messages, sending]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const clean = input.trim();
    if (!clean || sending || status === "completed") return;
    setError(undefined);
    setSending(true);
    const userMessage = makeMessage("user", clean);
    const withUser = [...messages, userMessage];
    setInput("");
    setInterview(withUser, progress, startedAt);
    try {
      const completedUserTurns = withUser.filter((message) => message.role === "user").length;
      const reply = await sendInterviewMessage("demo-scd-session", clean, completedUserTurns - 1);
      const nextMessages = [...withUser, makeMessage("assistant", reply.reply)];
      setInterview(nextMessages, reply.progress, startedAt);
      if (reply.completed) {
        const completedAt = new Date().toISOString();
        const submission: DemoSubmission<InterviewMessage[], { completed: true; progress: number }> = {
          assignmentId: "demo-scd-001",
          taskId: "demo-scd-interview",
          taskType: "scd_interview",
          answers: nextMessages,
          result: { completed: true, progress: reply.progress },
          metrics: { startedAt, completedAt, durationMs: Date.parse(completedAt) - Date.parse(startedAt) },
        };
        saveSubmission("scd_interview", submission);
      }
    } catch (caught) {
      setStatus("scd_interview", "failed");
      setError(caught instanceof ApiError ? caught.message : "发送失败，请稍后重试。");
    } finally {
      setSending(false);
    }
  }

  function restart() {
    resetTask("scd_interview");
    resetMockInterview();
    setError(undefined);
  }

  return (
    <div className="task-page">
      <div className="task-heading">
        <div><span className="eyebrow">C 类 · LLM 辅助</span><h1>SCD 结构化访谈</h1></div>
        <Button variant="ghost" onClick={restart}><RotateCcw size={18} />重新开始</Button>
      </div>
      <DemoNotice />
      <Progress value={status === "completed" ? 1 : progress} label="访谈进度" />
      <Card className="chat-card">
        <div className="chat-header"><MessageCircleMore size={20} /><span>认知访谈助手</span><small>{status === "completed" ? "已完成" : "访谈中"}</small></div>
        <div className="message-list" aria-live="polite">
          {messages.map((message) => (
            <div key={message.id} className={`message-row ${message.role}`}>
              <span className="avatar">{message.role === "assistant" ? <Bot size={20} /> : <UserRound size={20} />}</span>
              <div className="message-bubble">{message.content}</div>
            </div>
          ))}
          {sending && <div className="message-row assistant"><span className="avatar"><Bot size={20} /></span><div className="message-bubble typing"><LoaderCircle size={18} className="spin" />正在整理下一条问题…</div></div>}
          <div ref={bottomRef} />
        </div>
        {status === "completed" ? (
          <div className="complete-panel"><CheckCircle2 size={26} /><div><strong>访谈已完成</strong><span>回答已保存，后续由专业人员查看。</span></div></div>
        ) : (
          <form className="chat-form" onSubmit={submit}>
            <label htmlFor="interview-answer">请输入您的回答</label>
            <div className="chat-input-row">
              <textarea id="interview-answer" rows={2} value={input} onChange={(event) => setInput(event.target.value)} placeholder="请按您的实际感受回答…" disabled={sending} />
              <Button type="submit" disabled={!input.trim() || sending} aria-label="发送回答"><Send size={20} /><span>发送</span></Button>
            </div>
            {error && <div className="error-message" role="alert">{error} 您可以再次点击发送重试。</div>}
          </form>
        )}
      </Card>
    </div>
  );
}
