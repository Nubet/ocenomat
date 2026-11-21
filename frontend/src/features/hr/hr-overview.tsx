"use client";

import { useState } from "react";
import { Card, PageHeading } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { assessmentStatusLabels } from "@/features/assessments/types";
import { deadlineLabels, monitoringDate, type Monitoring } from "@/features/monitoring/types";
import { ReminderButton } from "./reminder-button";

export function HrOverview({ monitoring }: { monitoring: Monitoring }) {
  const [needsAttention, setNeedsAttention] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = monitoring.processes.find((process) => process.id === selectedId);
  return (
    <>
      <PageHeading
        eyebrow="Panel HR / Podgląd"
        title="Monitorowanie procesów"
        description="Widok organizacyjny. HR sprawdza etapy i terminy, ale nie otrzymuje notatek ani ocen cząstkowych."
      />
      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        {[
          [monitoring.total, "Wszystkie procesy"],
          [monitoring.total - monitoring.completed, "Niezakończone"],
          [monitoring.needs_attention, "Wymagają uwagi"],
        ].map(([count, label]) => (
          <Card key={label} className="p-5">
            <h2 className="text-label text-muted-foreground">{label}</h2>
            <p className="mt-4 text-[1.75rem] font-semibold tracking-heading">{count}</p>
          </Card>
        ))}
      </div>
      <Card className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-5">
          <h2 className="text-sm font-semibold">Rejestr ocen</h2>
          <fieldset
            aria-label="Filtr procesów HR"
            className="inline-flex rounded-xl border bg-surface-muted p-1"
          >
            {[false, true].map((value) => (
              <button
                type="button"
                key={String(value)}
                aria-pressed={needsAttention === value}
                onClick={() => setNeedsAttention(value)}
                className={`rounded-lg px-3 py-2 text-label ${needsAttention === value ? "bg-surface font-semibold shadow-sm" : "text-muted-foreground"}`}
              >
                {value ? "Wymagają uwagi" : "Wszystkie"}
              </button>
            ))}
          </fieldset>
        </div>
        <div className="overflow-x-auto">
          <table className="clean-table min-w-[40rem]">
            <thead>
              <tr>
                <th>Pracownik</th>
                <th>Przełożony</th>
                <th>Etap</th>
                <th>Termin oceny</th>
                <th>
                  <span className="sr-only">Działanie</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {monitoring.processes
                .filter((process) => !needsAttention || process.needs_attention)
                .map((process) => (
                  <tr key={process.id}>
                    <td className="font-semibold">
                      {process.employee_name}
                      <p className="text-label font-normal text-muted-foreground">
                        {process.kind === "first" ? "Pierwsza ocena" : `Arkusz ${process.form}`} ·{" "}
                        {process.department}
                      </p>
                    </td>
                    <td className="text-muted-foreground">{process.assessor_name}</td>
                    <td>
                      <Badge
                        tone={
                          process.status === "completed"
                            ? "success"
                            : process.needs_attention
                              ? "warning"
                              : "primary"
                        }
                      >
                        {assessmentStatusLabels[process.status]}
                      </Badge>
                    </td>
                    <td className="text-muted-foreground">
                      {monitoringDate(process.date_assessment)}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="text-label font-semibold text-primary"
                        onClick={() => setSelectedId(process.id)}
                      >
                        Szczegóły<span className="sr-only">: {process.employee_name}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              {!monitoring.processes.some(
                (process) => !needsAttention || process.needs_attention,
              ) ? (
                <tr>
                  <td colSpan={5}>Brak procesów w wybranym widoku.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </Card>
      <p className="mt-4 text-label text-muted-foreground">
        Wymagają uwagi: zaległe terminy, działania w najbliższych {monitoring.attention_window_days}{" "}
        dniach lub brakujące daty. Stan na {monitoringDate(monitoring.as_of)}.
      </p>
      {selected ? (
        <Dialog title="Szczegóły procesu" onClose={() => setSelectedId(null)}>
          <div className="space-y-4 p-6 text-body leading-6">
            <h3 className="font-semibold">{selected.employee_name}</h3>
            <p>
              {assessmentStatusLabels[selected.status]} · Prowadzący: {selected.assessor_name}
            </p>
            <ul>
              {monitoring.deadlines
                .filter((deadline) => deadline.assessment_id === selected.id)
                .map((deadline) => (
                  <li key={deadline.kind}>
                    {deadlineLabels[deadline.kind]}: {monitoringDate(deadline.due_on)}
                    {deadline.overdue ? " · Po terminie" : ""}
                  </li>
                ))}
            </ul>
            <ButtonLink href={`/employees/${selected.employee_id}`}>Profil pracownika</ButtonLink>
            <h4 className="font-semibold">Przypomnienia</h4>
            <p className="text-label text-muted-foreground">
              Dostarczenie w aplikacji oznacza zapis na pulpicie prowadzącego, nie odczytanie
              wiadomości.
            </p>
            {selected.can_remind ? (
              <ReminderButton key={selected.id} assessmentId={selected.id} />
            ) : (
              <p className="text-label text-muted-foreground">
                Wysyłka niedostępna: proces zakończony lub brak aktywnego prowadzącego z aktualnym
                przypisaniem.
              </p>
            )}
            <ul>
              {monitoring.reminders
                .filter((reminder) => reminder.assessment_id === selected.id)
                .map((reminder) => (
                  <li key={reminder.id} className="text-label text-muted-foreground">
                    Dostarczono w aplikacji{" "}
                    {new Date(reminder.created_at).toLocaleString("pl-PL", {
                      timeZone: "Europe/Warsaw",
                    })}{" "}
                    · HR: {reminder.sender_id} · odbiorca: {reminder.recipient_id}
                  </li>
                ))}
            </ul>
          </div>
        </Dialog>
      ) : null}
    </>
  );
}
