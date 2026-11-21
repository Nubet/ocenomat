import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/features/auth/session", () => ({ requireUser: vi.fn<() => Promise<WorkspaceUser>>() }));
vi.mock("@/features/hr/hr-overview", () => ({ HrOverview: () => null }));
vi.mock("next/navigation", () => ({
  notFound: () => {
    throw new Error("not-found");
  },
}));

import { requireUser, type WorkspaceUser } from "@/features/auth/session";
import HrPage from "./page";

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
    },
  );

  it("allows HR", async () => {
    vi.mocked(requireUser).mockResolvedValue({ id: "test", display_name: "HR", roles: ["HR"] });
    await expect(HrPage()).resolves.toBeTruthy();
  });
});
