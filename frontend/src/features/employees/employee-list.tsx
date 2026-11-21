import Link from "next/link";
import { Card, PageHeading } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
import { ButtonLink } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
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
      {employees.length > 0 ? (
        <Card className="overflow-hidden">
          <div
            aria-hidden="true"
            className="hidden grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)_1rem] gap-4 border-b bg-surface-muted px-6 py-3 text-label font-semibold text-muted-foreground md:grid"
          >
            <span>Pracownik</span>
            <span>Stanowisko</span>
            <span>Komórka</span>
          </div>
          <ul>
            {employees.map((employee) => (
              <li key={employee.id} className="border-b last:border-0">
                <Link
                  href={employeeHref(employee.id)}
                  className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1 px-6 py-4 text-left transition-colors hover:bg-surface-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary md:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)_1rem] md:gap-4"
                >
                  <span className="row-span-3 md:row-span-1 md:flex md:min-w-0 md:items-center md:gap-3">
                    <Avatar employee={employee} size={40} />
                    <span className="hidden text-sm font-semibold md:block">{employee.name}</span>
                  </span>
                  <span className="min-w-0 text-sm font-semibold md:hidden">{employee.name}</span>
                  <span className="col-start-2 text-body text-muted-foreground md:col-auto">
                    {employee.position}
                  </span>
                  <span className="col-start-2 text-body text-muted-foreground md:col-auto">
                    {employee.department}
                  </span>
                  <Icon
                    name="chevron-right"
                    size={16}
                    className="col-start-3 row-span-3 row-start-1 text-subtle-foreground md:col-auto md:row-auto"
                  />
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      ) : (
        <Card className="flex items-start gap-4 p-6 text-body text-muted-foreground">
          <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-surface-muted text-primary">
            <Icon name="users" size={20} />
          </span>
          <div>
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
          </div>
        </Card>
      )}
    </>
  );
}
