import type { ReactNode } from "react";

export type BadgeTone =
  "neutral" | "primary" | "success" | "warning" | "danger";
const tones: Record<BadgeTone, string> = {
  neutral: "border-border bg-surface-muted text-muted-foreground",
  primary: "border-primary-border bg-primary-muted text-primary-strong",
  success: "border-success/18 bg-success-muted text-success",
  warning: "border-transparent bg-warning-muted text-warning",
  danger: "border-danger/20 bg-danger-muted text-danger",
};

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: BadgeTone;
}) {
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2 py-1 text-[0.65625rem] leading-tight font-semibold ${tones[tone]}`}
    >
      {children}
    </span>
  );
}
