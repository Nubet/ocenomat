import type { Metadata } from "next";
import {
  getAssessment,
  getAssessmentCatalog,
  getAssessmentDocuments,
} from "@/features/assessments/server";
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
  const [catalog, query, documents] = await Promise.all([
    getAssessmentCatalog(assessment.catalog_version_id),
    searchParams,
    getAssessmentDocuments(assessment.id),
  ]);
  return (
    <ArrangementForm
      key={assessment.id}
      assessment={assessment}
      catalog={catalog}
      files={documents.files}
      descriptions={documents.descriptions}
      requestedStep={typeof query.step === "string" ? query.step : undefined}
    />
  );
}
