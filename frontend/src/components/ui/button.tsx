import Link from "next/link";
import type { ButtonHTMLAttributes, ComponentProps } from "react";

type Variant = "primary" | "secondary" | "ghost" | "feature";
const variants: Record<Variant, string> = {
  primary:
    "border-primary-action bg-primary-action text-primary-foreground shadow-sm hover:border-primary-action-hover hover:bg-primary-action-hover",
  secondary:
    "border-border bg-surface text-foreground hover:border-border-interactive hover:bg-surface-muted",
  ghost:
    "border-transparent bg-transparent text-muted-foreground hover:bg-surface-muted hover:text-foreground",
  feature: "border-white bg-white text-feature-action hover:bg-white/90",
};

export function buttonClass(variant: Variant = "secondary", className = "") {
  return `inline-flex min-h-[2.4375rem] shrink-0 items-center justify-center gap-2 rounded-control border px-3.5 py-2 text-[0.78125rem] font-semibold leading-5 transition-colors active:translate-y-px disabled:translate-y-0 max-compact:px-2.5 max-compact:text-label ${variants[variant]} ${className}`;
}

export function Button({
  variant = "secondary",
  className,
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button type={type} className={buttonClass(variant, className)} {...props} />;
}

export function ButtonLink({
  variant = "secondary",
  className,
  children,
  ...props
}: ComponentProps<typeof Link> & { variant?: Variant }) {
  return (
    <Link className={buttonClass(variant, className)} {...props}>
      {children}
    </Link>
  );
}
