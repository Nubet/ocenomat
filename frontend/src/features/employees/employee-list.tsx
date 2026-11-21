import Link from "next/link";
import Form from "next/form";
import { Card, PageHeading } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
import { Button, ButtonLink } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { employeeHref, type EmployeePage } from "./types";
import { employeeListHref, employeeSorts, positionKinds, type EmployeeQuery } from "./query";
import type { WorkspaceUser } from "@/features/auth/session";

export function EmployeeList({
  result,
  query,
  roles,
}: {
  result: EmployeePage;
  query: EmployeeQuery;
  roles: WorkspaceUser["roles"];
}) {
  const filtered = Boolean(query.q || query.position_kind);
  const first = (result.page - 1) * result.page_size + 1;
  return (
    <>
      <PageHeading
        eyebrow="Zespół"
        title="Pracownicy"
        description="Znajdź osobę w zespole, otwórz jej profil i przejdź do historii ocen."
      />
      <Card className="mb-5 p-4 sm:p-5">
        <Form
          action="/employees"
          scroll={false}
          key={employeeListHref(query)}
          aria-label="Wyszukiwanie i filtrowanie pracowników"
        >
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_auto] xl:items-end">
            <label className="sm:col-span-2 xl:col-span-1">
              <span className="field-label">Szukaj pracownika</span>
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
                  aria-describedby="employee-search-hint"
                />
              </span>
            </label>
            <label>
              <span className="field-label">Typ stanowiska</span>
              <select name="position_kind" defaultValue={query.position_kind} className="field">
                <option value="">Wszystkie stanowiska</option>
                {Object.entries(positionKinds).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <Button type="submit" variant="primary" className="self-end">
              Szukaj
            </Button>
          </div>
          <p id="employee-search-hint" className="mt-2 text-label text-muted-foreground">
            Możesz wpisać np. „radca” lub „Anna Kowalska”. Polskie znaki są opcjonalne.
          </p>
          <div className="mt-4 flex flex-wrap items-end gap-3 border-t pt-4">
            <label className="min-w-48 flex-1 sm:max-w-64">
              <span className="field-label">Sortowanie</span>
              <select name="sort" defaultValue={query.sort} className="field">
                {Object.entries(employeeSorts).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label className="w-32">
              <span className="field-label">Na stronie</span>
              <select name="page_size" defaultValue={query.page_size} className="field">
                {[10, 20, 50].map((size) => (
                  <option key={size} value={size}>
                    {size} osób
                  </option>
                ))}
              </select>
            </label>
            <Button type="submit">Zastosuj</Button>
            {filtered ? (
              <ButtonLink href="/employees" variant="ghost" scroll={false}>
                <Icon name="close" size={14} />
                Wyczyść filtry
              </ButtonLink>
            ) : null}
          </div>
        </Form>
      </Card>
      <div
        id="employee-results"
        className="mb-3 flex scroll-mt-5 flex-wrap items-center justify-between gap-2 text-body text-muted-foreground"
      >
        <output>
          {result.total > 0 ? (
            <>
              <span className="font-semibold text-foreground">
                {first}–{Math.min(first + result.page_size - 1, result.total)}
              </span>{" "}
              z {result.total} osób
            </>
          ) : (
            "0 osób"
          )}
          {filtered ? " · wyniki wyszukiwania" : ""}
        </output>
        <span className="text-label">Widoczne są osoby, do których masz dostęp</span>
      </div>
      {result.items.length > 0 ? (
        <Card className="overflow-hidden">
          <div
            aria-hidden="true"
            className="hidden grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)_1rem] gap-4 border-b bg-surface-muted px-6 py-3 text-label font-semibold text-muted-foreground md:grid"
          >
            <span>Pracownik</span>
            <span>Stanowisko</span>
            <span>Komórka</span>
          </div>
          <ul>
            {result.items.map((employee) => (
              <li key={employee.id} className="border-b last:border-0">
                <Link
                  href={{
                    pathname: employeeHref(employee.id),
                    query: { ...query, page: result.page },
                  }}
                  className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1 px-6 py-4 text-left transition-colors hover:bg-surface-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary md:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)_1rem] md:gap-4"
                >
                  <span className="row-span-3 md:row-span-1 md:flex md:min-w-0 md:items-center md:gap-3">
                    <Avatar employee={employee} size={40} />
                    <span className="hidden text-sm font-semibold md:block">{employee.name}</span>
                  </span>
                  <span className="min-w-0 text-sm font-semibold md:hidden">{employee.name}</span>
                  <span className="col-start-2 max-w-full justify-self-start rounded-md bg-primary-muted px-3 py-1 text-[0.8125rem] font-medium text-primary-strong md:col-auto">
                    {employee.position}
                  </span>
                  <span className="col-start-2 text-body text-muted-foreground md:col-auto">
                    {employee.department}
                  </span>
                  <Icon
                    name="chevron-right"
                    size={16}
                    className="col-start-3 row-span-3 row-start-1 text-subtle-foreground md:col-auto md:row-auto"
                  />
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      ) : (
        <Card className="flex items-start gap-4 p-6 text-body text-muted-foreground">
          <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-surface-muted text-primary">
            <Icon name="users" size={20} />
          </span>
          <div>
            <h2 className="font-semibold text-foreground">
              {filtered
                ? "Nie znaleziono pasujących pracowników"
                : "Nie ma jeszcze pracowników na tej liście"}
            </h2>
            <p className="mt-2 leading-6">
              {filtered
                ? "Spróbuj wpisać krótsze nazwisko lub stanowisko albo wybierz inny typ stanowiska."
                : roles.includes("ADMIN")
                  ? "Zleć osobie obsługującej wdrożenie dodanie pracowników i przypisanie ich przełożonym. Panel do tych zmian nie jest jeszcze dostępny w aplikacji."
                  : roles.includes("HR")
                    ? "Poproś administratora o sprawdzenie, czy pracownicy zostali dodani do organizacji."
                    : roles.includes("MANAGER")
                      ? "Poproś administratora o przypisanie osób, których oceny masz prowadzić. Podaj swój adres logowania oraz imiona i nazwiska pracowników."
                      : "Poproś administratora o sprawdzenie roli Twojego konta. Podaj adres, którym logujesz się do aplikacji."}
            </p>
            <ButtonLink href={filtered ? "/employees" : "/help"} className="mt-4">
              {filtered ? "Wyczyść filtry" : "Sprawdź role i dostęp"}
            </ButtonLink>
          </div>
        </Card>
      )}
      {result.total_pages > 1 ? (
        <nav
          aria-label="Strony listy pracowników"
          className="mt-5 flex flex-wrap items-center justify-between gap-3"
        >
          {result.page > 1 ? (
            <ButtonLink
              href={`${employeeListHref(query, result.page - 1)}#employee-results`}
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
            Strona <strong className="text-foreground">{result.page}</strong> z {result.total_pages}
          </span>
          {result.page < result.total_pages ? (
            <ButtonLink
              href={`${employeeListHref(query, result.page + 1)}#employee-results`}
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
