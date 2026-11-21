import type { Metadata } from "next";
import { AssessmentList } from "@/features/assessments/assessment-list";
import { getAssessments } from "@/features/assessments/server";
import { requireUser } from "@/features/auth/session";
import { getEmployeePage } from "@/features/employees/server";
import type { AssessmentListParams } from "@/features/assessments/list-query";
export const metadata: Metadata = { title: "Oceny" };
export default async function AssessmentsPage({
  searchParams,
}: {
  searchParams: Promise<AssessmentListParams>;
}) {
  const [user, assessments, params] = await Promise.all([
    requireUser(),
    getAssessments(),
    searchParams,
  ]);
  const canCreate =
    user.roles.includes("MANAGER") &&
    (await getEmployeePage({ assigned_only: true, page_size: 1 })).total > 0;
  return (
    <AssessmentList
      assessments={assessments}
      canCreate={canCreate}
      roles={user.roles}
      params={params}
    />
  );
}
