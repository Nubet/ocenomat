import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { NewAssessmentButton } from "@/features/assessments/components/new-assessment-button";
import { assessmentHref, assessmentStatusLabels } from "@/features/assessments/types";
import { deadlineLabels, monitoringDate, type Monitoring } from "@/features/monitoring/types";

export function Dashboard({
  canCreate,
  displayName,
  monitoring,
  isHr,
}: {
  canCreate: boolean;
  displayName: string;
  monitoring: Monitoring;
  isHr: boolean;
}) {
  const name = displayName.trim();
  const attention = monitoring.processes.find((process) => process.needs_attention);
  return (
    <>
      <div className="mb-8 flex flex-wrap items-end justify-between gap-5">
        <div>
          <p className="eyebrow mb-3">
            Twoja przestrzeń robocza / {monitoringDate(monitoring.as_of)}
          </p>
          <h1 className="text-[1.875rem] font-semibold tracking-heading sm:text-[2.125rem]">
            Dzień dobry{name ? `, ${name}` : ""}
          </h1>
          <p className="mt-3 text-[0.8125rem] text-muted-foreground">
            Twoje oceny i najbliższe decyzje.
          </p>
        </div>
        {canCreate ? <NewAssessmentButton /> : null}
        {isHr ? <ButtonLink href="/hr">Monitoring HR</ButtonLink> : null}
      </div>
      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        {[
          {
            number: monitoring.needs_attention,
            title: "Wymagają uwagi",
            subtitle: "Bliski termin, zaległość lub brak dat",
            color: "bg-warning",
          },
          {
            number: monitoring.in_progress,
            title: "W toku",
            subtitle: "Obserwacje i przygotowanie rozmowy",
            color: "bg-primary",
          },
          {
            number: monitoring.completed,
            title: "Zakończone",
            subtitle: "Proces zamknięty w aplikacji",
            color: "bg-success",
          },
        ].map((item) => (
          <section
            key={item.title}
            className="rounded-[0.875rem] border bg-surface px-[1.375rem] py-[1.3125rem]"
          >
            <h2 className="flex items-center gap-2 text-label font-medium text-muted-foreground">
              <span className={`size-[0.4375rem] rounded-full ${item.color}`} />
              {item.title}
            </h2>
            <div className="mt-4 flex items-end justify-between gap-2">
              <span className="text-[1.75rem] font-semibold tracking-heading tabular-nums">
                {item.number}
              </span>
              <span className="text-caption text-subtle-foreground">{item.subtitle}</span>
            </div>
          </section>
        ))}
      </div>
      {monitoring.reminders.length > 0 ? (
        <Card className="mb-6 p-6">
          <h2 className="text-sm font-semibold">Przypomnienia od HR</h2>
          <ul className="mt-4 space-y-3">
            {monitoring.reminders.map((reminder) => {
              const process = monitoring.processes.find(
                (item) => item.id === reminder.assessment_id,
              );
              return (
                <li key={reminder.id}>
                  <Link
                    className="text-body font-semibold text-primary"
                    href={assessmentHref(reminder.assessment_id)}
                  >
                    {process?.employee_name} · sprawdź etap i terminy oceny
                  </Link>
                  <p className="text-caption text-muted-foreground">
                    Dostarczono w aplikacji: {monitoringDate(reminder.created_at)}
                  </p>
                </li>
              );
            })}
          </ul>
        </Card>
      ) : null}
      <div className="mb-7 grid gap-4 lg:grid-cols-[1.36fr_1fr]">
        <section className="rounded-card border bg-surface px-6 py-6 sm:px-7">
          <p className="text-label font-semibold text-muted-foreground">Wymaga działania</p>
          {attention ? (
            <>
              <h2 className="mt-5 text-xl font-semibold tracking-heading">
                {attention.employee_name}
              </h2>
              <p className="mt-2 text-body text-muted-foreground">
                {assessmentStatusLabels[attention.status]} ·{" "}
                {attention.kind === "first" ? "Pierwsza ocena" : `Arkusz ${attention.form}`}
              </p>
              <p className="mt-5 text-body text-muted-foreground">
                Sprawdź terminy i zapisane ustalenia. Termin oceny:{" "}
                {monitoringDate(attention.date_assessment)}.
              </p>
              <div className="mt-5">
                <ButtonLink href={assessmentHref(attention.id)} variant="primary">
                  Przejdź do oceny
                  <Icon name="arrow-up-right" size={15} />
                </ButtonLink>
              </div>
            </>
          ) : (
            <p className="mt-5 text-body text-muted-foreground">
              Brak procesów z bliskim lub przekroczonym terminem ani brakujących dat.
            </p>
          )}
        </section>
        <Card className="p-6">
          <div className="mb-6 flex items-center justify-between gap-3">
            <h2 className="text-sm font-semibold">Najbliższe zadania</h2>
            <ButtonLink href="/deadlines">Terminy</ButtonLink>
          </div>
          <div className="space-y-5">
            {monitoring.deadlines.slice(0, 3).map((deadline) => (
              <Link
                key={`${deadline.assessment_id}:${deadline.kind}`}
                href={assessmentHref(deadline.assessment_id)}
                className="flex items-center gap-3"
              >
                <span className="flex-1">
                  <span className="block text-body font-semibold">
                    {deadlineLabels[deadline.kind]}
                  </span>
                  <span className="mt-1 block text-label text-muted-foreground">
                    {deadline.employee_name} · {monitoringDate(deadline.due_on)}
                  </span>
                </span>
                <Badge tone={deadline.overdue ? "warning" : "primary"}>
                  {deadline.overdue ? "Po terminie" : "Zaplanowano"}
                </Badge>
              </Link>
            ))}
            {monitoring.deadlines.length === 0 ? (
              <p className="text-body text-muted-foreground">Brak zapisanych terminów.</p>
            ) : null}
          </div>
        </Card>
      </div>
      <Card className="overflow-hidden">
        <div className="flex items-center justify-between gap-3 border-b px-6 py-5">
          <h2 className="text-sm font-semibold">Twoje procesy · {monitoring.total}</h2>
          <ButtonLink href="/assessments">Wszystkie</ButtonLink>
        </div>
        {monitoring.processes.map((process) => (
          <Link
            key={process.id}
            href={assessmentHref(process.id)}
            className="flex items-center gap-4 border-b px-6 py-4 last:border-0 hover:bg-surface-muted max-compact:flex-wrap"
          >
            <span className="min-w-0 flex-1">
              <span className="block text-body font-semibold">{process.employee_name}</span>
              <span className="mt-1 block text-caption text-muted-foreground">
                {process.position} ·{" "}
                {process.kind === "first" ? "Pierwsza ocena" : `Arkusz ${process.form}`}
              </span>
            </span>
            <Badge tone={process.status === "completed" ? "success" : "primary"}>
              {assessmentStatusLabels[process.status]}
            </Badge>
            <Icon name="arrow-up-right" size={17} className="text-subtle-foreground" />
          </Link>
        ))}
        {monitoring.total === 0 ? (
          <p className="p-6 text-body text-muted-foreground">
            Nie prowadzisz jeszcze żadnej oceny. Lista obejmuje wyłącznie Twoje procesy z aktualnym
            przypisaniem pracownika.
          </p>
        ) : null}
      </Card>
    </>
  );
}
