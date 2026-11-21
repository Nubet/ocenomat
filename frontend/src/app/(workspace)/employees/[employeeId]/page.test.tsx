import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, expect, it, vi } from "vitest";
import type { WorkspaceUser } from "@/features/auth/session";
import type { EmployeePage as EmployeePageData, EmployeeRecord } from "@/features/employees/types";

vi.mock("@/features/auth/session", () => ({ requireUser: vi.fn<() => Promise<WorkspaceUser>>() }));
vi.mock("@/features/employees/server", () => ({
  getEmployee: vi.fn<() => Promise<EmployeeRecord>>(),
  getEmployeePage: vi.fn<() => Promise<EmployeePageData>>(),
}));
vi.mock("@/features/assessments/server", () => ({ getAssessments: vi.fn<() => Promise<[]>>() }));

import { requireUser } from "@/features/auth/session";
import { getEmployee, getEmployeePage } from "@/features/employees/server";
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
  vi.mocked(getEmployeePage).mockResolvedValue({
    items: [],
    total: 0,
    page: 1,
    page_size: 1,
    total_pages: 1,
  });
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
  expect(getEmployeePage).toHaveBeenCalledWith({
    assigned_only: true,
    employee_id: employee.id,
    page_size: 1,
  });
  expect(html).not.toContain("/assessments/new");
});

it("offers a new assessment for the currently assigned employee", async () => {
  vi.mocked(requireUser).mockResolvedValue({
    id: "manager",
    display_name: "Test",
    roles: ["MANAGER"],
  });
  vi.mocked(getEmployeePage).mockResolvedValue({
    items: [employee],
    total: 1,
    page: 1,
    page_size: 1,
    total_pages: 1,
  });
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
  expect(getEmployeePage).not.toHaveBeenCalled();
  expect(html).not.toContain("/assessments/new");
});

it("returns to the same directory page with search and sorting intact", async () => {
  vi.mocked(requireUser).mockResolvedValue({ id: "hr", display_name: "HR", roles: ["HR"] });
  const html = renderToStaticMarkup(
    await EmployeePage({
      params: Promise.resolve({ employeeId: employee.id }),
      searchParams: Promise.resolve({ q: "radca", sort: "name_desc", page: "3", page_size: "10" }),
    }),
  );
  expect(html).toContain("page=3");
  expect(html).toContain("q=radca#employee-results");
  expect(html).toContain("sort=name_desc");
});
