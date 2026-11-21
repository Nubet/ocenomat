import Link from "next/link";
import { Card, PageHeading } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Icon } from "@/components/ui/icon";
import { NewAssessmentButton } from "./components/new-assessment-button";
import { assessmentHref, assessmentStatusLabels, type AssessmentRecord } from "./types";

export function AssessmentRows({ assessments }: { assessments: AssessmentRecord[] }) {
  if (assessments.length === 0)
    return (
      <p className="px-6 py-5 text-body text-muted-foreground">
        Nie masz dostępnych ocen. Widoczne są tylko procesy, które prowadzisz dla przypisanych
        pracowników.
      </p>
    );
  return assessments.map((assessment) => (
    <Link
      key={assessment.id}
      href={assessmentHref(assessment.id)}
      className="flex items-center gap-4 border-b px-6 py-5 last:border-0 hover:bg-surface-muted max-compact:flex-wrap"
    >
      <span className="min-w-0 flex-1">
        <strong className="block text-[0.8125rem] font-semibold">
          {assessment.employee_snapshot.name}
        </strong>
        <span className="mt-1 block text-label text-muted-foreground">
          {assessment.employee_snapshot.position} · Arkusz {assessment.form}
        </span>
        <span className="mt-1 block text-caption text-subtle-foreground">
          {new Date(assessment.created_at).toLocaleString("pl-PL", {
            timeZone: "Europe/Warsaw",
            dateStyle: "medium",
            timeStyle: "short",
          })}{" "}
          · {assessment.id}
        </span>
      </span>
      <Badge tone={assessment.status === "completed" ? "success" : "primary"}>
        {assessmentStatusLabels[assessment.status]}
      </Badge>
      <Icon name="arrow-up-right" size={16} />
    </Link>
  ));
}

export function AssessmentList({
  assessments,
  canCreate,
}: {
  assessments: AssessmentRecord[];
  canCreate: boolean;
}) {
  return (
    <>
      <PageHeading
        eyebrow="Zarządzanie procesami"
        title="Oceny pracownicze"
        description="Każda ocena jest osobnym procesem zapisanym w bazie. Nowa ocena nie usuwa poprzednich."
      />
      {canCreate ? (
        <div className="mb-4 flex justify-end">
          <NewAssessmentButton />
        </div>
      ) : null}
      <Card className="overflow-hidden">
        <AssessmentRows assessments={assessments} />
      </Card>
    </>
  );
}
