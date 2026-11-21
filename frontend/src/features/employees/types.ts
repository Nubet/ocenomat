import type { components } from "@/lib/api/schema";

export type EmployeeRecord = components["schemas"]["EmployeeResponse"];
export type EmployeePage = components["schemas"]["EmployeePage"];
export type EmployeeSort = components["schemas"]["EmployeeSort"];

export function employeeHref(id: string) {
  return `/employees/${encodeURIComponent(id)}`;
}
