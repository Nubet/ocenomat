import { Card, PageHeading } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { employees } from "@/features/assessments/data/employees";
import { NewAssessmentButton } from "@/features/assessments/components/new-assessment-button";

export function EmployeeList() {
  return (
    <>
      <PageHeading
        eyebrow="Zespół"
        title="Pracownicy"
        description="Szybki dostęp do profili i przypisanych procesów oceny."
      />
      <div className="grid gap-4 md:grid-cols-2">
        {employees.map((employee) => (
          <Card key={employee.id} className="flex items-start gap-4 p-6">
            <Avatar employee={employee} size={46} />
            <div className="min-w-0 flex-1">
              <h2 className="text-sm font-semibold">{employee.name}</h2>
              <p className="mt-1 text-label text-muted-foreground">{employee.role}</p>
              <p className="mt-1 text-label text-subtle-foreground">{employee.department}</p>
              <div className="mt-5 flex flex-wrap items-center justify-between gap-2">
                <Badge tone={employee.id === "alicja" ? "success" : "primary"}>
                  {employee.id === "alicja"
                    ? "Przygotowana"
                    : employee.id === "piotr"
                      ? "Zaplanowana"
                      : "W trakcie"}
                </Badge>
                <NewAssessmentButton employeeId={employee.id} compact />
              </div>
            </div>
          </Card>
        ))}
      </div>
    </>
  );
}
