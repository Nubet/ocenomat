import type { Metadata } from "next";
import { EmployeeList } from "@/features/employees/employee-list";
import { getEmployees } from "@/features/employees/server";
export const metadata: Metadata = { title: "Pracownicy" };
export default async function EmployeesPage() {
  return <EmployeeList employees={await getEmployees()} />;
}
