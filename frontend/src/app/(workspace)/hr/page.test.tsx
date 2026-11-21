import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Monitoring } from "@/features/monitoring/types";

vi.mock("@/features/auth/session", () => ({ requireUser: vi.fn<() => Promise<WorkspaceUser>>() }));
vi.mock("@/features/hr/hr-overview", () => ({ HrOverview: () => null }));
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
vi.mock("next/navigation", () => ({
  notFound: () => {
    throw new Error("not-found");
  },
}));

import { requireUser, type WorkspaceUser } from "@/features/auth/session";
import HrPage from "./page";
import { getMonitoring } from "@/features/monitoring/server";

describe("HR route authorization", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const deniedRoles: WorkspaceUser["roles"][] = [["ADMIN"], ["MANAGER"], []];
  it.each(deniedRoles.map((roles) => ({ roles })))(
    "rejects direct access without the HR role ($roles)",
    async ({ roles }) => {
      vi.mocked(requireUser).mockResolvedValue({ id: "test", display_name: "Test", roles });
      await expect(HrPage()).rejects.toThrow("not-found");
      expect(getMonitoring).not.toHaveBeenCalled();
    },
  );

  it("allows HR", async () => {
    vi.mocked(requireUser).mockResolvedValue({ id: "test", display_name: "HR", roles: ["HR"] });
    await expect(HrPage()).resolves.toBeTruthy();
    expect(getMonitoring).toHaveBeenCalledWith("hr");
  });
});
