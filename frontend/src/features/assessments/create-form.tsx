"use client";

import { useActionState, useState } from "react";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { Card, Note, PageHeading } from "@/components/ui/card";
import { RadioChoice } from "@/components/ui/choice";
import { Icon } from "@/components/ui/icon";
import type { EmployeeRecord } from "@/features/employees/types";
import { createAssessment } from "./actions";

const labels = ["Rodzaj oceny", "Pracownik", "Stanowisko", "Formularz"];

export function CreateAssessmentForm({
  employees,
  initialEmployeeId,
  requestKey,
}: {
  employees: EmployeeRecord[];
  initialEmployeeId: string;
  requestKey: string;
}) {
  const [index, setIndex] = useState(0);
  const [employeeId, setEmployeeId] = useState(initialEmployeeId);
  const [key, setKey] = useState(requestKey);
  const [state, action, pending] = useActionState(createAssessment, { error: "" });
  const employee = employees.find(({ id }) => id === employeeId);
  if (!employee)
    return (
      <Note>
        Nie masz jeszcze przypisanych pracowników. Poproś administratora o przypisanie osób, których
        oceny masz prowadzić. Podaj swój adres logowania oraz imiona i nazwiska pracowników.{" "}
        <ButtonLink href="/help" className="mt-4">
          Sprawdź role i dostęp
        </ButtonLink>
      </Note>
    );
  const form =
    employee.position_kind === "OTHER"
      ? "C"
      : employee.position_kind === "DIRECT_MANAGER"
        ? "B"
        : "A";

  return (
    <>
      <PageHeading
        eyebrow="Nowa ocena"
        title={labels[index]}
        description="Utwórz osobny proces. Poprzednie oceny pozostają w historii."
      />
      <form action={action}>
        <input type="hidden" name="employee_id" value={employeeId} />
        <input type="hidden" name="idempotency_key" value={key} />
        <fieldset disabled={pending}>
          <legend className="sr-only">Konfiguracja nowej oceny</legend>
          <ol aria-label="Postęp konfiguracji" className="mb-6 flex flex-wrap gap-x-5 gap-y-3">
            {labels.map((label, number) => (
              <li
                key={label}
                className="flex items-center gap-2"
                aria-current={index === number ? "step" : undefined}
              >
                <span
                  className={`grid size-7 place-items-center rounded-lg border text-label font-bold ${number === index ? "border-primary-border bg-primary-muted text-primary" : number < index ? "border-transparent bg-success-muted text-success" : "bg-surface-muted text-muted-foreground"}`}
                >
                  {number < index ? <Icon name="check" size={14} /> : number + 1}
                </span>
                <span
                  className={`text-label ${index === number ? "font-semibold" : "text-muted-foreground"}`}
                >
                  {label}
                </span>
              </li>
            ))}
          </ol>
          {index === 0 ? (
            <Card className="p-6 sm:p-8">
              <Badge tone="success">Dostępna ścieżka</Badge>
              <h2 className="mt-4 text-lg font-semibold">Ocena okresowa · Arkusz B lub C</h2>
              <p className="mt-3 text-body leading-6 text-muted-foreground">
                Arkusz B dla stanowisk bezpośrednio kierujących pracownikami, C dla pozostałych
                stanowisk. Formularz dobierzemy na podstawie profilu. Pierwsza ocena i arkusz A nie
                są jeszcze dostępne.
              </p>
            </Card>
          ) : null}
          {index === 1 ? (
            <Card className="overflow-hidden">
              <h2 className="border-b px-5 py-4 text-body font-semibold">
                Wybierz osobę z zespołu
              </h2>
              <fieldset className="space-y-2 p-3">
                <legend className="sr-only">Osoba oceniana</legend>
                {employees.map((person) => (
                  <RadioChoice
                    key={person.id}
                    name="employee-selection"
                    value={person.id}
                    checked={person.id === employeeId}
                    onChange={() => {
                      if (person.id !== employeeId) {
                        setEmployeeId(person.id);
                        setKey(crypto.randomUUID());
                      }
                    }}
                  >
                    <span className="flex items-center gap-3">
                      <Avatar employee={person} size={38} />
                      <span>
                        <strong className="block text-body font-semibold">{person.name}</strong>
                        <span className="mt-1 block text-label text-muted-foreground">
                          {person.position} · {person.department}
                        </span>
                      </span>
                    </span>
                  </RadioChoice>
                ))}
              </fieldset>
            </Card>
          ) : null}
          {index === 2 ? (
            <Card className="p-6 sm:p-8">
              <div className="mb-6 flex flex-wrap items-center gap-3">
                <Avatar employee={employee} size={43} />
                <div>
                  <p className="font-semibold">{employee.name}</p>
                  <p className="mt-1 text-label text-muted-foreground">{employee.department}</p>
                </div>
                <Badge tone="primary">Dane z profilu</Badge>
              </div>
              <dl className="grid gap-5 border-t pt-6 text-body sm:grid-cols-2">
                <div>
                  <dt className="eyebrow mb-2">Stanowisko</dt>
                  <dd className="font-semibold">{employee.position}</dd>
                </div>
                <div>
                  <dt className="eyebrow mb-2">Kierowanie zespołem</dt>
                  <dd>
                    {employee.position_kind === "OTHER"
                      ? "Nie"
                      : employee.position_kind === "DIRECT_MANAGER"
                        ? "Tak"
                        : "Kierownik urzędu"}
                  </dd>
                </div>
              </dl>
            </Card>
          ) : null}
          {index === 3 ? (
            <Card className="p-6 sm:p-8">
              <div className="flex items-center gap-4">
                <span className="grid h-[4.375rem] w-15 place-items-center rounded-xl bg-primary-muted text-[1.625rem] font-semibold text-primary">
                  {form}
                </span>
                <div>
                  <p className="eyebrow mb-2">Formularz z profilu stanowiska</p>
                  <h2 className="text-lg font-semibold">Arkusz {form}</h2>
                  <p className="mt-1 text-body text-muted-foreground">
                    {employee.name} · Ocena okresowa
                  </p>
                </div>
              </div>
              <p className="mt-6 border-t pt-5 text-body leading-6 text-muted-foreground">
                Zapiszemy dane pracownika i kryteria obowiązujące w chwili rozpoczęcia oceny.
                Poprzednie oceny pozostaną w historii.
              </p>
              {form === "A" ? (
                <Note className="mt-5">
                  Arkusz {form} nie jest jeszcze obsługiwany. Wybierz pracownika na stanowisku
                  objętym arkuszem B lub C.
                </Note>
              ) : null}
            </Card>
          ) : null}
          {state.error ? (
            <p role="alert" className="mt-5 text-body text-warning">
              {state.error}
            </p>
          ) : null}
          <div className="mt-6 flex flex-wrap justify-between gap-3">
            {index > 0 ? (
              <Button onClick={() => setIndex(index - 1)}>Wstecz</Button>
            ) : (
              <ButtonLink href="/assessments">Wróć do ocen</ButtonLink>
            )}
            {index < 3 ? (
              <Button variant="primary" onClick={() => setIndex(index + 1)}>
                Dalej
                <Icon name="chevron-right" size={16} />
              </Button>
            ) : (
              <Button type="submit" variant="primary" disabled={pending || form === "A"}>
                {pending ? "Zapisywanie…" : "Utwórz ocenę"}
              </Button>
            )}
          </div>
        </fieldset>
      </form>
    </>
  );
}
