import Link from "next/link";
import Form from "next/form";
import { Card, PageHeading } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { Icon } from "@/components/ui/icon";
import { NewAssessmentButton } from "./components/new-assessment-button";
import { assessmentHref, assessmentStatusLabels, type AssessmentRecord } from "./types";
import { Button, ButtonLink } from "@/components/ui/button";
import type { WorkspaceUser } from "@/features/auth/session";
import {
  assessmentGroups,
  assessmentListHref,
  assessmentSorts,
  getAssessmentListPage,
  type AssessmentListParams,
} from "./list-query";

export function AssessmentEmptyState({
  roles,
  canCreate,
  employeeId,
}: {
  roles: WorkspaceUser["roles"];
  canCreate: boolean;
  employeeId?: string;
}) {
  const manager = roles.includes("MANAGER");
  return (
    <div className="px-6 py-6">
      <h2 className="text-body font-semibold">
        {manager
          ? employeeId
            ? "Nie prowadzisz jeszcze oceny tej osoby"
            : "Nie prowadzisz jeszcze żadnej oceny"
          : "Ten widok jest dla przełożonych prowadzących oceny"}
      </h2>
      <p className="mt-2 text-body leading-6 text-muted-foreground">
        {manager
          ? canCreate
            ? "Rozpocznij nową ocenę i wybierz pracownika. Zapisana ocena pojawi się tutaj — możesz do niej wrócić później."
            : "Aby rozpocząć ocenę, potrzebujesz przypisania pracownika. Poproś administratora o sprawdzenie przypisania; podaj swój adres logowania oraz imię i nazwisko pracownika."
          : roles.includes("HR")
            ? "Jako HR możesz przeglądać profile pracowników oraz etapy i terminy w panelu HR. Treść ocen jest dostępna tylko dla przełożonego, który je prowadzi."
            : roles.includes("ADMIN")
              ? "Sama rola administratora nie udostępnia treści ocen. Jeśli masz je prowadzić, zleć osobie obsługującej wdrożenie dodanie roli przełożonego i przypisanie pracownika."
              : "Poproś administratora o nadanie roli odpowiedniej do Twoich obowiązków. Podaj adres, którym logujesz się do aplikacji."}
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {manager && canCreate ? <NewAssessmentButton employeeId={employeeId} /> : null}
        {roles.some((role) => ["MANAGER", "HR", "ADMIN"].includes(role)) ? (
          <ButtonLink href="/employees">Sprawdź pracowników</ButtonLink>
        ) : null}
        <ButtonLink href="/help" variant="ghost">
          Sprawdź role i dostęp
        </ButtonLink>
      </div>
    </div>
  );
}

export function AssessmentRows({
  assessments,
  emptyState,
}: {
  assessments: AssessmentRecord[];
  emptyState: React.ReactNode;
}) {
  if (assessments.length === 0) return emptyState;
  return assessments.map((assessment) => (
    <Link
      key={assessment.id}
      href={assessmentHref(assessment.id)}
      className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-b px-5 py-4 transition-colors last:border-0 hover:bg-surface-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary sm:px-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_minmax(0,1fr)_1rem] lg:gap-5"
    >
      <span className="flex min-w-0 items-center gap-3">
        <Avatar employee={assessment.employee_snapshot} size={40} />
        <span className="min-w-0">
          <strong className="block text-sm font-semibold">
            {assessment.employee_snapshot.name}
          </strong>
          <span className="mt-1 block text-label text-muted-foreground">
            {assessment.employee_snapshot.position}
          </span>
        </span>
      </span>
      <span className="col-start-1 pl-[3.25rem] lg:col-auto lg:pl-0">
        <span className="block text-body font-medium">
          {assessment.kind === "first" ? "Pierwsza ocena" : "Ocena okresowa"} · {assessment.form}
        </span>
        <span className="mt-1 block text-caption text-muted-foreground">
          Utworzono{" "}
          {new Date(assessment.created_at).toLocaleDateString("pl-PL", {
            timeZone: "Europe/Warsaw",
          })}
        </span>
      </span>
      <span className="col-start-1 justify-self-start pl-[3.25rem] lg:col-auto lg:pl-0">
        <Badge
          tone={
            assessment.status === "completed"
              ? "success"
              : assessment.status === "draft"
                ? "neutral"
                : "primary"
          }
        >
          {assessmentStatusLabels[assessment.status]}
        </Badge>
      </span>
      <Icon
        name="chevron-right"
        size={16}
        className="col-start-2 row-start-1 text-subtle-foreground lg:col-auto lg:row-auto"
      />
    </Link>
  ));
}

