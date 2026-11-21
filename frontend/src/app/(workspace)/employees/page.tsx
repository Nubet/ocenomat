import type { Metadata } from "next";
import { EmployeeList } from "@/features/employees/employee-list";
import { getEmployeePage } from "@/features/employees/server";
import { parseEmployeeQuery } from "@/features/employees/query";
import { requireUser } from "@/features/auth/session";
export const metadata: Metadata = { title: "Pracownicy" };
export default async function EmployeesPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = parseEmployeeQuery(await searchParams);
  const [result, user] = await Promise.all([getEmployeePage(query), requireUser()]);
  return <EmployeeList result={result} query={query} roles={user.roles} />;
}
