import type { Metadata } from "next";
import { Avatar } from "@/components/ui/avatar";
import { ButtonLink } from "@/components/ui/button";
import { Card, PageHeading } from "@/components/ui/card";
import { getEmployee } from "@/features/employees/server";
import { requireUser } from "@/features/auth/session";
import { getAssessments } from "@/features/assessments/server";
import { AssessmentRows } from "@/features/assessments/assessment-list";
import { NewAssessmentButton } from "@/features/assessments/components/new-assessment-button";

export const metadata: Metadata = { title: "Profil pracownika" };

const positionLabels = {
  OFFICE_HEAD: "Kierownik urzędu",
  DIRECT_MANAGER: "Stanowisko bezpośrednio kierujące pracownikami",
  OTHER: "Pozostałe stanowisko",
};

export default async function EmployeePage({
  params,
}: {
  params: Promise<{ employeeId: string }>;
}) {
  const { employeeId } = await params;
  const [employee, user, assessments] = await Promise.all([
    getEmployee(employeeId),
    requireUser(),
    getAssessments(employeeId),
  ]);
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
        {user.roles.includes("MANAGER") ? <NewAssessmentButton employeeId={employee.id} /> : null}
      </div>
      <Card className="overflow-hidden">
        <AssessmentRows assessments={assessments} />
      </Card>
      <ButtonLink href="/employees" className="mt-5">
        Wróć do pracowników
      </ButtonLink>
    </>
  );
}
