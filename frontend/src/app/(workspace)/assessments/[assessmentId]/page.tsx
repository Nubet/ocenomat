import type { Metadata } from "next";
import {
  getAssessment,
  getAssessmentCatalog,
  getAssessmentDocuments,
} from "@/features/assessments/server";
import { ArrangementForm } from "@/features/assessments/arrangement-form";
import { FirstAssessmentForm } from "@/features/assessments/first-form";

type Props = {
  params: Promise<{ assessmentId: string }>;
  searchParams: Promise<{ step?: string | string[] }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const assessment = await getAssessment((await params).assessmentId);
  return {
    title: `${assessment.employee_snapshot.name} — ${assessment.kind === "first" ? "pierwsza ocena" : `ocena ${assessment.form}`}`,
  };
}

export default async function AssessmentPage({ params, searchParams }: Props) {
  const assessment = await getAssessment((await params).assessmentId);
  if (assessment.kind === "first") {
    const documents = await getAssessmentDocuments(assessment.id);
    return (
      <FirstAssessmentForm
        key={assessment.id}
        assessment={assessment}
        files={documents.files}
        descriptions={documents.descriptions}
      />
    );
  }
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
