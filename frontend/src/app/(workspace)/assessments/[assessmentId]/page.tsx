import type { Metadata } from "next";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Card, Note, PageHeading } from "@/components/ui/card";
import { getAssessment } from "@/features/assessments/server";
import { assessmentStatusLabels } from "@/features/assessments/types";

type Props = { params: Promise<{ assessmentId: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { assessmentId } = await params;
  const assessment = await getAssessment(assessmentId);
  return { title: `${assessment.employee_snapshot.name} — ocena C` };
}

export default async function AssessmentPage({ params }: Props) {
  const { assessmentId } = await params;
  const assessment = await getAssessment(assessmentId);
  const employee = assessment.employee_snapshot;
  return (
    <>
      <PageHeading
        eyebrow="Ocena okresowa · Arkusz C"
        title={employee.name}
        description="Zapisany proces oceny. Odświeżenie strony wczytuje ten sam zapis z API."
      />
      <Card className="p-6 sm:p-8">
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <Avatar employee={employee} size={43} />
          <div className="flex-1">
            <p className="font-semibold">{employee.position}</p>
            <p className="mt-1 text-label text-muted-foreground">{employee.department}</p>
          </div>
          <Badge tone="primary">{assessmentStatusLabels[assessment.status]}</Badge>
        </div>
        <dl className="grid gap-5 border-t pt-6 text-body sm:grid-cols-2">
          <div>
            <dt className="eyebrow mb-2">Identyfikator oceny</dt>
            <dd className="break-all">{assessment.id}</dd>
          </div>
          <div>
            <dt className="eyebrow mb-2">Rewizja zapisu</dt>
            <dd>{assessment.revision}</dd>
          </div>
          <div>
            <dt className="eyebrow mb-2">Utworzona</dt>
            <dd>
              {new Date(assessment.created_at).toLocaleString("pl-PL", {
                timeZone: "Europe/Warsaw",
                dateStyle: "medium",
                timeStyle: "short",
              })}
            </dd>
          </div>
          <div>
            <dt className="eyebrow mb-2">Wersja katalogu</dt>
            <dd className="break-all">{assessment.catalog_version_id}</dd>
          </div>
        </dl>
      </Card>
      <Note className="mt-5">
        Szkic jest zapisany w bazie wraz z migawką danych pracownika i wersją katalogu. Dobór
        kryteriów i terminów zostanie podłączony w następnym etapie wdrożenia.
      </Note>
      <ButtonLink href="/assessments" className="mt-5">
        Wróć do ocen
      </ButtonLink>
    </>
  );
}
