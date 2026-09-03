import { type KeyboardEvent, useEffect, useRef, useState } from "react";
import { CheckCircle2, Clock3, RotateCcw, Route } from "lucide-react";
import { Button, Card, DemoNotice, Progress } from "../components/ui";
import { trailNodes, trailSequence } from "../data/demo-data";
import { useDemoStore } from "../store/use-demo-store";
import type { DemoSubmission, TrailEvent, TrailResult } from "../types";

const emptyResult = (): TrailResult => ({ clickedSequence: [], events: [], durationMs: 0, errorCount: 0, completed: false });

export function TrailMakingPage() {
  const storedDraft = useDemoStore((state) => state.trailDraft);
  const status = useDemoStore((state) => state.statuses.trail_making);
  const setStatus = useDemoStore((state) => state.setStatus);
  const setTrailDraft = useDemoStore((state) => state.setTrailDraft);
  const saveSubmission = useDemoStore((state) => state.saveSubmission);
  const resetTask = useDemoStore((state) => state.resetTask);
  const [result, setResult] = useState<TrailResult>(storedDraft ?? emptyResult());
  const [elapsed, setElapsed] = useState(storedDraft?.durationMs ?? 0);
  const startedAt = useRef(Date.now() - (storedDraft?.durationMs ?? 0));
  const startedAtIso = useRef(new Date(startedAt.current).toISOString());
  const expectedIndex = result.clickedSequence.length;

  useEffect(() => {
    if (result.completed) return;
    const timer = window.setInterval(() => setElapsed(Date.now() - startedAt.current), 200);
    return () => window.clearInterval(timer);
  }, [result.completed]);

  function selectNode(nodeId: string) {
    if (result.completed) return;
    const timestampMs = Date.now() - startedAt.current;
    const correct = nodeId === trailSequence[expectedIndex];
    const event: TrailEvent = { nodeId, timestampMs, correct };
    const clickedSequence = correct ? [...result.clickedSequence, nodeId] : result.clickedSequence;
    const completed = clickedSequence.length === trailSequence.length;
    const next: TrailResult = {
      clickedSequence,
      events: [...result.events, event],
      durationMs: timestampMs,
      errorCount: result.errorCount + (correct ? 0 : 1),
      completed,
    };
    setResult(next);
    setTrailDraft(next);
    setStatus("trail_making", completed ? "completed" : "in_progress");
    if (completed) {
      const completedAt = new Date().toISOString();
      const submission: DemoSubmission<TrailEvent[], TrailResult> = {
        assignmentId: "demo-trail-001", taskId: "demo-trail-making", taskType: "trail_making",
        answers: next.events, result: next,
        metrics: { startedAt: startedAtIso.current, completedAt, durationMs: timestampMs },
      };
      saveSubmission("trail_making", submission);
    }
  }

  function handleKey(event: KeyboardEvent<SVGGElement>, nodeId: string) {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectNode(nodeId); }
  }

  function restart() {
    resetTask("trail_making");
    const fresh = emptyResult();
    setResult(fresh); setTrailDraft(fresh); setElapsed(0);
    startedAt.current = Date.now(); startedAtIso.current = new Date().toISOString();
  }

  const completedNodes = new Set(result.clickedSequence);
  const completedLines = result.clickedSequence.slice(1).map((nodeId, index) => {
    const from = trailNodes.find((node) => node.id === result.clickedSequence[index])!;
    const to = trailNodes.find((node) => node.id === nodeId)!;
    return <line key={`${from.id}-${to.id}`} x1={from.x} y1={from.y} x2={to.x} y2={to.y} className="trail-line" />;
  });

  return (
    <div className="task-page">
      <div className="task-heading"><div><span className="eyebrow">B 类 · 程序辅助</span><h1>STT 形状连线</h1></div><Button variant="ghost" onClick={restart}><RotateCcw size={18} />重新开始</Button></div>
      <DemoNotice />
      <Progress value={result.clickedSequence.length / trailSequence.length} label="连线进度" />
      <div className="trail-layout">
        <Card className="trail-instructions"><div className="question-badge"><Route size={18} />任务说明</div><h2>请按顺序点击</h2><div className="sequence-preview">1 <span>→</span> A <span>→</span> 2 <span>→</span> B <span>→</span> 3 <span>→</span> C</div><div className="metric"><Clock3 size={20} /><div><span>已用时间</span><strong>{(elapsed / 1000).toFixed(1)} 秒</strong></div></div><div className="metric"><span className="error-dot">!</span><div><span>错误次数</span><strong>{result.errorCount}</strong></div></div>{!result.completed && <p>下一目标：<strong>{trailSequence[expectedIndex]}</strong></p>}</Card>
        <Card className="trail-board-card">
          <svg className="trail-board" viewBox="0 0 100 100" role="group" aria-label="形状连线操作区域">
            {completedLines}
            {trailNodes.map((node) => (
              <g key={node.id} role="button" aria-label={`节点 ${node.label}`} aria-disabled={result.completed || completedNodes.has(node.id)} tabIndex={result.completed || completedNodes.has(node.id) ? -1 : 0} onClick={() => selectNode(node.id)} onKeyDown={(event) => handleKey(event, node.id)} className={`trail-node ${completedNodes.has(node.id) ? "done" : ""}`}>
                <circle cx={node.x} cy={node.y} r="7" /><text x={node.x} y={node.y + 0.5}>{node.label}</text>
              </g>
            ))}
          </svg>
          {result.completed && <div className="trail-complete"><CheckCircle2 size={28} /><div><strong>任务已完成</strong><span>交互顺序、用时与错误次数已记录。</span></div></div>}
        </Card>
      </div>
    </div>
  );
}
