import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { requireUser } from "@/features/auth/session";
import { getEmployees } from "@/features/employees/server";
import { CreateAssessmentForm } from "@/features/assessments/create-form";

export const metadata: Metadata = { title: "Nowa ocena" };

export default async function NewAssessmentPage({
  searchParams,
}: {
  searchParams: Promise<{ employee_id?: string | string[] }>;
}) {
  const user = await requireUser();
  if (!user.roles.includes("MANAGER")) notFound();
  const [employees, query] = await Promise.all([getEmployees(true), searchParams]);
  const selected =
    typeof query.employee_id === "string" ? query.employee_id : (employees[0]?.id ?? "");
  if (query.employee_id && !employees.some(({ id }) => id === selected)) notFound();
  return (
    <CreateAssessmentForm
      employees={employees}
      initialEmployeeId={selected}
      requestKey={crypto.randomUUID()}
    />
  );
}
