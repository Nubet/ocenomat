import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { findEmployee } from "@/features/assessments/data/employees";
import { AssessmentFlow } from "@/features/assessments/assessment-flow";
import { steps } from "@/features/assessments/model/types";

type Props = {
  params: Promise<{ employeeId: string }>;
  searchParams: Promise<{ step?: string | string[] }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { employeeId } = await params;
  return { title: findEmployee(employeeId)?.name ?? "Ocena" };
}

export default async function AssessmentPage({ params, searchParams }: Props) {
  const [{ employeeId }, query] = await Promise.all([params, searchParams]);
  const employee = findEmployee(employeeId);
  if (!employee) notFound();
  const step = steps.find((step) => step === query.step);
  return <AssessmentFlow employee={employee} requestedStep={step} />;
}