export function AssessmentList({
  assessments,
  canCreate,
  roles,
  params = {},
}: {
  assessments: AssessmentRecord[];
  canCreate: boolean;
  roles: WorkspaceUser["roles"];
  params?: AssessmentListParams;
}) {
  const result = getAssessmentListPage(assessments, params);
  const { query } = result;
  const filtered = Boolean(query.q || query.status || query.kind || query.group !== "all");
  const first = (result.page - 1) * result.pageSize + 1;
  const completed = assessments.filter((assessment) => assessment.status === "completed").length;
  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-x-6">
        <PageHeading
          eyebrow="Zarządzanie procesami"
          title="Oceny pracownicze"
          description="Wróć do rozpoczętej oceny, sprawdź etap procesu lub odszukaj zakończoną ocenę."
        />
        {canCreate && assessments.length > 0 ? (
          <div className="mb-5 sm:mt-8">
            <NewAssessmentButton />
          </div>
        ) : null}
      </div>
      {assessments.length > 0 ? (
        <>
          <nav aria-label="Grupy ocen" className="mb-5 flex flex-wrap gap-2">
            {Object.entries(assessmentGroups).map(([group, label]) => (
              <Link
                key={group}
                href={assessmentListHref(query, { group, status: "", page: "1" })}
                scroll={false}
                aria-current={query.group === group ? "page" : undefined}
                className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2.5 text-body font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-primary ${query.group === group ? "border-primary-border bg-primary-muted text-primary-strong" : "border-border bg-surface text-muted-foreground hover:bg-surface-muted"}`}
              >
                {label}
                <span className="rounded-md bg-surface-muted px-2 py-0.5 text-label text-foreground tabular-nums">
                  {group === "all"
                    ? assessments.length
                    : group === "completed"
                      ? completed
                      : assessments.length - completed}
                </span>
              </Link>
            ))}
          </nav>
          <Card className="mb-5 p-4 sm:p-5">
            <Form
              action="/assessments"
              scroll={false}
              key={assessmentListHref(query)}
              aria-label="Wyszukiwanie i filtrowanie ocen"
            >
              <input type="hidden" name="group" value={query.group} />
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)]">
                <label className="sm:col-span-2 xl:col-span-1">
                  <span className="field-label">Szukaj oceny</span>
                  <span className="relative block">
                    <Icon
                      name="search"
                      size={18}
                      className="pointer-events-none absolute top-3 left-3 text-subtle-foreground"
                    />
                    <input
                      type="search"
                      name="q"
                      defaultValue={query.q}
                      maxLength={100}
                      placeholder="Imię, nazwisko lub stanowisko…"
                      className="field pl-10"
                    />
                  </span>
                </label>
                <label>
                  <span className="field-label">Etap procesu</span>
                  <select name="status" defaultValue={query.status} className="field">
                    <option value="">Wszystkie etapy</option>
                    {Object.entries(assessmentStatusLabels)
                      .filter(
                        ([status]) =>
                          query.group === "all" ||
                          (query.group === "completed"
                            ? status === "completed"
                            : status !== "completed"),
                      )
                      .map(([status, label]) => (
                        <option key={status} value={status}>
                          {label}
                        </option>
                      ))}
                  </select>
                </label>
                <label>
                  <span className="field-label">Rodzaj oceny</span>
                  <select name="kind" defaultValue={query.kind} className="field">
                    <option value="">Wszystkie rodzaje</option>
                    <option value="periodic">Ocena okresowa</option>
                    <option value="first">Pierwsza ocena</option>
                  </select>
                </label>
              </div>
              <div className="mt-4 flex flex-wrap items-end gap-3 border-t pt-4">
                <label className="min-w-48 flex-1 sm:max-w-64">
                  <span className="field-label">Sortowanie</span>
                  <select name="sort" defaultValue={query.sort} className="field">
                    {Object.entries(assessmentSorts).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="w-28">
                  <span className="field-label">Na stronie</span>
                  <select name="page_size" defaultValue={query.page_size} className="field">
                    {[10, 20, 50].map((size) => (
                      <option key={size} value={size}>
                        {size} ocen
                      </option>
                    ))}
                  </select>
                </label>
                <Button type="submit" variant="primary">
                  Zastosuj
                </Button>
                {filtered ? (
                  <ButtonLink href="/assessments" variant="ghost" scroll={false}>
                    Wyczyść filtry
                  </ButtonLink>
                ) : null}
              </div>
            </Form>
          </Card>
          <div
            id="assessment-results"
            className="mb-3 flex scroll-mt-5 flex-wrap items-center justify-between gap-2 text-body text-muted-foreground"
          >
            <output>
              {result.total > 0 ? (
                <>
                  <span className="font-semibold text-foreground">
                    {first}–{Math.min(first + result.pageSize - 1, result.total)}
                  </span>{" "}
                  z {result.total} ocen
                </>
              ) : (
                "0 ocen"
              )}
            </output>
          </div>
        </>
      ) : null}
      <Card className="overflow-hidden">
        {result.items.length > 0 ? (
          <div
            aria-hidden="true"
            className="hidden grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_minmax(0,1fr)_1rem] gap-5 border-b bg-surface-muted px-6 py-3 text-label font-semibold text-muted-foreground lg:grid"
          >
            <span>Pracownik</span>
            <span>Rodzaj i data utworzenia</span>
            <span>Etap procesu</span>
          </div>
        ) : null}
        <AssessmentRows
          assessments={result.items}
          emptyState={
            assessments.length > 0 ? (
              <div className="p-6 sm:p-8">
                <h2 className="text-sm font-semibold">Nie znaleziono pasujących ocen</h2>
                <p className="mt-2 text-body text-muted-foreground">
                  Zmień frazę, etap lub rodzaj oceny albo wybierz inną zakładkę.
                </p>
                <ButtonLink href="/assessments" className="mt-4">
                  Wyczyść filtry
                </ButtonLink>
              </div>
            ) : (
              <AssessmentEmptyState roles={roles} canCreate={canCreate} />
            )
          }
        />
      </Card>
      {result.totalPages > 1 ? (
        <nav
          aria-label="Strony listy ocen"
          className="mt-5 flex flex-wrap items-center justify-between gap-3"
        >
          {result.page > 1 ? (
            <ButtonLink
              href={`${assessmentListHref(query, { page: String(result.page - 1) })}#assessment-results`}
              rel="prev"
            >
              <Icon name="chevron-left" size={16} />
              Poprzednia
            </ButtonLink>
          ) : (
            <Button disabled>
              <Icon name="chevron-left" size={16} />
              Poprzednia
            </Button>
          )}
          <span className="text-body text-muted-foreground">
            Strona <strong className="text-foreground">{result.page}</strong> z {result.totalPages}
          </span>
          {result.page < result.totalPages ? (
            <ButtonLink
              href={`${assessmentListHref(query, { page: String(result.page + 1) })}#assessment-results`}
              rel="next"
            >
              Następna
              <Icon name="chevron-right" size={16} />
            </ButtonLink>
          ) : (
            <Button disabled>
              Następna
              <Icon name="chevron-right" size={16} />
            </Button>
          )}
        </nav>
      ) : null}
    </>
  );
}
