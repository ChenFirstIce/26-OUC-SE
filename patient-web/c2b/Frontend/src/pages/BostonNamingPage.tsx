import { type FormEvent, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, CheckCircle2, Clock3, ImageIcon, Lightbulb, RotateCcw } from "lucide-react";
import { Button, Card, DemoNotice, Progress } from "../components/ui";
import { bostonQuestions } from "../data/demo-data";
import { useDemoStore } from "../store/use-demo-store";
import type { BostonAnswer, DemoSubmission } from "../types";

export function BostonNamingPage() {
  const savedAnswers = useDemoStore((state) => state.bostonAnswers);
  const status = useDemoStore((state) => state.statuses.boston_naming);
  const setStatus = useDemoStore((state) => state.setStatus);
  const setBostonAnswers = useDemoStore((state) => state.setBostonAnswers);
  const saveSubmission = useDemoStore((state) => state.saveSubmission);
  const resetTask = useDemoStore((state) => state.resetTask);
  const [index, setIndex] = useState(Math.min(savedAnswers.length, bostonQuestions.length - 1));
  const existing = savedAnswers[index];
  const [answer, setAnswer] = useState(existing?.answer ?? "");
  const [hintUsed, setHintUsed] = useState(existing?.hintUsed ?? false);
  const [startedAt, setStartedAt] = useState(existing?.startedAt ?? new Date().toISOString());
  const [imageFailed, setImageFailed] = useState(false);
  const taskStartedAt = useRef(savedAnswers[0]?.startedAt ?? new Date().toISOString());
  const question = bostonQuestions[index];

  function goTo(nextIndex: number) {
    const next = savedAnswers[nextIndex];
    setIndex(nextIndex);
    setAnswer(next?.answer ?? "");
    setHintUsed(next?.hintUsed ?? false);
    setStartedAt(next?.startedAt ?? new Date().toISOString());
    setImageFailed(false);
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const clean = answer.trim();
    if (!clean) return;
    const submittedAt = new Date().toISOString();
    const result: BostonAnswer = {
      questionId: question.id,
      answer: clean,
      startedAt,
      submittedAt,
      durationMs: Math.max(0, Date.parse(submittedAt) - Date.parse(startedAt)),
      hintUsed,
      provisionalScore: clean === question.expectedAnswer ? 1 : 0,
    };
    const updated = [...savedAnswers];
    updated[index] = result;
    setBostonAnswers(updated);
    if (index < bostonQuestions.length - 1) {
      setStatus("boston_naming", "in_progress");
      goTo(index + 1);
      return;
    }
    const submission: DemoSubmission<BostonAnswer[], { provisionalTotal: number; completed: true }> = {
      assignmentId: "demo-boston-001", taskId: "demo-boston-naming", taskType: "boston_naming",
      answers: updated,
      result: { provisionalTotal: updated.reduce((sum, item) => sum + item.provisionalScore, 0), completed: true },
      metrics: { startedAt: taskStartedAt.current, completedAt: submittedAt, durationMs: Date.parse(submittedAt) - Date.parse(taskStartedAt.current) },
    };
    saveSubmission("boston_naming", submission);
  }

  function restart() {
    resetTask("boston_naming");
    setIndex(0); setAnswer(""); setHintUsed(false); setStartedAt(new Date().toISOString());
    taskStartedAt.current = new Date().toISOString();
  }

  return (
    <div className="task-page narrow">
      <div className="task-heading"><div><span className="eyebrow">B 类 · 程序辅助</span><h1>Boston 图片命名</h1></div><Button variant="ghost" onClick={restart}><RotateCcw size={18} />重新开始</Button></div>
      <DemoNotice />
      <Progress value={status === "completed" ? 1 : (index + 1) / bostonQuestions.length} label="题目进度" />
      {status === "completed" ? (
        <Card className="success-card"><span className="success-icon"><CheckCircle2 size={38} /></span><h2>图片命名任务已完成</h2><p>系统已记录每道题的原始回答、用时和提示使用情况。</p><Button onClick={restart}>重新演示</Button></Card>
      ) : (
        <Card className="question-card naming-card">
          <div className="question-topline"><span>第 {index + 1} 题，共 {bostonQuestions.length} 题</span><span><Clock3 size={16} />单题计时中</span></div>
          <h2>{question.title}</h2>
          <div className="demo-image-wrap">
            {imageFailed ? <div className="image-fallback"><ImageIcon size={42} /><span>图片加载失败，请刷新后重试</span></div> : <img src={question.image} alt={question.imageAlt} onError={() => setImageFailed(true)} />}
          </div>
          <form onSubmit={submit}>
            <label htmlFor="naming-answer">您的回答</label>
            <input id="naming-answer" value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="请输入图片中的物品名称" autoComplete="off" />
            {hintUsed ? <div className="hint-box"><Lightbulb size={18} /><span>{question.hint}</span></div> : <Button type="button" variant="secondary" onClick={() => setHintUsed(true)}><Lightbulb size={18} />使用提示</Button>}
            <div className="navigation-buttons">
              <Button type="button" variant="ghost" disabled={index === 0} onClick={() => goTo(index - 1)}><ArrowLeft size={18} />上一题</Button>
              <Button type="submit" disabled={!answer.trim()}>{index === bostonQuestions.length - 1 ? "完成任务" : "确认并继续"}<ArrowRight size={18} /></Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
