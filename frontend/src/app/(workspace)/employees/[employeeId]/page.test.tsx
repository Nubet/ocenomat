import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, expect, it, vi } from "vitest";
import type { WorkspaceUser } from "@/features/auth/session";
import type { EmployeeRecord } from "@/features/employees/types";

vi.mock("@/features/auth/session", () => ({ requireUser: vi.fn<() => Promise<WorkspaceUser>>() }));
vi.mock("@/features/employees/server", () => ({
  getEmployee: vi.fn<() => Promise<EmployeeRecord>>(),
  getEmployees: vi.fn<() => Promise<EmployeeRecord[]>>(),
}));
vi.mock("@/features/assessments/server", () => ({ getAssessments: vi.fn<() => Promise<[]>>() }));

import { requireUser } from "@/features/auth/session";
import { getEmployee, getEmployees } from "@/features/employees/server";
import { getAssessments } from "@/features/assessments/server";
import EmployeePage from "./page";

const employee: EmployeeRecord = {
  id: "employee",
  name: "Test Anna",
  position: "Radca",
  position_kind: "OTHER",
  department: "Test",
};
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEmployee).mockResolvedValue(employee);
  vi.mocked(getEmployees).mockResolvedValue([]);
  vi.mocked(getAssessments).mockResolvedValue([]);
});

it("does not offer creation for an unassigned profile visible through an admin role", async () => {
  vi.mocked(requireUser).mockResolvedValue({
    id: "mixed",
    display_name: "Test",
    roles: ["MANAGER", "ADMIN"],
  });
  const html = renderToStaticMarkup(
    await EmployeePage({ params: Promise.resolve({ employeeId: employee.id }) }),
  );
  expect(getEmployees).toHaveBeenCalledWith(true);
  expect(html).not.toContain("/assessments/new");
});

it("offers a new assessment for the currently assigned employee", async () => {
  vi.mocked(requireUser).mockResolvedValue({
    id: "manager",
    display_name: "Test",
    roles: ["MANAGER"],
  });
  vi.mocked(getEmployees).mockResolvedValue([employee]);
  const html = renderToStaticMarkup(
    await EmployeePage({ params: Promise.resolve({ employeeId: employee.id }) }),
  );
  expect(html).toContain("/assessments/new?employee_id=employee");
});

it.each(["HR", "ADMIN"] as const)("does not offer creation with only %s", async (role) => {
  vi.mocked(requireUser).mockResolvedValue({ id: "user", display_name: "Test", roles: [role] });
  const html = renderToStaticMarkup(
    await EmployeePage({ params: Promise.resolve({ employeeId: employee.id }) }),
  );
  expect(getEmployees).not.toHaveBeenCalled();
  expect(html).not.toContain("/assessments/new");
});
