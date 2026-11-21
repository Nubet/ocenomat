import type { Employee } from "@/features/assessments/model/types";

const colors = {
  primary: "bg-avatar-primary text-avatar-primary-foreground",
  peach: "bg-avatar-peach text-avatar-peach-foreground",
  green: "bg-avatar-green text-avatar-green-foreground",
  purple: "bg-avatar-purple text-avatar-purple-foreground",
};

export function Avatar({ employee, size = 37 }: { employee: Employee; size?: number }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center text-body font-bold ${colors[employee.avatar]}`}
      style={{
        width: size,
        height: size,
        borderRadius: Math.round(size * 0.3),
      }}
    >
      {employee.initials}
    </span>
  );
}
