import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { PageHeading } from "@/components/ui/card";
import { Button, ButtonLink } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { formType } from "../model/scoring";
import { useAssessment } from "./assessment-context";

export function FlowFrame({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  const { employee, step, assessment } = useAssessment();
  const phase = ["setup", "analysis", "criteria", "timing", "saved"].includes(step)
    ? 0
    : step === "period"
      ? 1
      : 2;
  return (
    <div className="print-layout mx-auto max-w-flow animate-enter">
      <div className="no-print">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <Badge>
            <Icon name="file-check" size={13} />
            {assessment.type === "first"
              ? "Pierwsza ocena"
              : `Okresowa · Arkusz ${formType(employee)}`}
            <span className="text-subtle-foreground">/</span>
            {employee.name}
          </Badge>
          <span className="text-caption text-subtle-foreground">Demo v0.2 · zapis lokalny</span>
        </div>
        <nav
          aria-label="Fazy procesu"
          className="mt-[1.125rem] mb-[1.9375rem] grid gap-2.5 min-[701px]:grid-cols-3"
        >
          {[
            ["01", "Ustalenie oceny", "OSP · kryteria · terminy"],
            ["02", "Okres obserwacji", "Praca i przykłady zachowań"],
            ["03", "Zakończenie oceny", "Rozmowa · wynik · arkusz"],
          ].map(([number, label, kicker], index) => (
            <div
              key={number}
              aria-current={index === phase ? "step" : undefined}
              className={`flex min-w-0 items-center gap-3 rounded-[0.8125rem] border px-3.5 py-3 max-[700px]:py-2 ${index === phase ? "border-primary-border bg-primary-muted" : "bg-surface"}`}
            >
              <span
                className={`grid size-7 shrink-0 place-items-center rounded-lg text-label font-bold ${index === phase ? "bg-primary text-canvas" : "bg-surface-muted text-muted-foreground"}`}
              >
                {index < phase ? <Icon name="check" size={15} /> : number}
              </span>
              <div className="min-w-0">
                <p className="hidden text-[0.5625rem] font-bold tracking-wider text-muted-foreground uppercase min-[701px]:block">
                  {kicker}
                </p>
                <p className="mt-0.5 truncate text-label font-semibold max-[650px]:whitespace-normal">
                  {label}
                </p>
              </div>
            </div>
          ))}
        </nav>
        <PageHeading eyebrow={eyebrow} title={title} description={description} />
      </div>
      {children}
    </div>
  );
}

export function FlowFooter({
  onBack,
  onNext,
  label = "Dalej",
  disabled = false,
  note = "Zmiany zapisują się lokalnie",
}: {
  onBack?: () => void;
  onNext: () => void;
  label?: string;
  disabled?: boolean;
  note?: string;
}) {
  return (
    <div className="no-print sticky bottom-0 z-10 mt-[1.875rem] flex flex-wrap items-center justify-between gap-3 rounded-[0.875rem] border bg-surface/95 px-4 py-3 shadow-card backdrop-blur-xl max-compact:static">
      <div>
        {onBack ? (
          <Button variant="ghost" onClick={onBack}>
            <Icon name="chevron-left" size={16} />
            Wstecz
          </Button>
        ) : (
          <ButtonLink href="/" variant="ghost">
            <Icon name="chevron-left" size={16} />
            Pulpit
          </ButtonLink>
        )}
      </div>
      <span className="hidden text-caption text-subtle-foreground navigation:inline">
        <Icon name="check" size={12} className="mr-1 inline" />
        {note}
      </span>
      <Button variant="primary" onClick={onNext} disabled={disabled} className="max-compact:flex-1">
        {label}
        <Icon name="chevron-right" size={16} />
      </Button>
    </div>
  );
}
