import { ArrowRight, Image, Link2, MessageCircleMore, TextCursorInput, RotateCcw, CheckCircle2 } from "lucide-react";
import { Link } from "react-router-dom";
import { Button, Card, DemoNotice } from "../components/ui";
import { useDemoStore } from "../store/use-demo-store";
import type { TaskStatus, TaskType } from "../types";

const tasks: Array<{ type: TaskType; title: string; category: string; description: string; path: string; icon: typeof Image }> = [
  { type: "scd_interview", title: "SCD 结构化访谈", category: "C 类 · LLM 辅助", description: "通过对话逐步记录认知变化相关的主观感受。", path: "/demo/scd-interview", icon: MessageCircleMore },
  { type: "moca_open_answer", title: "MoCA-B 开放题", category: "C 类 · LLM 辅助", description: "提交自然语言回答并模拟后台结构化分析。", path: "/demo/moca-open-answer", icon: TextCursorInput },
  { type: "boston_naming", title: "Boston 图片命名", category: "B 类 · 程序辅助", description: "观看演示图片、输入名称并记录用时和提示。", path: "/demo/boston-naming", icon: Image },
  { type: "trail_making", title: "STT 形状连线", category: "B 类 · 程序辅助", description: "按指定顺序连接节点，记录过程、用时和错误。", path: "/demo/trail-making", icon: Link2 },
];

const labels: Record<TaskStatus, string> = { not_started: "未开始", in_progress: "进行中", completed: "已完成", failed: "需重试" };

export function HomePage() {
  const statuses = useDemoStore((state) => state.statuses);
  const resetTask = useDemoStore((state) => state.resetTask);
  return (
    <>
      <section className="hero">
        <span className="eyebrow">PATIENT EXPERIENCE DEMO</span>
        <h1>认知评估功能演示</h1>
        <p>依次体验两个 AI 辅助任务和两个标准化交互任务。所有数据只保存在本机浏览器中。</p>
      </section>
      <DemoNotice />
      <div className="task-grid">
        {tasks.map((task) => {
          const Icon = task.icon;
          const status = statuses[task.type];
          return (
            <Card className="task-card" key={task.type}>
              <div className="task-card-top"><span className="task-icon"><Icon size={24} /></span><span className={`status status-${status}`}>{status === "completed" && <CheckCircle2 size={14} />}{labels[status]}</span></div>
              <span className="task-category">{task.category}</span>
              <h2>{task.title}</h2><p>{task.description}</p>
              <div className="task-actions">
                <Link className="button button-primary" to={task.path}>{status === "not_started" ? "开始体验" : status === "completed" ? "查看结果" : "继续体验"}<ArrowRight size={18} /></Link>
                {status !== "not_started" && <Button variant="ghost" aria-label={`重置${task.title}`} onClick={() => resetTask(task.type)}><RotateCcw size={17} /></Button>}
              </div>
            </Card>
          );
        })}
      </div>
    </>
  );
}
