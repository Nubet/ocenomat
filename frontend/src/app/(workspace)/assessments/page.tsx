import type { Metadata } from "next";
import { AssessmentList } from "@/features/assessments/assessment-list";
import { getAssessments } from "@/features/assessments/server";
import { requireUser } from "@/features/auth/session";
export const metadata: Metadata = { title: "Oceny" };
export default async function AssessmentsPage() {
  const [user, assessments] = await Promise.all([requireUser(), getAssessments()]);
  return <AssessmentList assessments={assessments} canCreate={user.roles.includes("MANAGER")} />;
}
