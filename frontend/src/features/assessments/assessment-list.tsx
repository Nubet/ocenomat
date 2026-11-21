import Link from "next/link";
import { Card, PageHeading } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Icon } from "@/components/ui/icon";
import { NewAssessmentButton } from "./components/new-assessment-button";
import { assessmentHref, assessmentStatusLabels, type AssessmentRecord } from "./types";
import { ButtonLink } from "@/components/ui/button";
import type { WorkspaceUser } from "@/features/auth/session";

export function AssessmentEmptyState({
  roles,
  canCreate,
  employeeId,
}: {
  roles: WorkspaceUser["roles"];
  canCreate: boolean;
  employeeId?: string;
}) {
  const manager = roles.includes("MANAGER");
  return (
    <div className="px-6 py-6">
      <h2 className="text-body font-semibold">
        {manager
          ? employeeId
            ? "Nie prowadzisz jeszcze oceny tej osoby"
            : "Nie prowadzisz jeszcze żadnej oceny"
          : "Ten widok jest dla przełożonych prowadzących oceny"}
      </h2>
      <p className="mt-2 text-body leading-6 text-muted-foreground">
        {manager
          ? canCreate
            ? "Rozpocznij nową ocenę i wybierz pracownika. Zapisana ocena pojawi się tutaj — możesz do niej wrócić później."
            : "Aby rozpocząć ocenę, potrzebujesz przypisania pracownika. Poproś administratora o sprawdzenie przypisania; podaj swój adres logowania oraz imię i nazwisko pracownika."
          : roles.includes("HR")
            ? "Jako HR możesz przeglądać profile pracowników. Treść ocen jest dostępna tylko dla przełożonego, który je prowadzi. Monitoring HR jest jeszcze w przygotowaniu."
            : roles.includes("ADMIN")
              ? "Sama rola administratora nie udostępnia treści ocen. Jeśli masz je prowadzić, zleć osobie obsługującej wdrożenie dodanie roli przełożonego i przypisanie pracownika."
              : "Poproś administratora o nadanie roli odpowiedniej do Twoich obowiązków. Podaj adres, którym logujesz się do aplikacji."}
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {manager && canCreate ? <NewAssessmentButton employeeId={employeeId} /> : null}
        {roles.some((role) => ["MANAGER", "HR", "ADMIN"].includes(role)) ? (
          <ButtonLink href="/employees">Sprawdź pracowników</ButtonLink>
        ) : null}
        <ButtonLink href="/help" variant="ghost">
          Sprawdź role i dostęp
        </ButtonLink>
      </div>
    </div>
  );
}

export function AssessmentRows({
  assessments,
  emptyState,
}: {
  assessments: AssessmentRecord[];
  emptyState: React.ReactNode;
}) {
  if (assessments.length === 0) return emptyState;
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
          {assessment.employee_snapshot.position} ·{" "}
          {assessment.kind === "first" ? "Pierwsza ocena" : `Arkusz ${assessment.form}`}
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
  roles,
}: {
  assessments: AssessmentRecord[];
  canCreate: boolean;
  roles: WorkspaceUser["roles"];
}) {
  return (
    <>
      <PageHeading
        eyebrow="Zarządzanie procesami"
        title="Oceny pracownicze"
        description="Tu wrócisz do ocen, które prowadzisz. Poprzednie oceny pozostają w historii."
      />
      {canCreate && assessments.length > 0 ? (
        <div className="mb-4 flex justify-end">
          <NewAssessmentButton />
        </div>
      ) : null}
      <Card className="overflow-hidden">
        <AssessmentRows
          assessments={assessments}
          emptyState={<AssessmentEmptyState roles={roles} canCreate={canCreate} />}
        />
      </Card>
    </>
  );
}
