import type { HTMLAttributes, ReactNode } from "react";

export function Card({ className = "", ...props }: HTMLAttributes<HTMLElement>) {
  return (
    <section
      className={`rounded-card border bg-surface shadow-card max-compact:rounded-[0.875rem] ${className}`}
      {...props}
    />
  );
}

export function Note({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-xl border bg-surface-muted px-4 py-3 text-label leading-relaxed text-muted-foreground ${className}`}
    >
      {children}
    </div>
  );
}

export function PageHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="mb-8">
      <p className="eyebrow mb-3">{eyebrow}</p>
      <h1 className="text-[1.75rem] leading-heading font-semibold tracking-heading sm:text-title">
        {title}
      </h1>
      {description ? (
        <p className="mt-3 max-w-[40.625rem] text-[0.8125rem] leading-6 text-muted-foreground">
          {description}
        </p>
      ) : null}
    </div>
  );
}
