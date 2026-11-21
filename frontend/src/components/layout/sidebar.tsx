"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "@/components/ui/icon";
import { Avatar } from "@/components/ui/avatar";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import {
  assessmentHref,
  findEmployee,
} from "@/features/assessments/data/employees";
import { navigation, processNavigation } from "./navigation";

export function Sidebar({
  onNavigate,
  onSearch,
}: {
  onNavigate?: () => void;
  onSearch: () => void;
}) {
  const pathname = usePathname();
  const { state, toggleTheme } = useWorkspace();
  const employee = findEmployee(pathname.split("/")[2] ?? "");
  const assessment = employee ? state.assessments[employee.id] : null;
  const current =
    assessment?.step === "recommendation"
      ? "rating"
      : assessment?.step === "saved"
        ? "timing"
        : assessment?.step === "finished"
          ? "document"
          : assessment?.step;
  const currentIndex = processNavigation.findIndex(
    ({ step }) => step === current,
  );
  const linkClass =
    "flex min-h-[2.5625rem] w-full items-center gap-3 rounded-[0.6875rem] border px-3 py-2.5 text-left text-[0.8125rem] font-medium transition-colors";

  return (
    <div className="flex min-h-full flex-col bg-sidebar">
      <div className="flex items-center justify-between px-5 pt-6 pb-7">
        <Link
          href="/"
          onClick={onNavigate}
          aria-label="Kompas — przejdź do pulpitu"
          className="flex items-center gap-3"
        >
          <span className="flex size-[2.125rem] items-center justify-center rounded-[0.6875rem] bg-primary-action text-white shadow-sm">
            <Icon name="compass" size={21} />
          </span>
          <span>
            <strong className="block text-[0.9375rem] leading-4 tracking-tight">
              kompas<span className="text-primary">.</span>
            </strong>
            <span className="text-[0.5625rem] font-bold tracking-[0.18em] text-subtle-foreground uppercase">
              kompetencji
            </span>
          </span>
        </Link>
      </div>
      <div className="px-4 pb-6">
        <button
          onClick={onSearch}
          type="button"
          className="flex h-10 w-full items-center gap-2.5 rounded-control border bg-surface px-3 text-body text-muted-foreground"
        >
          <Icon name="search" size={16} />
          <span className="flex-1 text-left">Szukaj w Kompasie</span>
          <kbd className="rounded-md border px-1.5 py-0.5 text-caption text-subtle-foreground">
            Ctrl K
          </kbd>
        </button>
      </div>
      <div className="px-4">
        <p className="eyebrow mx-3 mb-3 text-caption">Przestrzeń robocza</p>
        <nav aria-label="Sekcje aplikacji" className="space-y-1">
          {navigation.map(({ href, label, icon }) => {
            const active =
              href === "/" ? pathname === href : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                onClick={onNavigate}
                aria-current={active ? "page" : undefined}
                className={`${linkClass} ${active ? "border-border bg-surface font-semibold text-foreground shadow-navigation" : "border-transparent text-muted-foreground hover:bg-surface/80 hover:text-foreground"}`}
              >
                <Icon
                  name={icon}
                  size={17}
                  className={active ? "shrink-0 text-primary" : "shrink-0"}
                />
                <span>{label}</span>
                {href === "/assessments" ? (
                  <span className="ml-auto text-caption text-subtle-foreground">
                    03
                  </span>
                ) : null}
              </Link>
            );
          })}
        </nav>
      </div>
      {employee && assessment && assessment.type === "periodic" ? (
        <div className="mx-4 mt-6 border-t pt-6 pb-4">
          <p className="eyebrow mx-3 mb-3 text-caption">Bieżąca ocena</p>
          <div className="mb-3 flex items-center gap-2 px-2">
            <Avatar employee={employee} size={29} />
            <div>
              <p className="text-label font-semibold">{employee.name}</p>
              <p className="text-caption text-subtle-foreground">
                Ocena okresowa
              </p>
            </div>
          </div>
          <nav aria-label="Etapy oceny" className="space-y-0.5">
            {processNavigation.map(({ step, label }, index) => {
              const content = (
                <>
                  <span
                    className={`grid size-6 shrink-0 place-items-center rounded-lg border text-caption font-bold ${index === currentIndex ? "border-primary-border bg-primary-muted text-primary" : index < currentIndex ? "border-transparent bg-success-muted text-success" : "bg-surface-muted"}`}
                  >
                    {index < currentIndex ? (
                      <Icon name="check" size={13} />
                    ) : (
                      index + 1
                    )}
                  </span>
                  {label}
                </>
              );
              const className = `flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-label ${index === currentIndex ? "bg-surface font-bold" : "text-muted-foreground"}`;
              return index <= currentIndex ? (
                <Link
                  key={step}
                  href={assessmentHref(employee.id, step)}
                  onClick={onNavigate}
                  className={className}
                  aria-current={index === currentIndex ? "step" : undefined}
                >
                  {content}
                </Link>
              ) : (
                <span
                  key={step}
                  aria-disabled="true"
                  className={`${className} opacity-45`}
                >
                  {content}
                </span>
              );
            })}
          </nav>
        </div>
      ) : null}
      <div className="mt-auto px-4 pt-6 pb-4">
        <div className="border-t pt-4">
          <Link
            href="/hr"
            onClick={onNavigate}
            className={`${linkClass} ${pathname === "/hr" ? "border-border bg-surface" : "border-transparent text-muted-foreground"}`}
          >
            <Icon name="shield" size={17} />
            <span>Widok HR</span>
            <Icon name="chevron-right" size={14} className="ml-auto" />
          </Link>
          <button
            type="button"
            onClick={toggleTheme}
            className={`${linkClass} border-transparent text-muted-foreground hover:bg-surface`}
          >
            <Icon name={state.theme === "dark" ? "sun" : "moon"} size={17} />
            <span>{state.theme === "dark" ? "Tryb jasny" : "Tryb ciemny"}</span>
          </button>
        </div>
        <div className="mt-4 flex items-center gap-2 px-2">
          <span className="grid size-8 place-items-center rounded-full bg-avatar-peach text-label font-bold text-avatar-peach-foreground">
            AN
          </span>
          <div>
            <p className="text-label font-semibold">Anna Nowak</p>
            <p className="text-caption text-subtle-foreground">
              Przełożona · Demo
            </p>
          </div>
          <Icon
            name="more"
            size={17}
            className="ml-auto text-subtle-foreground"
          />
        </div>
      </div>
    </div>
  );
}
