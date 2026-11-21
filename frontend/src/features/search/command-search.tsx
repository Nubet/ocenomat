"use client";

import Link from "next/link";
import { useState } from "react";
import { Dialog } from "@/components/ui/dialog";
import { Icon } from "@/components/ui/icon";
import { navigation } from "@/components/layout/navigation";
import { employees, assessmentHref } from "@/features/assessments/data/employees";

export function CommandSearch({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState("");
  const choices = [
    ...navigation,
    ...employees.map((employee) => ({
      href: assessmentHref(employee.id),
      label: `${employee.name} · ${employee.role}`,
      icon: "users" as const,
    })),
  ].filter(({ label }) => label.toLocaleLowerCase("pl").includes(query.toLocaleLowerCase("pl")));
  return (
    <Dialog title="Szukaj w Kompasie" onClose={onClose}>
      <div className="flex items-center gap-3 border-b p-5">
        <Icon name="search" />
        <label className="min-w-0 flex-1">
          <span className="sr-only">Szukana fraza</span>
          <input
            className="field"
            placeholder="Znajdź ekran lub pracownika…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      </div>
      <div className="max-h-80 overflow-y-auto p-2">
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
        ) : (
          <output className="block p-5 text-center text-body text-muted-foreground">
            Brak wyników.
          </output>
        )}
      </div>
    </Dialog>
  );
}
