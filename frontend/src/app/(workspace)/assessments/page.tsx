import type { Metadata } from "next";
import { AssessmentList } from "@/features/assessments/assessment-list";
export const metadata: Metadata = { title: "Oceny" };
export default function AssessmentsPage() {
  return <AssessmentList />;
}
