import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";
import { cn } from "../lib/cn";

export function SurfaceCard({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-[32px] border border-[var(--line)] bg-white/90 shadow-[0_10px_30px_rgba(15,23,42,0.04)]",
        className,
      )}
      {...props}
    />
  );
}

export function GlassCard({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <SurfaceCard
      className={cn(
        "bg-[var(--panel)] shadow-[0_12px_40px_rgba(15,23,42,0.06)] backdrop-blur",
        className,
      )}
      {...props}
    />
  );
}

export function StatusPill({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: "neutral" | "brand" | "gold";
  className?: string;
}) {
  const toneClass =
    tone === "brand"
      ? "bg-[var(--brand-soft)] text-[var(--brand-dark)]"
      : tone === "gold"
        ? "bg-amber-50 text-amber-800"
        : "bg-slate-100 text-slate-600";

  return (
    <span className={cn("rounded-full px-3 py-2 text-sm", toneClass, className)}>
      {children}
    </span>
  );
}

export function ActionButton({
  className,
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "navy";
}) {
  const variantClass =
    variant === "secondary"
      ? "border border-slate-200 bg-white text-slate-800 hover:bg-slate-50 disabled:bg-slate-100 disabled:text-slate-400"
      : variant === "navy"
        ? "bg-[var(--navy)] text-white hover:bg-slate-900 disabled:bg-slate-400"
        : "bg-[var(--brand)] text-white hover:bg-[var(--brand-dark)] disabled:bg-teal-300";

  return (
    <button
      className={cn(
        "min-h-14 rounded-2xl px-5 py-4 text-lg font-medium transition disabled:cursor-not-allowed",
        variantClass,
        className,
      )}
      {...props}
    />
  );
}

export function MetricCard({
  label,
  value,
  emphasized = false,
}: {
  label: string;
  value: ReactNode;
  emphasized?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-[24px] p-4",
        emphasized ? "bg-[var(--navy)] text-white" : "bg-white ring-1 ring-slate-200",
      )}
    >
      <div className={cn("text-sm", emphasized ? "text-slate-200" : "text-slate-500")}>
        {label}
      </div>
      <div className="mt-2 text-3xl font-semibold">{value}</div>
    </div>
  );
}
