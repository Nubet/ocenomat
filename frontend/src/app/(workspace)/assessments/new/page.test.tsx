import { beforeEach, describe, expect, it, vi } from "vitest";
import type { WorkspaceUser } from "@/features/auth/session";
import type { EmployeeRecord } from "@/features/employees/types";

vi.mock("@/features/auth/session", () => ({ requireUser: vi.fn<() => Promise<WorkspaceUser>>() }));
vi.mock("@/features/employees/server", () => ({
  getEmployees: vi.fn<() => Promise<EmployeeRecord[]>>(),
}));
vi.mock("@/features/assessments/create-form", () => ({ CreateAssessmentForm: () => null }));
vi.mock("next/navigation", () => ({
  notFound: () => {
    throw new Error("not-found");
  },
}));

import { requireUser } from "@/features/auth/session";
import { getEmployees } from "@/features/employees/server";
import NewAssessmentPage from "./page";

describe("new assessment route", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(requireUser).mockResolvedValue({
      id: "manager",
      display_name: "Test",
      roles: ["MANAGER", "HR"],
    });
    vi.mocked(getEmployees).mockResolvedValue([
      {
        id: "assigned",
        name: "Test employee",
        department: "Test",
        position: "Test",
        position_kind: "OTHER",
      },
    ]);
  });

  const forbidden: WorkspaceUser["roles"][] = [["ADMIN"], ["HR"]];
  it.each(forbidden.map((roles) => ({ roles })))(
    "rejects direct creation-page access for $roles",
    async ({ roles }) => {
      vi.mocked(requireUser).mockResolvedValue({ id: "test", display_name: "Test", roles });
      await expect(NewAssessmentPage({ searchParams: Promise.resolve({}) })).rejects.toThrow(
        "not-found",
      );
      expect(getEmployees).not.toHaveBeenCalled();
    },
  );

  it("requests only assigned choices even when a manager also has HR access", async () => {
    await NewAssessmentPage({ searchParams: Promise.resolve({}) });
    expect(getEmployees).toHaveBeenCalledWith(true);
  });

  it("does not silently replace a requested unassigned employee", async () => {
    await expect(
      NewAssessmentPage({ searchParams: Promise.resolve({ employee_id: "unassigned" }) }),
    ).rejects.toThrow("not-found");
  });
});
