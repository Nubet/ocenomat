import "server-only";

import { cache } from "react";
import { notFound } from "next/navigation";
import { apiRequest } from "@/lib/api/server";
import type { EmployeeRecord } from "./types";

async function employeeRequest(path: string): Promise<Response> {
  const response = await apiRequest(path);
  if (response.status === 404 || response.status === 422) notFound();
  if (!response.ok) throw new Error("Nie można pobrać danych pracowników.");
  return response;
}

export const getEmployees = cache(async (assignedOnly = false): Promise<EmployeeRecord[]> => {
  const response = await employeeRequest(
    `/api/v1/employees${assignedOnly ? "?assigned_only=true" : ""}`,
  );
  return response.json() as Promise<EmployeeRecord[]>;
});

export async function getEmployee(id: string): Promise<EmployeeRecord> {
  const response = await employeeRequest(`/api/v1/employees/${encodeURIComponent(id)}`);
  return response.json() as Promise<EmployeeRecord>;
}
