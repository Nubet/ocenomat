"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Avatar } from "@/components/ui/avatar";
import { Icon } from "@/components/ui/icon";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import { assessmentHref } from "@/features/assessments/data/employees";
import { resolveAssessmentStep } from "@/features/assessments/model/navigation";
import type { Employee } from "@/features/assessments/model/types";
import { processNavigation } from "./navigation";

export function AssessmentNavigation({
  employee,
  onNavigate,
}: {
  employee: Employee;
  onNavigate?: () => void;
}) {
  const { state, updateAssessment } = useWorkspace();
  const query = useSearchParams();
  const current = resolveAssessmentStep(
    employee,
    state.assessments[employee.id],
    query.get("step"),
  );
  const navigationStep =
    current === "recommendation"
      ? "rating"
      : current === "saved"
        ? "timing"
        : current === "finished"
          ? "document"
          : current;
  const currentIndex = processNavigation.findIndex(({ step }) => step === navigationStep);

  return (
    <div className="mx-4 mt-6 border-t pt-6 pb-4">
      <p className="eyebrow mx-3 mb-3 text-caption">Bieżąca ocena</p>
      <div className="mb-3 flex items-center gap-2 px-2">
        <Avatar employee={employee} size={29} />
        <div>
          <p className="text-label font-semibold">{employee.name}</p>
          <p className="text-caption text-subtle-foreground">Ocena okresowa</p>
        </div>
      </div>
      <nav aria-label="Etapy oceny" className="space-y-0.5">
        {processNavigation.map(({ step, label }, index) => {
          const content = (
            <>
              <span
                className={`grid size-6 shrink-0 place-items-center rounded-lg border text-caption font-bold ${index === currentIndex ? "border-primary-border bg-primary-muted text-primary" : index < currentIndex ? "border-transparent bg-success-muted text-success" : "bg-surface-muted"}`}
              >
                {index < currentIndex ? <Icon name="check" size={13} /> : index + 1}
              </span>
              {label}
            </>
          );
          const className = `flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-label ${index === currentIndex ? "bg-surface font-bold" : "text-muted-foreground"}`;
          return index <= currentIndex ? (
            <Link
              key={step}
              href={assessmentHref(employee.id, step)}
              onClick={() => {
                updateAssessment(employee.id, { step });
                onNavigate?.();
              }}
              className={className}
              aria-current={index === currentIndex ? "step" : undefined}
            >
              {content}
            </Link>
          ) : (
            <span key={step} aria-disabled="true" className={`${className} opacity-45`}>
              {content}
            </span>
          );
        })}
      </nav>
    </div>
  );
}
