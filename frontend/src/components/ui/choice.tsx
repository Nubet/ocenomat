import type { ReactNode } from "react";

export function RadioChoice({
  name,
  value,
  checked,
  onChange,
  children,
}: {
  name: string;
  value: string;
  checked: boolean;
  onChange: () => void;
  children: ReactNode;
}) {
  return (
    <label
      className={`flex cursor-pointer items-start gap-3 rounded-choice border px-4 py-3.5 text-body leading-6 transition-colors hover:border-primary ${checked ? "border-primary bg-primary-muted/40 ring-3 ring-primary/9" : "bg-surface"}`}
    >
      <input
        type="radio"
        name={name}
        value={value}
        checked={checked}
        onChange={onChange}
        className="mt-1 size-[1.1875rem] shrink-0"
      />
      <span className="min-w-0 flex-1">{children}</span>
    </label>
  );
}

export function CheckRow({
  checked,
  onChange,
  children,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  children: ReactNode;
}) {
  return (
    <label className="flex cursor-pointer items-start gap-3 text-body leading-5">
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="mt-0.5 size-[1.0625rem] shrink-0"
      />
      <span>{children}</span>
    </label>
  );
}
