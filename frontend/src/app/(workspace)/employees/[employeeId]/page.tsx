import type { Metadata } from "next";
import { Avatar } from "@/components/ui/avatar";
import { ButtonLink } from "@/components/ui/button";
import { Card, PageHeading } from "@/components/ui/card";
import { getEmployee, getEmployeePage } from "@/features/employees/server";
import { requireUser } from "@/features/auth/session";
import { getAssessments } from "@/features/assessments/server";
import { AssessmentRows, AssessmentEmptyState } from "@/features/assessments/assessment-list";
import { NewAssessmentButton } from "@/features/assessments/components/new-assessment-button";
import { employeeListHref, parseEmployeeQuery } from "@/features/employees/query";

export const metadata: Metadata = { title: "Profil pracownika" };

const positionLabels = {
  OFFICE_HEAD: "Kierownik urzędu",
  DIRECT_MANAGER: "Stanowisko bezpośrednio kierujące pracownikami",
  OTHER: "Pozostałe stanowisko",
};

export default async function EmployeePage({
  params,
  searchParams,
}: {
  params: Promise<{ employeeId: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { employeeId } = await params;
  const [employee, user, assessments] = await Promise.all([
    getEmployee(employeeId),
    requireUser(),
    getAssessments(employeeId),
  ]);
  const canCreate =
    user.roles.includes("MANAGER") &&
    (await getEmployeePage({ assigned_only: true, employee_id: employee.id, page_size: 1 })).total >
      0;
  return (
    <>
      <PageHeading
        eyebrow="Zespół"
        title={employee.name}
        description="Profil pracownika z bazy aplikacji."
      />
      <Card className="flex items-start gap-4 p-6">
        <Avatar employee={employee} size={46} />
        <dl className="space-y-4 text-body">
          <div>
            <dt className="text-muted-foreground">Stanowisko</dt>
            <dd className="font-semibold">{employee.position}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Komórka organizacyjna</dt>
            <dd>{employee.department}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Typ stanowiska</dt>
            <dd>{positionLabels[employee.position_kind]}</dd>
          </div>
        </dl>
      </Card>
      <div className="mt-6 mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold">Oceny prowadzone przez Ciebie</h2>
        {canCreate && assessments.length > 0 ? (
          <NewAssessmentButton employeeId={employee.id} />
        ) : null}
      </div>
      <Card className="overflow-hidden">
        <AssessmentRows
          assessments={assessments}
          emptyState={
            <AssessmentEmptyState
              roles={user.roles}
              canCreate={canCreate}
              employeeId={employee.id}
            />
          }
        />
      </Card>
      <ButtonLink
        href={
          employeeListHref(parseEmployeeQuery((await searchParams) ?? {})) + "#employee-results"
        }
        className="mt-5"
      >
        Wróć do pracowników
      </ButtonLink>
    </>
  );
}
