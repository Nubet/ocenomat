"use client";

import { useState } from "react";
import { Card, PageHeading } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Icon } from "@/components/ui/icon";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import { employees } from "@/features/assessments/data/employees";
import { assessmentStatus } from "@/features/assessments/components/assessment-status";
import type { Employee } from "@/features/assessments/model/types";

export function HrOverview() {
  const { state } = useWorkspace();
  const [needsAttention, setNeedsAttention] = useState(false);
  const [selected, setSelected] = useState<Employee | null>(null);
  return (
    <>
      <PageHeading
        eyebrow="Panel HR / Podgląd"
        title="Monitorowanie procesów"
        description="Widok organizacyjny. HR sprawdza etapy i formalności, ale nie ocenia pracownika za przełożonego."
      />
      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        {[
          ["12", "Wszystkie procesy"],
          ["04", "W toku"],
          ["02", "Wymagają uwagi"],
        ].map(([count, label]) => (
          <Card key={label} className="p-5">
            <h2 className="text-label text-muted-foreground">{label}</h2>
            <p className="mt-4 text-[1.75rem] font-semibold tracking-heading">
              {count}
            </p>
          </Card>
        ))}
      </div>
      <Card className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-5">
          <h2 className="text-sm font-semibold">Rejestr ocen</h2>
          <div
            role="group"
            aria-label="Filtr procesów HR"
            className="inline-flex rounded-xl border bg-surface-muted p-1"
          >
            {[
              [false, "Wszystkie"],
              [true, "Wymagają uwagi"],
            ].map(([value, label]) => (
              <button
                type="button"
                key={String(value)}
                aria-pressed={needsAttention === value}
                onClick={() => setNeedsAttention(value as boolean)}
                className={`rounded-lg px-3 py-2 text-label ${needsAttention === value ? "bg-surface font-semibold shadow-sm" : "text-muted-foreground"}`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="clean-table min-w-[40rem]">
            <thead>
              <tr>
                <th>Pracownik</th>
                <th>Przełożony</th>
                <th>Etap</th>
                <th>Termin</th>
                <th>
                  <span className="sr-only">Działanie</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {employees
                .filter((_, index) => !needsAttention || index < 2)
                .map((employee) => {
                  const assessment = state.assessments[employee.id];
                  const status = assessmentStatus(assessment);
                  return (
                    <tr key={employee.id}>
                      <td className="font-semibold">{employee.name}</td>
                      <td className="text-muted-foreground">
                        {employee.id === "alicja" ? "Tomasz Lis" : "Anna Nowak"}
                      </td>
                      <td>
                        <Badge tone={status.tone}>{status.label}</Badge>
                      </td>
                      <td className="text-muted-foreground">
                        {assessment.dateAssessment}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="text-label font-semibold text-primary"
                          onClick={() => setSelected(employee)}
                        >
                          Szczegóły
                          <span className="sr-only">: {employee.name}</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </Card>
      <div className="mt-5">
        <ButtonLink href="/">
          <Icon name="chevron-left" size={16} />
          Widok przełożonej
        </ButtonLink>
      </div>
      {selected ? (
        <Dialog title="Szczegóły procesu" onClose={() => setSelected(null)}>
          <div className="space-y-4 p-6 text-body leading-6">
            <h3 className="font-semibold">{selected.name}</h3>
            <p className="text-muted-foreground">
              Termin: {state.assessments[selected.id].dateAssessment}
            </p>
            <p className="text-muted-foreground">
              Potwierdzenia formalne:{" "}
              {state.assessments[selected.id].formal.filter(Boolean).length}/3
            </p>
            <p className="text-muted-foreground">
              W panelu HR dostępne byłyby terminy, status wymaganych czynności
              oraz historia przypomnień. HR nie zmienia ocen cząstkowych
              pracownika.
            </p>
            <Button onClick={() => setSelected(null)}>Zamknij</Button>
          </div>
        </Dialog>
      ) : null}
    </>
  );
}
