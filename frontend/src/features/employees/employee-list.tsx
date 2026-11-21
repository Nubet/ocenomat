import { Card, PageHeading } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
import { ButtonLink } from "@/components/ui/button";
import { employeeHref, type EmployeeRecord } from "./types";

export function EmployeeList({ employees }: { employees: EmployeeRecord[] }) {
  return (
    <>
      <PageHeading
        eyebrow="Zespół"
        title="Pracownicy"
        description="Pracownicy widoczni zgodnie z Twoimi uprawnieniami."
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
          Brak pracowników dostępnych dla Twojego konta. Przełożony widzi tylko przypisane osoby.
        </Card>
      ) : null}
    </>
  );
}
