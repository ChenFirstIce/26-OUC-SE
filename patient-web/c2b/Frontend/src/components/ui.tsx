import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";

export function cn(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(" ");
}

export function Button({ className, variant = "primary", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" | "danger" }) {
  return <button className={cn("button", `button-${variant}`, className)} {...props} />;
}

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("card", className)} {...props} />;
}

export function Progress({ value, label }: { value: number; label?: string }) {
  const percentage = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className="progress-wrap" aria-label={label ?? `完成 ${percentage}%`}>
      <div className="progress-track"><div className="progress-fill" style={{ width: `${percentage}%` }} /></div>
      <span>{percentage}%</span>
    </div>
  );
}

export function DemoNotice() {
  return <div className="demo-notice"><strong>DEMO 演示内容</strong><span>不构成医学诊断，题目和评分规则均为占位内容。</span></div>;
}

export function EmptyState({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return <Card className="empty-state"><div className="empty-icon">{icon}</div><h2>{title}</h2><p>{children}</p></Card>;
}
