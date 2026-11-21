"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, Note } from "@/components/ui/card";
import { RadioChoice } from "@/components/ui/choice";
import { Dialog } from "@/components/ui/dialog";
import { Icon } from "@/components/ui/icon";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import { employees, assessmentHref } from "../data/employees";
import { createAssessment, hasAssessmentProgress } from "../model/defaults";
import { formType } from "../model/scoring";
import type { Employee } from "../model/types";
import { useAssessment } from "./assessment-context";
import { FlowFrame, FlowFooter } from "./flow-frame";

const labels = ["Rodzaj oceny", "Pracownik", "Stanowisko", "Formularz"];
const descriptions = [
  "Wybierz ścieżkę, którą chcesz rozpocząć.",
  "Z kim chcesz przeprowadzić ocenę?",
  "Sprawdź informacje potrzebne do doboru kryteriów.",
  "Potwierdź sugerowany wzór arkusza.",
];

export function Setup() {
  const { assessment, employee, update, go } = useAssessment();
  const { state, updateAssessment } = useWorkspace();
  const router = useRouter();
  const [pendingEmployee, setPendingEmployee] = useState<Employee | null>(null);
  const index = assessment.setupIndex;

  function choose(person: Employee) {
    updateAssessment(person.id, {
      ...createAssessment(),
      type: assessment.type,
      setupIndex: 1,
    });
    setPendingEmployee(null);
    router.push(assessmentHref(person.id, "setup"));
  }
  function select(person: Employee) {
    if (person.id === employee.id) return;
    if (hasAssessmentProgress(state.assessments[person.id])) setPendingEmployee(person);
    else choose(person);
  }

  return (
    <FlowFrame eyebrow="Nowa ocena" title={labels[index]} description={descriptions[index]}>
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
        <>
          <fieldset className="grid gap-4 md:grid-cols-2">
            <legend className="sr-only">Rodzaj oceny</legend>
            {(
              [
                [
                  "periodic",
                  "Ocena okresowa",
                  "Ocena kompetencji pracownika zgodnie z przyjętymi kryteriami.",
                  "refresh",
                ],
                [
                  "first",
                  "Pierwsza ocena",
                  "Odrębna ścieżka dla nowych członków korpusu służby cywilnej.",
                  "users",
                ],
              ] as const
            ).map(([value, title, description, icon]) => (
              <RadioChoice
                key={value}
                name="assessment-type"
                value={value}
                checked={assessment.type === value}
                onChange={() => update({ type: value })}
              >
                <span className="flex gap-3">
                  <span
                    className={`grid size-11 shrink-0 place-items-center rounded-xl ${value === "first" ? "bg-warning-muted text-warning" : "bg-primary-muted text-primary"}`}
                  >
                    <Icon name={icon} size={21} />
                  </span>
                  <span>
                    <strong className="mb-2 block text-sm font-semibold">{title}</strong>
                    <span className="block text-body leading-5 text-muted-foreground">
                      {description}
                    </span>
                    <span className="mt-4 block">
                      <Badge tone={value === "periodic" ? "success" : "neutral"}>
                        {value === "periodic" ? "Pełny scenariusz demo" : "Interaktywna ścieżka"}
                      </Badge>
                    </span>
                  </span>
                </span>
              </RadioChoice>
            ))}
          </fieldset>
          {assessment.type === "first" ? (
            <Note className="mt-5 border-warning/20 bg-warning-muted text-warning">
              Pierwsza ocena ma odrębne zasady i formularz. Wybierz tę ścieżkę, aby poznać odrębną
              skalę i warunki wyniku.
            </Note>
          ) : null}
        </>
      ) : null}
      {index === 1 ? (
        <Card className="overflow-hidden">
          <h2 className="border-b px-5 py-4 text-body font-semibold">Wybierz osobę z zespołu</h2>
          <fieldset className="space-y-2 p-3">
            <legend className="sr-only">Osoba oceniana</legend>
            {employees.map((person) => (
              <RadioChoice
                key={person.id}
                name="employee"
                value={person.id}
                checked={person.id === employee.id}
                onChange={() => select(person)}
              >
                <span className="flex items-center gap-3">
                  <Avatar employee={person} size={38} />
                  <span>
                    <strong className="block text-body font-semibold">{person.name}</strong>
                    <span className="mt-1 block text-label text-muted-foreground">
                      {person.role} · {person.department}
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
            <Badge tone="success">Dane z profilu</Badge>
          </div>
          <div className="grid gap-5 border-t pt-6 sm:grid-cols-2">
            <div>
              <p className="eyebrow mb-2">Stanowisko</p>
              <p className="text-[0.8125rem] font-semibold">{employee.role}</p>
            </div>
            <div>
              <p className="eyebrow mb-2">Kierowanie zespołem</p>
              <p className="text-[0.8125rem] font-semibold">
                {employee.manager ? "Tak · 5–9 osób (demo)" : "Nie"}
              </p>
            </div>
          </div>
          <p className="eyebrow mt-7 mb-3">Główne obszary obowiązków</p>
          <div className="flex flex-wrap gap-2">
            {[
              "Analiza dokumentacji",
              "Przygotowanie rekomendacji",
              "Współpraca międzywydziałowa",
            ].map((text) => (
              <Badge key={text}>{text}</Badge>
            ))}
          </div>
        </Card>
      ) : null}
      {index === 3 ? (
        <Card className="p-6 sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-5">
            <div className="flex items-center gap-4">
              <span className="grid h-[4.375rem] w-15 place-items-center rounded-xl bg-primary-muted text-[1.625rem] font-semibold text-primary">
                {assessment.type === "first" ? "1" : formType(employee)}
              </span>
              <div>
                <p className="eyebrow mb-2">Dobrany formularz</p>
                <h2 className="text-lg font-semibold tracking-tight">
                  {assessment.type === "first"
                    ? "Arkusz pierwszej oceny"
                    : `Arkusz ${formType(employee)}`}
                </h2>
                <p className="mt-1 text-body text-muted-foreground">
                  {assessment.type === "first"
                    ? "Pierwsza ocena · podgląd ścieżki"
                    : "Ocena okresowa · wariant demonstracyjny"}
                </p>
              </div>
            </div>
            <Badge tone="primary">Do potwierdzenia</Badge>
          </div>
          <p className="mt-6 border-t pt-5 text-body leading-6 text-muted-foreground">
            {assessment.type === "first"
              ? "Pierwsza ocena przebiega według innej procedury niż okresowa i korzysta z odrębnego arkusza. W prototypie dostępna jest interaktywna symulacja wyniku."
              : "Kompas proponuje formularz na podstawie danych stanowiska. W rzeczywistym wdrożeniu jego dobór będzie weryfikowany względem aktualnych przepisów i typu stanowiska."}
          </p>
        </Card>
      ) : null}
      <FlowFooter
        onBack={index ? () => update({ setupIndex: index - 1 }) : undefined}
        onNext={() => {
          if (index < 3) update({ setupIndex: index + 1 });
          else go(assessment.type === "first" ? "first" : "analysis");
        }}
        label={index === 3 ? "Potwierdź i kontynuuj" : "Dalej"}
      />
      {pendingEmployee ? (
        <Dialog title="Zastąpić bieżącą ocenę?" onClose={() => setPendingEmployee(null)}>
          <div className="p-6">
            <p className="text-body leading-6 text-muted-foreground">
              {pendingEmployee.name} ma już lokalnie zapisany proces. Wybranie tej osoby do nowej
              oceny usunie jej poprzednie notatki i wyniki.
            </p>
            <div className="mt-6 flex justify-end gap-2">
              <Button onClick={() => setPendingEmployee(null)}>Anuluj</Button>
              <Button variant="primary" onClick={() => choose(pendingEmployee)}>
                Wybierz i rozpocznij
              </Button>
            </div>
          </div>
        </Dialog>
      ) : null}
    </FlowFrame>
  );
}
