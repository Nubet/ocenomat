"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { NewAssessmentButton } from "@/features/assessments/components/new-assessment-button";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import { employees } from "@/features/assessments/data/employees";
import { assessmentStatus } from "@/features/assessments/components/assessment-status";

export function Dashboard({ canCreate, displayName }: { canCreate: boolean; displayName: string }) {
  const { state } = useWorkspace();
  const name = displayName?.trim();
  const tasks = [
    {
      number: "01",
      title: "Potwierdź rozmowę rozpoczynającą",
      person: "Maria Wiśniewska",
      href: "/assessments",
    },
    {
      number: "02",
      title: "Sprawdź kryteria dla kierownika",
      person: "Piotr Nowak · Arkusz B",
      href: "/assessments",
    },
    {
      number: "03",
      title: "Przejrzyj obserwacje",
      person: "Jan Kowalski",
      href: "/assessments",
    },
  ];
  return (
    <>
      <div className="mb-8 flex flex-wrap items-end justify-between gap-5">
        <div>
          <p className="eyebrow mb-3">Twoja przestrzeń robocza / listopad 2026</p>
          <h1 className="text-[1.875rem] font-semibold tracking-heading sm:text-[2.125rem]">
            Dzień dobry{name ? `, ${name}` : ""}
          </h1>
          <p className="mt-3 text-[0.8125rem] text-muted-foreground">
            Twoje oceny i najbliższe decyzje.
          </p>
        </div>
        {canCreate ? <NewAssessmentButton /> : null}
      </div>
      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        {[
          {
            number: "02",
            title: "Wymaga działania",
            subtitle: "Do omówienia lub zatwierdzenia",
            color: "bg-warning",
          },
          {
            number: "04",
            title: "W okresie obserwacji",
            subtitle: "Zapisuj fakty i przykłady",
            color: "bg-primary",
          },
          {
            number: "03",
            title: "Przygotowane",
            subtitle: "Wymagają czynności formalnych",
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
      <div className="mb-7 grid gap-4 lg:grid-cols-[1.36fr_1fr]">
        <section className="rounded-card border bg-surface px-6 py-6 sm:px-7">
          <p className="flex items-center gap-2 text-label font-semibold text-muted-foreground">
            <span aria-hidden="true" className="size-2 rounded-full bg-warning" />
            Wymaga działania
          </p>
          <div className="mt-5 flex items-center gap-4">
            <span
              aria-hidden="true"
              className="grid size-11 shrink-0 place-items-center rounded-full bg-surface-muted text-sm font-semibold text-primary"
            >
              JK
            </span>
            <div>
              <h2 className="text-xl font-semibold tracking-heading">Jan Kowalski</h2>
              <p className="mt-1 text-body text-muted-foreground">Okres obserwacji · Arkusz C</p>
            </div>
          </div>
          <p className="mt-5 text-body leading-6 text-muted-foreground">
            Przejrzyj zebrane przykłady zachowań i przygotuj się do rozmowy oceniającej.
          </p>
          <dl className="mt-5 grid gap-3 border-y py-4 min-[480px]:grid-cols-3 min-[480px]:gap-4">
            <div>
              <dt className="text-label text-muted-foreground">Etap</dt>
              <dd className="mt-1 text-body font-semibold">Przegląd materiałów</dd>
            </div>
            <div>
              <dt className="text-label text-muted-foreground">Termin</dt>
              <dd className="mt-1 text-body font-semibold">
                {state.assessments.jan?.dateAssessment || "Nie ustalono"}
              </dd>
            </div>
            <div>
              <dt className="text-label text-muted-foreground">Następny krok</dt>
              <dd className="mt-1 text-body font-semibold">Rozmowa oceniająca</dd>
            </div>
          </dl>
          <div className="mt-5">
            <ButtonLink href="/assessments" variant="primary">
              Przejdź do ocen
              <Icon name="arrow-up-right" size={15} />
            </ButtonLink>
          </div>
        </section>
        <Card className="p-6">
          <div className="mb-6 flex items-center justify-between gap-3">
            <h2 className="text-sm font-semibold">Najbliższe zadania</h2>
            <ButtonLink href="/deadlines">Terminy</ButtonLink>
          </div>
          <div className="space-y-5">
            {tasks.map((task) => (
              <Link
                key={task.number}
                href={task.href}
                className="flex w-full items-center gap-3 text-left"
              >
                <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-surface-muted text-label font-semibold text-muted-foreground">
                  {task.number}
                </span>
                <span className="flex-1">
                  <span className="block text-body font-semibold">{task.title}</span>
                  <span className="mt-1 block text-label text-muted-foreground">{task.person}</span>
                </span>
                <Icon name="arrow-up-right" size={15} className="text-subtle-foreground" />
              </Link>
            ))}
          </div>
        </Card>
      </div>
      <Card className="overflow-hidden">
        <div className="flex items-center justify-between gap-3 border-b px-6 py-5">
          <h2 className="text-sm font-semibold">Twoje procesy</h2>
          <ButtonLink href="/assessments">Wszystkie</ButtonLink>
        </div>
        {employees
          .filter(({ id }) => id !== "alicja")
          .map((employee) => {
            const status = assessmentStatus(state.assessments[employee.id]);
            return (
              <Link
                key={employee.id}
                href="/assessments"
                className="flex w-full items-center gap-4 border-b px-6 py-4 text-left last:border-0 hover:bg-surface-muted max-compact:flex-wrap"
              >
                <span className="min-w-0 flex-1">
                  <span className="block text-body font-semibold">{employee.name}</span>
                  <span className="mt-1 block text-caption text-muted-foreground">
                    {employee.role}
                  </span>
                </span>
                <Badge tone={status.tone}>{status.label}</Badge>
                <Icon name="arrow-up-right" size={17} className="text-subtle-foreground" />
              </Link>
            );
          })}
      </Card>
      <p className="mt-5 text-caption text-subtle-foreground">
        Wszystkie osoby, daty i obserwacje są przykładowe. Nie służą do rzeczywistych decyzji
        kadrowych.
      </p>
    </>
  );
}
