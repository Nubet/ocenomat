import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import type { WorkspaceUser } from "@/features/auth/session";
import type { Monitoring } from "@/features/monitoring/types";

vi.mock("@/features/auth/session", () => ({ requireUser: vi.fn<() => Promise<WorkspaceUser>>() }));
vi.mock("@/features/monitoring/server", () => ({
  getMonitoring: vi.fn<() => Promise<Monitoring>>().mockResolvedValue({
    as_of: "2026-11-21",
    attention_window_days: 14,
    total: 0,
    in_progress: 0,
    completed: 0,
    needs_attention: 0,
    processes: [],
    deadlines: [],
    reminders: [],
  }),
}));

import { requireUser } from "@/features/auth/session";
import HomePage from "./page";

describe("dashboard greeting", () => {
  it.each([
    { displayName: "  Anna Nowak  ", greeting: "Dzień dobry, Anna Nowak" },
    { displayName: "  ", greeting: "Dzień dobry" },
  ])("greets the signed-in user with $displayName", async ({ displayName, greeting }) => {
    vi.mocked(requireUser).mockResolvedValue({ id: "test", display_name: displayName, roles: [] });

    const html = renderToStaticMarkup(await HomePage());
    expect(html).toContain(`>${greeting}</h1>`);
    expect(html).not.toContain("✳");
  });
});
