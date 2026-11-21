import "server-only";

import { cache } from "react";
import { notFound } from "next/navigation";
import { apiRequest } from "@/lib/api/server";
import type { EmployeePage, EmployeeRecord } from "./types";
import type { EmployeeQuery } from "./query";

async function employeeRequest(path: string): Promise<Response> {
  const response = await apiRequest(path);
  if (response.status === 404 || response.status === 422) notFound();
  if (!response.ok) throw new Error("Nie można pobrać danych pracowników.");
  return response;
}

export async function getEmployeePage(
  query: Partial<EmployeeQuery> & { assigned_only?: boolean; employee_id?: string } = {},
): Promise<EmployeePage> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== "" && value !== false) params.set(key, String(value));
  }
  const response = await employeeRequest(`/api/v1/employees${params.size ? `?${params}` : ""}`);
  return response.json() as Promise<EmployeePage>;
}

// The assessment picker needs every assigned option, not just the first directory page.
export const getEmployees = cache(async (assignedOnly = false): Promise<EmployeeRecord[]> => {
  const employees: EmployeeRecord[] = [];
  let page = 1;
  let result: EmployeePage;
  do {
    result = await getEmployeePage({ assigned_only: assignedOnly, page_size: 100, page });
    employees.push(...result.items);
    page += 1;
  } while (page <= result.total_pages);
  return employees;
});

export async function getEmployee(id: string): Promise<EmployeeRecord> {
  const response = await employeeRequest(`/api/v1/employees/${encodeURIComponent(id)}`);
  return response.json() as Promise<EmployeeRecord>;
}
