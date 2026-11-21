import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import type { WorkspaceUser } from "@/features/auth/session";

vi.mock("@/features/auth/session", () => ({ requireUser: vi.fn<() => Promise<WorkspaceUser>>() }));
vi.mock("@/features/workspace/workspace-provider", () => ({
  useWorkspace: () => ({ state: { assessments: {} } }),
}));
vi.mock("@/features/assessments/components/assessment-status", () => ({
  assessmentStatus: () => ({ label: "", tone: "default" }),
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
