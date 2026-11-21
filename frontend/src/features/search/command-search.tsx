"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Dialog } from "@/components/ui/dialog";
import { Icon } from "@/components/ui/icon";
import { navigation } from "@/components/layout/navigation";
import { employeeHref, type EmployeeRecord } from "@/features/employees/types";
import { searchEmployees } from "@/features/employees/search-action";

export function CommandSearch({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<{
    query: string;
    items: EmployeeRecord[];
    total: number;
    error?: string;
  } | null>(null);
  useEffect(() => {
    let ignore = false;
    const timer = setTimeout(() => {
      searchEmployees(query)
        .then((data) => {
          if (!ignore) setResult({ ...data, query });
        })
        .catch(() => {
          if (!ignore)
            setResult({
              query,
              items: [],
              total: 0,
              error: "Nie udało się wyszukać pracowników. Spróbuj ponownie.",
            });
        });
    }, 250);
    return () => {
      ignore = true;
      clearTimeout(timer);
    };
  }, [query]);
  const current = result?.query === query ? result : null;
  const choices = [
    ...navigation.filter(({ label }) =>
      label.toLocaleLowerCase("pl").includes(query.toLocaleLowerCase("pl")),
    ),
    ...(current?.items ?? []).map((employee) => ({
      href: employeeHref(employee.id),
      label: `${employee.name} · ${employee.position}`,
      icon: "users" as const,
    })),
  ];
  return (
    <Dialog title="Szukaj w OcenoMat" onClose={onClose}>
      <div className="flex items-center gap-3 border-b p-5">
        <Icon name="search" />
        <label className="min-w-0 flex-1">
          <span className="sr-only">Szukana fraza</span>
          <input
            className="field"
            placeholder="Znajdź ekran lub pracownika…"
            value={query}
            maxLength={100}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      </div>
      <div className="max-h-80 overflow-y-auto p-2" aria-busy={!current}>
        {!current ? (
          <output className="block p-3 text-body text-muted-foreground">Szukam pracowników…</output>
        ) : null}
        {current?.error ? (
          <p role="alert" className="p-3 text-body text-danger">
            {current.error}
          </p>
        ) : null}
        {choices.length ? (
          choices.map(({ href, label, icon }) => (
            <Link
              key={href}
              href={href}
              onClick={onClose}
              className="flex items-center gap-3 rounded-lg px-3 py-3 text-body hover:bg-surface-muted"
            >
              <Icon name={icon} size={17} className="text-subtle-foreground" />
              <span className="flex-1">{label}</span>
              <Icon name="chevron-right" size={15} />
            </Link>
          ))
        ) : current && !current.error ? (
          <output className="block p-5 text-center text-body text-muted-foreground">
            Nie znaleźliśmy pasujących wyników. Wpisz krótszą nazwę lub sprawdź pisownię. Jeśli
            szukasz pracownika, którego nie widzisz na liście, poproś administratora o sprawdzenie
            dostępu.
          </output>
        ) : null}
        {current && current.total > current.items.length ? (
          <Link
            href={`/employees?${new URLSearchParams({ q: query })}`}
            onClick={onClose}
            className="block rounded-lg border-t px-3 py-3 text-body font-semibold text-primary hover:bg-surface-muted"
          >
            Pokaż wszystkie wyniki ({current.total})
          </Link>
        ) : null}
      </div>
    </Dialog>
  );
}
