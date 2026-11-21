import { Card, PageHeading } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
import { ButtonLink } from "@/components/ui/button";
import { employeeHref, type EmployeeRecord } from "./types";
import type { WorkspaceUser } from "@/features/auth/session";

export function EmployeeList({
  employees,
  roles,
}: {
  employees: EmployeeRecord[];
  roles: WorkspaceUser["roles"];
}) {
  return (
    <>
      <PageHeading
        eyebrow="Zespół"
        title="Pracownicy"
        description="Otwórz profil pracownika, aby sprawdzić jego dane i własną historię ocen."
      />
      <div className="grid gap-4 md:grid-cols-2">
        {employees.map((employee) => (
          <Card key={employee.id} className="flex items-start gap-4 p-6">
            <Avatar employee={employee} size={46} />
            <div className="min-w-0 flex-1">
              <h2 className="text-sm font-semibold">{employee.name}</h2>
              <p className="mt-1 text-label text-muted-foreground">{employee.position}</p>
              <p className="mt-1 text-label text-subtle-foreground">{employee.department}</p>
              <div className="mt-5 flex flex-wrap items-center justify-between gap-2">
                <ButtonLink href={employeeHref(employee.id)} variant="ghost">
                  Profil pracownika
                </ButtonLink>
              </div>
            </div>
          </Card>
        ))}
      </div>
      {employees.length === 0 ? (
        <Card className="p-6 text-body text-muted-foreground">
          <h2 className="font-semibold text-foreground">
            Nie ma jeszcze pracowników na tej liście
          </h2>
          <p className="mt-2 leading-6">
            {roles.includes("ADMIN")
              ? "Zleć osobie obsługującej wdrożenie dodanie pracowników i przypisanie ich przełożonym. Panel do tych zmian nie jest jeszcze dostępny w aplikacji."
              : roles.includes("HR")
                ? "Poproś administratora o sprawdzenie, czy pracownicy zostali dodani do organizacji."
                : roles.includes("MANAGER")
                  ? "Poproś administratora o przypisanie osób, których oceny masz prowadzić. Podaj swój adres logowania oraz imiona i nazwiska pracowników."
                  : "Poproś administratora o sprawdzenie roli Twojego konta. Podaj adres, którym logujesz się do aplikacji."}
          </p>
          <ButtonLink href="/help" className="mt-4">
            Sprawdź role i dostęp
          </ButtonLink>
        </Card>
      ) : null}
    </>
  );
}
