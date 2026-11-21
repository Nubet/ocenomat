const colors = {
  primary: "bg-avatar-primary text-avatar-primary-foreground",
  peach: "bg-avatar-peach text-avatar-peach-foreground",
  green: "bg-avatar-green text-avatar-green-foreground",
  purple: "bg-avatar-purple text-avatar-purple-foreground",
};

export function Avatar({
  employee,
  size = 37,
}: {
  employee: { name: string; initials?: string; avatar?: keyof typeof colors };
  size?: number;
}) {
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center text-body font-bold ${colors[employee.avatar ?? "primary"]}`}
      style={{
        width: size,
        height: size,
        borderRadius: Math.round(size * 0.3),
      }}
    >
      {employee.initials ??
        employee.name
          .split(/\s+/)
          .slice(0, 2)
          .map((part) => part[0])
          .join("")}
    </span>
  );
}
