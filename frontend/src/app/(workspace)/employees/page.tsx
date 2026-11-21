import type { Metadata } from "next";
import { EmployeeList } from "@/features/employees/employee-list";
export const metadata: Metadata = { title: "Pracownicy" };
export default function EmployeesPage() {
  return <EmployeeList />;
}
