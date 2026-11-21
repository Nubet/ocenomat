import type { Metadata } from "next";
import { getAssessment, getAssessmentCatalog } from "@/features/assessments/server";
import { ArrangementForm } from "@/features/assessments/arrangement-form";

type Props = {
  params: Promise<{ assessmentId: string }>;
  searchParams: Promise<{ step?: string | string[] }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const assessment = await getAssessment((await params).assessmentId);
  return { title: `${assessment.employee_snapshot.name} — ocena C` };
}

export default async function AssessmentPage({ params, searchParams }: Props) {
  const assessment = await getAssessment((await params).assessmentId);
  const [catalog, query] = await Promise.all([
    getAssessmentCatalog(assessment.catalog_version_id),
    searchParams,
  ]);
  return (
    <ArrangementForm
      key={assessment.id}
      assessment={assessment}
      catalog={catalog}
      requestedStep={typeof query.step === "string" ? query.step : undefined}
    />
  );
}
