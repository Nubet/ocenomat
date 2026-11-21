import Link from "next/link";
import Form from "next/form";
import { Card, PageHeading } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { assessmentHref } from "@/features/assessments/types";
import { deadlineLabels, monitoringDate, type Monitoring } from "@/features/monitoring/types";
import {
  deadlineListHref,
  deadlineStatus,
  deadlineStatuses,
  getDeadlinePage,
  type DeadlineParams,
} from "./query";

export function Deadlines({
  monitoring,
  params = {},
}: {
  monitoring: Monitoring;
  params?: DeadlineParams;
}) {
  const result = getDeadlinePage(monitoring.deadlines, params);
  const { query } = result;
  const filtered = Boolean(query.q || query.status !== "all");
  const first = (result.page - 1) * result.pageSize + 1;
  return (
    <>
      <PageHeading
        eyebrow="Planowanie"
        title="Terminy"
        description="Sprawdź, co wymaga uwagi, i znajdź najbliższe działania w ocenach."
      />
      <nav aria-label="Status terminów" className="mb-5 flex flex-wrap gap-2">
        {Object.entries(deadlineStatuses).map(([status, label]) => (
          <Link
            key={status}
            href={deadlineListHref(query, { status, page: "1" })}
            scroll={false}
            aria-current={query.status === status ? "page" : undefined}
            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2.5 text-body font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-primary ${query.status === status ? "border-primary-border bg-primary-muted text-primary-strong" : "border-border bg-surface text-muted-foreground hover:bg-surface-muted"}`}
          >
            {label}
            <span className="rounded-md bg-surface-muted px-2 py-0.5 text-label text-foreground tabular-nums">
              {status === "all"
                ? monitoring.deadlines.length
                : monitoring.deadlines.filter((deadline) => deadlineStatus(deadline) === status)
                    .length}
            </span>
          </Link>
        ))}
      </nav>
      <Card className="mb-5 p-4 sm:p-5">
        <Form
          action="/deadlines"
          scroll={false}
          key={deadlineListHref(query)}
          aria-label="Wyszukiwanie i sortowanie terminów"
        >
          <input type="hidden" name="status" value={query.status} />
          <div className="flex flex-wrap items-end gap-3">
            <label className="min-w-48 flex-1">
              <span className="field-label">Szukaj terminu</span>
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
                  placeholder="Imię, nazwisko lub działanie…"
                  className="field pl-10"
                />
              </span>
            </label>
            <label className="min-w-48 flex-1 sm:max-w-64">
              <span className="field-label">Sortowanie</span>
              <select name="sort" defaultValue={query.sort} className="field">
                <option value="date_asc">Od najwcześniejszego</option>
                <option value="date_desc">Od najpóźniejszego</option>
              </select>
            </label>
            <label className="w-28">
              <span className="field-label">Na stronie</span>
              <select name="page_size" defaultValue={query.page_size} className="field">
                {[10, 20, 50].map((size) => (
                  <option key={size} value={size}>
                    {size} terminów
                  </option>
                ))}
              </select>
            </label>
            <Button type="submit" variant="primary">
              Zastosuj
            </Button>
            {filtered ? (
              <ButtonLink href="/deadlines" variant="ghost" scroll={false}>
                Wyczyść filtry
              </ButtonLink>
            ) : null}
          </div>
        </Form>
      </Card>
      <div
        id="deadline-results"
        className="mb-3 flex scroll-mt-5 flex-wrap items-center justify-between gap-2 text-body text-muted-foreground"
      >
        <output>
          {result.total > 0 ? (
            <>
              <span className="font-semibold text-foreground">
                {first}–{Math.min(first + result.pageSize - 1, result.total)}
              </span>{" "}
              z {result.total} terminów
            </>
          ) : (
            "0 terminów"
          )}
        </output>
        <span className="text-label">
          Bliski termin: najbliższe {monitoring.attention_window_days} dni
        </span>
      </div>
      <Card className="overflow-hidden">
        {result.items.length > 0 ? (
          <ul className="divide-y divide-border">
            {result.items.map((deadline) => (
              <li key={`${deadline.assessment_id}:${deadline.kind}`}>
                <Link
                  href={assessmentHref(deadline.assessment_id)}
                  className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-5 py-4 transition-colors hover:bg-surface-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary sm:grid-cols-[7rem_minmax(0,1fr)_auto_auto] sm:gap-5 sm:px-6"
                >
                  <span className="text-caption font-semibold text-primary tabular-nums">
                    {monitoringDate(deadline.due_on)}
                  </span>
                  <span className="col-start-1 row-start-2 min-w-0 sm:col-auto sm:row-auto">
                    <span className="block text-sm font-semibold">{deadline.employee_name}</span>
                    <span className="mt-1 block text-label text-muted-foreground">
                      {deadlineLabels[deadline.kind]}
                    </span>
                  </span>
                  <span
                    className={`col-start-2 row-start-2 sm:col-auto sm:row-auto ${deadline.overdue ? "[&>span]:border-warning/25 [&>span]:bg-warning/20" : ""}`}
                  >
                    <Badge tone={deadline.overdue || deadline.due_soon ? "warning" : "primary"}>
                      {deadline.overdue
                        ? "Po terminie"
                        : deadline.due_soon
                          ? "Bliski termin"
                          : "Zaplanowano"}
                    </Badge>
                  </span>
                  <Icon
                    name="chevron-right"
                    size={16}
                    className="col-start-2 row-start-1 justify-self-end text-subtle-foreground sm:col-auto sm:row-auto"
                  />
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <div className="p-6 sm:p-8">
            <h2 className="text-sm font-semibold">
              {filtered
                ? "Nie znaleziono pasujących terminów"
                : "Brak zapisanych terminów aktywnych ocen"}
            </h2>
            <p className="mt-2 text-body text-muted-foreground">
              {filtered
                ? "Zmień frazę lub wybierz inny status, aby zobaczyć pozostałe działania."
                : "Terminy pojawią się po ustaleniu dat w prowadzonych ocenach."}
            </p>
            {filtered ? (
              <ButtonLink href="/deadlines" className="mt-4">
                Wyczyść filtry
              </ButtonLink>
            ) : null}
          </div>
        )}
      </Card>
      {result.totalPages > 1 ? (
        <nav
          aria-label="Strony listy terminów"
          className="mt-5 flex flex-wrap items-center justify-between gap-3"
        >
          {result.page > 1 ? (
            <ButtonLink
              href={`${deadlineListHref(query, { page: String(result.page - 1) })}#deadline-results`}
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
              href={`${deadlineListHref(query, { page: String(result.page + 1) })}#deadline-results`}
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
      <p className="mt-5 text-label text-muted-foreground">
        Stan na {monitoringDate(monitoring.as_of)}. Przypomnienia wysłane przez HR znajdziesz na
        pulpicie.
      </p>
    </>
  );
}
