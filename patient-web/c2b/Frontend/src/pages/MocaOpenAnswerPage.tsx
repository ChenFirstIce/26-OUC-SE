import { type FormEvent, useState } from "react";
import { CheckCircle2, LoaderCircle, RotateCcw, Sparkles } from "lucide-react";
import { analyzeOpenAnswer } from "../api/llm";
import { Button, Card, DemoNotice } from "../components/ui";
import { mocaOpenTasks } from "../data/moca-open";
import { useDemoStore } from "../store/use-demo-store";
import { ApiError, type DemoSubmission, type OpenAnswerAnalysis } from "../types";

export function MocaOpenAnswerPage() {
  const answers = useDemoStore((state) => state.openAnswers ?? {});
  const status = useDemoStore((state) => state.statuses.moca_open_answer);
  const submission = useDemoStore((state) => state.submissions.moca_open_answer);
  const setAnswer = useDemoStore((state) => state.setOpenAnswer);
  const setStatus = useDemoStore((state) => state.setStatus);
  const saveSubmission = useDemoStore((state) => state.saveSubmission);
  const resetTask = useDemoStore((state) => state.resetTask);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string>();
  const [startedAt] = useState(new Date().toISOString());
  const allAnswered = mocaOpenTasks.every((task) => answers[task.id]?.trim());

  async function submit(event: FormEvent) {
    event.preventDefault();
    const cleanAnswers = Object.fromEntries(mocaOpenTasks.map((task) => [task.id, answers[task.id]?.trim() ?? ""]));
    if (!mocaOpenTasks.every((task) => cleanAnswers[task.id]) || analyzing || status === "completed") return;
    setAnalyzing(true);
    setError(undefined);
    setStatus("moca_open_answer", "in_progress");
    try {
      const response = await analyzeOpenAnswer({ assignmentId: "demo-moca-001", answers: cleanAnswers });
      const completedAt = new Date().toISOString();
      const result: DemoSubmission<Record<string, string>, OpenAnswerAnalysis> = {
        assignmentId: "demo-moca-001", taskId: "demo-moca-open-answer", taskType: "moca_open_answer",
        answers: cleanAnswers, result: response.analysis,
        metrics: { startedAt, completedAt, durationMs: Date.parse(completedAt) - Date.parse(startedAt) },
      };
      saveSubmission("moca_open_answer", result);
    } catch (caught) {
      setStatus("moca_open_answer", "failed");
      setError(caught instanceof ApiError ? caught.message : "分析暂时失败，请重试。");
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="task-page narrow">
      <div className="task-heading"><div><span className="eyebrow">C 类 · LLM 辅助</span><h1>MoCA-B 开放题</h1></div><Button variant="ghost" onClick={() => resetTask("moca_open_answer")}><RotateCcw size={18} />重新开始</Button></div>
      <DemoNotice />
      {status === "completed" ? (
        <Card className="success-card">
          <span className="success-icon"><CheckCircle2 size={38} /></span><h2>回答已记录</h2><p>您的回答已经安全保存，后续将由专业人员查看。</p>
          <div className="answer-review">
            <span>您提交的回答</span>
            {mocaOpenTasks.map((task) => <p key={task.id}><strong>{task.title}：</strong>{String((submission?.answers as Record<string, string> | undefined)?.[task.id] ?? answers[task.id] ?? "")}</p>)}
          </div>
          <p className="privacy-note">内部候选分数与分析依据不会在患者端展示。</p>
        </Card>
      ) : (
        <Card className="question-card">
          <div className="question-badge"><Sparkles size={18} />开放回答</div>
          <h2>请完成以下 2 个 MoCA-B 开放题子任务。</h2>
          <p className="question-help">没有唯一的表达方式，请用您觉得自然的语言回答；候选分只供专业人员参考。</p>
          <form onSubmit={submit}>
            {mocaOpenTasks.map((task) => (
              <div className="open-task-field" key={task.id}>
                <label htmlFor={task.id}>{task.title}</label>
                <p>{task.prompt}</p>
                <textarea id={task.id} rows={4} maxLength={500} value={answers[task.id] ?? ""} onChange={(event) => setAnswer(task.id, event.target.value)} placeholder={task.hint} disabled={analyzing} />
                <div className="field-meta"><span>{(answers[task.id] ?? "").length} / 500 字</span></div>
              </div>
            ))}
            {error && <div className="error-message" role="alert">{error}</div>}
            <Button className="full-button" type="submit" disabled={!allAnswered || analyzing}>
              {analyzing ? <><LoaderCircle size={20} className="spin" />正在记录与分析…</> : "确认提交"}
            </Button>
          </form>
        </Card>
      )}
    </div>
  );
}
