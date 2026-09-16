import { type KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle2, Clock3, RotateCcw, Route, Shapes } from "lucide-react";
import { Button, Card, DemoNotice, Progress } from "../components/ui";
import { getSttThreshold, interpretSttResult, sttAgeBands, sttCoordinateSystem, sttTasks } from "../data/stt-scale";
import { useDemoStore } from "../store/use-demo-store";
import type { DemoSubmission, SttAgeBand, SttForm, SttPhase, TrailEvent, TrailResult } from "../types";

const defaultForm: SttForm = "A";
const defaultPhase: SttPhase = "practice";
const defaultAgeBand: SttAgeBand = "60-69";

const emptyResult = (form: SttForm, phase: SttPhase, ageBand: SttAgeBand): TrailResult => ({
  form,
  phase,
  ageBand,
  thresholdSeconds: getSttThreshold(form, ageBand),
  clickedSequence: [],
  events: [],
  durationMs: 0,
  errorCount: 0,
  completed: false,
});

const phaseLabel: Record<SttPhase, string> = {
  practice: "练习",
  test: "正式",
};

const shapeLabel = {
  square: "方形",
  circle: "圆形",
};

export function TrailMakingPage() {
  const storedDraft = useDemoStore((state) => state.trailDraft);
  const setStatus = useDemoStore((state) => state.setStatus);
  const setTrailDraft = useDemoStore((state) => state.setTrailDraft);
  const saveSubmission = useDemoStore((state) => state.saveSubmission);
  const resetTask = useDemoStore((state) => state.resetTask);
  const [form, setForm] = useState<SttForm>(storedDraft?.form ?? defaultForm);
  const [phase, setPhase] = useState<SttPhase>(storedDraft?.phase ?? defaultPhase);
  const [ageBand, setAgeBand] = useState<SttAgeBand>(storedDraft?.ageBand ?? defaultAgeBand);
  const [result, setResult] = useState<TrailResult>(storedDraft ?? emptyResult(form, phase, ageBand));
  const [elapsed, setElapsed] = useState(storedDraft?.durationMs ?? 0);
  const startedAt = useRef(Date.now() - (storedDraft?.durationMs ?? 0));
  const startedAtIso = useRef(new Date(startedAt.current).toISOString());
  const task = sttTasks[form][phase];
  const expectedIndex = result.clickedSequence.length;
  const expectedNodeId = task.sequence[expectedIndex];
  const thresholdSeconds = getSttThreshold(form, ageBand);

  useEffect(() => {
    if (result.completed) return;
    const timer = window.setInterval(() => setElapsed(Date.now() - startedAt.current), 200);
    return () => window.clearInterval(timer);
  }, [result.completed]);

  useEffect(() => {
    if (result.form === form && result.phase === phase && result.ageBand === ageBand) return;
    startTask(form, phase, ageBand, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form, phase, ageBand]);

  const completedNodes = useMemo(() => new Set(result.clickedSequence), [result.clickedSequence]);
  const nodeById = useMemo(() => new Map(task.nodes.map((node) => [node.id, node])), [task.nodes]);
  const targetNodes = task.sequence.map((nodeId) => nodeById.get(nodeId)).filter(Boolean);

  const completedLines = result.clickedSequence.slice(1).map((nodeId, index) => {
    const from = nodeById.get(result.clickedSequence[index]);
    const to = nodeById.get(nodeId);
    if (!from || !to) return null;
    return <line key={`${from.id}-${to.id}`} x1={from.x} y1={from.y} x2={to.x} y2={to.y} className="trail-line" />;
  });

  function startTask(nextForm: SttForm, nextPhase: SttPhase, nextAgeBand: SttAgeBand, clearStoredTask = true) {
    if (clearStoredTask) resetTask("trail_making");
    const fresh = emptyResult(nextForm, nextPhase, nextAgeBand);
    setResult(fresh);
    setTrailDraft(fresh);
    setElapsed(0);
    setStatus("trail_making", "in_progress");
    startedAt.current = Date.now();
    startedAtIso.current = new Date().toISOString();
  }

  function selectNode(nodeId: string) {
    if (result.completed) return;
    const node = nodeById.get(nodeId);
    if (!node || !expectedNodeId) return;
    const timestampMs = Date.now() - startedAt.current;
    const correct = nodeId === expectedNodeId;
    const event: TrailEvent = {
      nodeId,
      label: node.label,
      shape: node.shape,
      expectedNodeId,
      timestampMs,
      correct,
    };
    const clickedSequence = correct ? [...result.clickedSequence, nodeId] : result.clickedSequence;
    const completed = clickedSequence.length === task.sequence.length;
    const assessment = completed ? interpretSttResult(form, ageBand, timestampMs) : undefined;
    const next: TrailResult = {
      ...result,
      form,
      phase,
      ageBand,
      thresholdSeconds,
      clickedSequence,
      events: [...result.events, event],
      durationMs: timestampMs,
      errorCount: result.errorCount + (correct ? 0 : 1),
      completed,
      abnormal: assessment?.abnormal,
      interpretation: assessment?.text,
    };
    setResult(next);
    setTrailDraft(next);
    setStatus("trail_making", completed ? "completed" : "in_progress");
    if (completed) {
      const completedAt = new Date().toISOString();
      const submission: DemoSubmission<TrailEvent[], TrailResult> = {
        assignmentId: "demo-trail-001",
        taskId: `demo-stt-${form.toLowerCase()}-${phase}`,
        taskType: "trail_making",
        answers: next.events,
        result: next,
        metrics: { startedAt: startedAtIso.current, completedAt, durationMs: timestampMs },
      };
      saveSubmission("trail_making", submission);
    }
  }

  function handleKey(event: KeyboardEvent<SVGGElement>, nodeId: string) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectNode(nodeId);
    }
  }

  function restart() {
    startTask(form, phase, ageBand);
  }

  function chooseForm(nextForm: SttForm) {
    setForm(nextForm);
  }

  function choosePhase(nextPhase: SttPhase) {
    setPhase(nextPhase);
  }

  const nextNode = expectedNodeId ? nodeById.get(expectedNodeId) : undefined;
  const progress = result.clickedSequence.length / task.sequence.length;
  const currentSeconds = (elapsed / 1000).toFixed(1);

  return (
    <div className="task-page">
      <div className="task-heading">
        <div>
          <span className="eyebrow">B 类 · 程序辅助</span>
          <h1>STT 形状连线</h1>
        </div>
        <Button variant="ghost" onClick={restart}>
          <RotateCcw size={18} />重新开始
        </Button>
      </div>
      <DemoNotice />
      <Progress value={progress} label={`${phaseLabel[phase]}进度`} />
      <div className="trail-layout">
        <Card className="trail-instructions">
          <div className="question-badge"><Route size={18} />任务设置</div>
          <div className="segmented-control" aria-label="STT 表单">
            {(["A", "B"] as SttForm[]).map((item) => (
              <button key={item} type="button" className={form === item ? "active" : ""} onClick={() => chooseForm(item)}>
                STT-{item}
              </button>
            ))}
          </div>
          <div className="segmented-control" aria-label="任务阶段">
            {(["practice", "test"] as SttPhase[]).map((item) => (
              <button key={item} type="button" className={phase === item ? "active" : ""} onClick={() => choosePhase(item)}>
                {phaseLabel[item]}
              </button>
            ))}
          </div>
          <label htmlFor="stt-age-band">年龄分层</label>
          <select id="stt-age-band" value={ageBand} onChange={(event) => setAgeBand(event.target.value as SttAgeBand)}>
            {sttAgeBands.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
          <div className="metric">
            <Clock3 size={20} />
            <div><span>已用时间</span><strong>{currentSeconds} 秒</strong></div>
          </div>
          <div className="metric">
            <span className="error-dot">!</span>
            <div><span>错误次数</span><strong>{result.errorCount}</strong></div>
          </div>
          <div className="metric">
            <Shapes size={20} />
            <div><span>异常阈值</span><strong>{thresholdSeconds} 秒</strong></div>
          </div>
          {!result.completed && nextNode && (
            <p>下一目标：<strong>{nextNode.label} · {shapeLabel[nextNode.shape]}</strong></p>
          )}
          {result.completed && (
            <p className={result.abnormal ? "threshold-warning" : "threshold-normal"}>
              {result.interpretation}：{(result.durationMs / 1000).toFixed(1)} 秒 / {result.thresholdSeconds} 秒
            </p>
          )}
        </Card>
        <Card className="trail-board-card">
          <svg className="trail-board" viewBox="0 0 100 100" role="group" aria-label={`STT-${form}${phaseLabel[phase]}操作区域`}>
            <rect x="0" y="0" width="100" height="100" className="trail-paper" />
            {targetNodes.slice(1).map((node, index) => {
              const from = targetNodes[index];
              if (!from || !node) return null;
              return <line key={`${from.id}-${node.id}-guide`} x1={from.x} y1={from.y} x2={node.x} y2={node.y} className="trail-guide-line" />;
            })}
            {completedLines}
            {task.nodes.map((node) => (
              <g
                key={node.id}
                role="button"
                aria-label={`节点 ${node.label} ${shapeLabel[node.shape]}`}
                aria-disabled={result.completed || completedNodes.has(node.id)}
                tabIndex={result.completed || completedNodes.has(node.id) ? -1 : 0}
                onClick={() => selectNode(node.id)}
                onKeyDown={(event) => handleKey(event, node.id)}
                className={`trail-node ${completedNodes.has(node.id) ? "done" : ""} ${node.isTarget ? "target" : "distractor"} ${node.id === expectedNodeId ? "next-target" : ""}`}
              >
                {node.shape === "circle"
                  ? <circle cx={node.x} cy={node.y} r="2.15" />
                  : <rect x={node.x - 2.15} y={node.y - 2.15} width="4.3" height="4.3" rx=".3" />}
                <text x={node.x} y={node.y + 0.08}>{node.label}</text>
              </g>
            ))}
          </svg>
          <div className="trail-source-note">
            坐标源：PDF {sttCoordinateSystem.width} × {sttCoordinateSystem.height} px，已按网页画布等比缩放。
          </div>
          {result.completed && (
            <div className="trail-complete">
              <CheckCircle2 size={28} />
              <div><strong>任务已完成</strong><span>交互顺序、用时、错误次数和年龄阈值判读已记录。</span></div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
