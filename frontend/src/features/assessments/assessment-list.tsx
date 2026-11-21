"use client";

import Link from "next/link";
import { Card, PageHeading } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Icon } from "@/components/ui/icon";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import { employees, assessmentHref } from "./data/employees";
import { assessmentStatus } from "./components/assessment-status";
import { formType } from "./model/scoring";
import { NewAssessmentButton } from "./components/new-assessment-button";

export function AssessmentList() {
  const { state } = useWorkspace();
  return (
    <>
      <PageHeading
        eyebrow="Zarządzanie procesami"
        title="Oceny pracownicze"
        description="Rozpoczęte oceny są widoczne przez cały okres trwania procesu."
      />
      <div className="mb-4 flex justify-end">
        <NewAssessmentButton />
      </div>
      <Card className="overflow-hidden">
        {employees
          .filter(({ id }) => id !== "alicja")
          .map((employee) => {
            const status = assessmentStatus(state.assessments[employee.id]);
            return (
              <Link
                key={employee.id}
                href={assessmentHref(employee.id)}
                className="flex items-center gap-4 border-b px-6 py-5 last:border-0 hover:bg-surface-muted max-compact:flex-wrap"
              >
                <span className="min-w-0 flex-1">
                  <strong className="block text-[0.8125rem] font-semibold">
                    {employee.name}
                  </strong>
                  <span className="mt-1 block text-label text-muted-foreground">
                    {employee.role} · Arkusz {formType(employee)}
                  </span>
                </span>
                <Badge tone={status.tone}>{status.label}</Badge>
                <Icon name="arrow-up-right" size={16} />
              </Link>
            );
          })}
      </Card>
    </>
  );
}
