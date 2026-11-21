"use client";

import { Suspense, useEffect, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { AssistantDrawer } from "@/features/assistant/assistant-drawer";
import { CommandSearch } from "@/features/search/command-search";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import type { WorkspaceUser } from "@/features/auth/session";
import type { EmployeeRecord } from "@/features/employees/types";
import { Sidebar } from "./sidebar";
import { navigation } from "./navigation";

export function AppShell({
  children,
  user,
  employees,
}: {
  children: ReactNode;
  user: WorkspaceUser;
  employees: EmployeeRecord[];
}) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const { openAssistant, assistantOpen } = useWorkspace();
  const label =
    pathname === "/hr"
      ? "Panel HR"
      : (navigation.find(({ href }) =>
          href === "/" ? pathname === href : pathname.startsWith(href),
        )?.label ?? "Kompas");

  useEffect(() => {
    function shortcut(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        if (!assistantOpen) {
          setMobileOpen(false);
          setSearchOpen((open) => !open);
        }
      }
    }
    document.addEventListener("keydown", shortcut);
    return () => document.removeEventListener("keydown", shortcut);
  }, [assistantOpen]);

  function search() {
    setMobileOpen(false);
    setSearchOpen(true);
  }

  return (
    <>
      <a
        href="#main-content"
        className="no-print sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-100 focus:rounded-lg focus:bg-surface focus:px-4 focus:py-3"
      >
        Przejdź do głównej treści
      </a>
      <div className="print-layout min-h-dvh min-[801px]:max-[1100px]:grid-cols-[14.375rem_minmax(0,1fr)] navigation:grid navigation:grid-cols-[var(--spacing-sidebar)_minmax(0,1fr)]">
        <aside
          className="no-print sticky top-0 hidden h-dvh overflow-y-auto border-r navigation:block"
          aria-label="Nawigacja główna"
        >
          <Sidebar user={user} onSearch={search} />
        </aside>
        <div className="print-layout min-w-0">
          <header className="no-print flex h-[3.9375rem] items-center justify-between gap-3 border-b bg-surface px-[1.1875rem] navigation:h-18 navigation:px-[2.375rem]">
            <div className="flex min-w-0 items-center gap-3">
              <Button
                aria-label="Otwórz menu"
                className="size-10 p-0! navigation:hidden"
                onClick={() => setMobileOpen(true)}
              >
                <Icon name="menu" />
              </Button>
              <span className="hidden text-body text-subtle-foreground navigation:inline">
                Kompas
              </span>
              <Icon
                name="chevron-right"
                size={14}
                className="hidden text-subtle-foreground navigation:block"
              />
              <span className="truncate text-body font-semibold">{label}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="hidden navigation:inline">
                <Badge>
                  <Icon name="info" size={12} />
                  Dane demonstracyjne
                </Badge>
              </span>
              <Button onClick={openAssistant} aria-label="Otwórz asystenta Kompas">
                <Icon name="sparkles" size={16} />
                <span className="hidden compact:inline">Zapytaj Kompas</span>
              </Button>
            </div>
          </header>
          <main
            id="main-content"
            tabIndex={-1}
            className="print-layout mx-auto w-full max-w-workspace px-[0.8125rem] pt-6 pb-24 outline-none min-[1101px]:px-[2.6875rem] min-[1101px]:pt-[2.375rem] compact:px-[1.1875rem] compact:pt-7 navigation:px-[1.6875rem] navigation:pt-[1.875rem]"
          >
            {children}
          </main>
        </div>
      </div>
      {mobileOpen ? (
        <Dialog title="Menu" onClose={() => setMobileOpen(false)} drawer="left">
          <Sidebar user={user} onNavigate={() => setMobileOpen(false)} onSearch={search} />
        </Dialog>
      ) : null}
      {searchOpen ? (
        <CommandSearch employees={employees} onClose={() => setSearchOpen(false)} />
      ) : null}
      <Suspense fallback={null}>
        <AssistantDrawer />
      </Suspense>
    </>
  );
}
