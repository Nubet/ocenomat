import type { components } from "@/lib/api/schema";

export type EmployeeRecord = components["schemas"]["EmployeeResponse"];

export function employeeHref(id: string) {
  return `/employees/${encodeURIComponent(id)}`;
}
