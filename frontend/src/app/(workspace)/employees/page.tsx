import type { Metadata } from "next";
import { EmployeeList } from "@/features/employees/employee-list";
import { getEmployees } from "@/features/employees/server";
import { requireUser } from "@/features/auth/session";
export const metadata: Metadata = { title: "Pracownicy" };
export default async function EmployeesPage() {
  const [employees, user] = await Promise.all([getEmployees(), requireUser()]);
  return <EmployeeList employees={employees} roles={user.roles} />;
}
