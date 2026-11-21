"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "@/features/auth/actions";
import type { WorkspaceUser } from "@/features/auth/session";
import { Icon } from "@/components/ui/icon";
import { Brand } from "@/components/ui/brand";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import { navigation } from "./navigation";

export function Sidebar({
  user,
  onNavigate,
  onSearch,
}: {
  user: WorkspaceUser;
  onNavigate?: () => void;
  onSearch: () => void;
}) {
  const pathname = usePathname();
  const { state, toggleTheme } = useWorkspace();
  const linkClass =
    "flex min-h-[2.5625rem] w-full items-center gap-3 rounded-[0.6875rem] border px-3 py-2.5 text-left text-[0.8125rem] font-medium transition-colors";

  return (
    <div className="flex min-h-full flex-col bg-sidebar">
      <div className="flex items-center justify-between px-5 pt-6 pb-7">
        <Link
          href="/"
          onClick={onNavigate}
          aria-label="OcenoMat — przejdź do pulpitu"
          className="flex items-center gap-3"
        >
          <Brand />
        </Link>
      </div>
      <div className="px-4 pb-6">
        <button
          onClick={onSearch}
          type="button"
          className="flex h-10 w-full items-center gap-2.5 rounded-control border bg-surface px-3 text-body text-muted-foreground"
        >
          <Icon name="search" size={16} />
          <span className="flex-1 text-left">Szukaj w OcenoMat</span>
          <kbd className="rounded-md border px-1.5 py-0.5 text-caption text-subtle-foreground">
            Ctrl K
          </kbd>
        </button>
      </div>
      <div className="px-4">
        <p className="eyebrow mx-3 mb-3 text-caption">Przestrzeń robocza</p>
        <nav aria-label="Sekcje aplikacji" className="space-y-1">
          {navigation.map(({ href, label, icon }) => {
            const active = href === "/" ? pathname === href : pathname.startsWith(href);
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
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="mt-auto px-4 pt-6 pb-4">
        <div className="border-t pt-4">
          {user.roles.includes("HR") ? (
            <Link
              href="/hr"
              onClick={onNavigate}
              className={`${linkClass} ${pathname === "/hr" ? "border-border bg-surface" : "border-transparent text-muted-foreground"}`}
            >
              <Icon name="shield" size={17} />
              <span>Widok HR</span>
              <Icon name="chevron-right" size={14} className="ml-auto" />
            </Link>
          ) : null}
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
            {user.display_name
              .split(/\s+/)
              .slice(0, 2)
              .map((part) => part[0])
              .join("")}
          </span>
          <div>
            <p className="text-label font-semibold">{user.display_name}</p>
            <p className="text-caption text-subtle-foreground">{user.roles.join(" · ")}</p>
          </div>
          <Icon name="more" size={17} className="ml-auto text-subtle-foreground" />
        </div>
        <form action={signOut} className="mt-3">
          <button
            type="submit"
            className={`${linkClass} border-transparent text-muted-foreground hover:bg-surface`}
          >
            Wyloguj się
          </button>
        </form>
      </div>
    </div>
  );
}
