"use client";

import { useActionState, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, Note, PageHeading } from "@/components/ui/card";
import type { components } from "@/lib/api/schema";
import { DocumentsPanel } from "./documents-panel";
import type { AssessmentDocument, JobDescription } from "./document-types";
import { saveFirstAssessment } from "./first-actions";
import { assessmentHref, type AssessmentRecord, type AssessmentActionState } from "./types";

type FirstData = components["schemas"]["FirstData"];
type Field = readonly [keyof FirstData, string, "date" | "text" | "checkbox"];
const introduction: Field[] = [
  ["intro_on", "Data rozmowy wstępnej (w ciągu 21 dni)", "date"],
  ["report_from", "Początek terminu złożenia sprawozdania", "date"],
  ["report_to", "Koniec terminu złożenia sprawozdania", "date"],
  ["intro_confirmed", "Omówiono sposób i zakres oceny oraz rozwój zawodowy", "checkbox"],
  ["arrangements_shared", "Przekazano ocenianemu ustalenia i termin sprawozdania", "checkbox"],
];
const report: Field[] = [
  ["report_period_from", "Przepracowany okres — od", "date"],
  ["report_period_to", "Przepracowany okres — do (co najmniej 7 miesięcy)", "date"],
  ["report_submitted_on", "Data złożenia sprawozdania", "date"],
  ["report_missing", "Nie złożono sprawozdania — termin już upłynął", "checkbox"],
  ["report_tasks", "Zadania wykonywane w przepracowanym okresie", "text"],
  ["report_problems", "Problemy i sposób ich rozwiązania", "text"],
  ["report_learning", "Nowa wiedza i umiejętności", "text"],
  ["report_conclusions", "Wnioski usprawniające pracę", "text"],
  ["exam_basis", "Podstawa ustawowego zwolnienia z egzaminu (jeśli dotyczy)", "text"],
  ["conversation_on", "Data rozmowy oceniającej", "date"],
  ["conversation_notes", "Omówione zadania, problemy, wiedza, rozwój i wnioski", "text"],
  ["conversation_confirmed", "Przeprowadzono rozmowę i omówiono wymagane zagadnienia", "checkbox"],
];
const decision: Field[] = [
  ["assessed_on", "Data dokonania oceny", "date"],
  ["justification", "Uzasadnienie (obowiązkowe dla wyniku negatywnego)", "text"],
  ["development_conclusions", "Wnioski dotyczące rozwoju zawodowego", "text"],
  ["unit_head_name", "Imię i nazwisko kierującego komórką", "text"],
  ["unit_head_position", "Stanowisko kierującego komórką", "text"],
  ["unit_head_agreed", "Uzgodniono ocenę z kierującym komórką", "checkbox"],
];
const elements = [
  ["reliability", "Rzetelność"],
  ["knowledge", "Wykorzystywanie wiedzy i doskonalenie zawodowe"],
  ["organization", "Organizacja pracy i orientacja na osiąganie celów"],
  ["communication", "Komunikacja"],
  ["cooperation", "Współpraca"],
] as const;

export function FirstAssessmentForm({
  assessment: initial,
  files,
  descriptions,
}: {
  assessment: AssessmentRecord;
  files: AssessmentDocument[];
  descriptions: JobDescription[];
}) {
  const [assessment, setAssessment] = useState(initial);
  const [documentsPending, setDocumentsPending] = useState(false);
  const fields =
    assessment.status === "draft"
      ? introduction
      : assessment.status === "in_progress"
        ? report
        : decision;
  const data = assessment.first!;
  const completed = assessment.status === "completed";
  const [state, action, pending] = useActionState(
    async (previous: AssessmentActionState, form: FormData) => {
      if (previous.conflict) return previous;
      const operation = form.get("operation");
      let result: AssessmentActionState;
      if (operation === "deadlines") {
        result = await saveFirstAssessment(
          assessment.id,
          {
            revision: assessment.revision,
            reason: String(
              form.get("reason"),
            ) as components["schemas"]["FirstDeadlineUpdate"]["reason"],
            basis: String(form.get("basis")),
            circumstance_from: String(form.get("circumstance_from")),
            circumstance_to: String(form.get("circumstance_to")),
            notified_on: String(form.get("notified_on")),
            contract_end: String(form.get("contract_end")),
            report_from: String(form.get("report_from")),
            report_to: String(form.get("report_to")),
          },
          true,
        );
      } else {
        const updated = {
          ...data,
          ...Object.fromEntries(
            fields.map(([name, , type]) => [
              name,
              type === "checkbox"
                ? form.get(name) === "on"
                : form.get(name) || (type === "date" ? null : ""),
            ]),
          ),
        };
        if (assessment.status === "in_progress")
          updated.exam = (form.get("exam") || null) as FirstData["exam"];
        if (assessment.status === "evaluation")
          updated.scores = Object.fromEntries(
            elements.map(([key]) => [key, form.get(key) ? Number(form.get(key)) : null]),
          );
        result = await saveFirstAssessment(assessment.id, {
          revision: assessment.revision,
          data: updated,
          action: operation as components["schemas"]["FirstUpdate"]["action"],
        });
      }
      if (result.assessment) setAssessment(result.assessment);
      return result;
    },
    { error: "", conflict: false },
  );
  const disabled = pending || documentsPending || state.conflict || completed;
  return (
    <>
      <PageHeading
        eyebrow="Pierwsza ocena"
        title={assessment.employee_snapshot.name}
        description="Kwalifikacja → rozmowa wstępna → sprawozdanie i egzamin → ocena i wynik"
      />
      <Note>
        Podstawa kwalifikacji: {data.qualification_basis}. Zatrudnienie: {data.hired_on} –{" "}
        {data.contract_end}. Zwolnienie ze służby przygotowawczej nie jest zwolnieniem z egzaminu.
      </Note>
      {assessment.status !== "draft" ? (
        <Card className="my-6 p-6">
          <details>
            <summary className="cursor-pointer font-semibold">
              Zapisane ustalenia i wcześniejsze etapy
            </summary>
            <dl className="mt-5 space-y-4">
              {(assessment.status === "in_progress"
                ? introduction
                : [...introduction, ...report]
              ).map(([name, label, type]) => (
                <div key={name}>
                  <dt className="field-label">{label}</dt>
                  <dd className="text-body whitespace-pre-wrap">
                    {type === "checkbox" ? (data[name] ? "Tak" : "Nie") : String(data[name] || "—")}
                  </dd>
                </div>
              ))}
              <div>
                <dt className="field-label">Egzamin</dt>
                <dd>
                  {data.exam === "passed"
                    ? "Zaliczony"
                    : data.exam === "failed"
                      ? "Niezaliczony"
                      : data.exam === "not_applicable"
                        ? "Nie dotyczy — ustawowe zwolnienie"
                        : "Nie ustalono"}
                </dd>
              </div>
            </dl>
          </details>
        </Card>
      ) : null}
      {assessment.first_deadline_changes?.length ? (
        <Card className="my-6 p-6">
          <h2 className="font-semibold">Historia zmian terminów</h2>
          <ol className="mt-4 space-y-4">
            {assessment.first_deadline_changes.map((change) => (
              <li key={change.id} className="text-body">
                <p>
                  {change.basis} · zawiadomienie: {change.notified_on}
                </p>
                <p>
                  Sprawozdanie: {change.previous_report_from} – {change.previous_report_to} →{" "}
                  {change.report_from} – {change.report_to}
                </p>
                <p>
                  Umowa: {change.previous_contract_end} → {change.contract_end}
                </p>
              </li>
            ))}
          </ol>
        </Card>
      ) : null}
      {state.error ? (
        <Note>
          <p role="alert">{state.error}</p>
          <a
            className="text-primary underline"
            href={assessmentHref(assessment.id)}
            target="_blank"
            rel="noreferrer"
          >
            Otwórz zapisaną wersję
          </a>
        </Note>
      ) : null}
      {state.message ? <output className="my-4 block text-success">{state.message}</output> : null}
      <Card className="my-6 p-6">
        <h2 className="mb-5 text-lg font-semibold">
          {assessment.status === "draft"
            ? "Rozmowa wstępna"
            : assessment.status === "in_progress"
              ? "Sprawozdanie, egzamin i rozmowa"
              : "Oceny i wynik"}
        </h2>
        <form action={action} key={assessment.status}>
          <fieldset disabled={disabled} className="space-y-5">
            <legend className="sr-only">Dane bieżącego etapu</legend>
            {fields.map(([name, label, type]) => (
              <label key={name} className="block">
                {type === "checkbox" ? (
                  <span className="flex gap-3">
                    <input name={name} type="checkbox" defaultChecked={data[name] === true} />
                    {label}
                  </span>
                ) : (
                  <>
                    <span className="field-label">{label}</span>
                    {type === "text" ? (
                      <textarea
                        className="field"
                        name={name}
                        maxLength={10000}
                        defaultValue={String(data[name] ?? "")}
                      />
                    ) : (
                      <input
                        className="field"
                        name={name}
                        type="date"
                        defaultValue={String(data[name] ?? "")}
                      />
                    )}
                  </>
                )}
              </label>
            ))}
            {assessment.status === "in_progress" ? (
              <label className="block">
                <span className="field-label">Egzamin</span>
                <select className="field" name="exam" defaultValue={data.exam ?? ""}>
                  <option value="">Nie ustalono</option>
                  <option value="passed">Zaliczony</option>
                  <option value="failed">Niezaliczony</option>
                  <option value="not_applicable">Nie dotyczy — ustawowe zwolnienie</option>
                </select>
              </label>
            ) : null}
            {assessment.status === "evaluation" || completed
              ? elements.map(([key, label]) => (
                  <label key={key} className="block">
                    <span className="field-label">{label}</span>
                    <select className="field" name={key} defaultValue={data.scores?.[key] ?? ""}>
                      <option value="">Nie oceniono</option>
                      <option value="3">3 — poniżej oczekiwań</option>
                      <option value="5">5 — na poziomie oczekiwań</option>
                      <option value="7">7 — powyżej oczekiwań</option>
                    </select>
                  </label>
                ))
              : null}
            {!completed ? (
              <div className="flex flex-wrap gap-3">
                <Button type="submit" name="operation" value="save">
                  Zapisz etap
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  name="operation"
                  value={
                    assessment.status === "draft"
                      ? "confirm_introduction"
                      : assessment.status === "in_progress"
                        ? "confirm_conversation"
                        : "complete"
                  }
                >
                  {assessment.status === "draft"
                    ? "Potwierdź rozmowę wstępną"
                    : assessment.status === "in_progress"
                      ? "Potwierdź rozmowę oceniającą"
                      : "Zakończ ocenę"}
                </Button>
              </div>
            ) : null}
          </fieldset>
        </form>
        {completed ? (
          <output className="mt-5 block font-semibold">
            Wynik backendu: {assessment.result.outcome === "positive" ? "pozytywny" : "negatywny"}.
            Zakończenie nie oznacza podpisania ani doręczenia.
          </output>
        ) : null}
      </Card>
      {assessment.status === "in_progress" ? (
        <Card className="my-6 p-6">
          <details>
            <summary className="cursor-pointer font-semibold">
              Zmień terminy — udokumentowana okoliczność
            </summary>
            <form action={action} className="mt-5">
              <fieldset disabled={disabled} className="space-y-4">
                <legend className="sr-only">Zmiana terminów</legend>
                <label className="block">
                  <span className="field-label">Przyczyna</span>
                  <select className="field" name="reason">
                    <option value="justified_absence">Usprawiedliwiona nieobecność</option>
                    <option value="outside_workplace">Obowiązki poza miejscem pracy</option>
                    <option value="contract_extension">Przedłużenie umowy — art. 35 ust. 4</option>
                  </select>
                </label>
                <label className="block">
                  <span className="field-label">
                    Podstawa, wniosek pracownika i decyzja (jeśli wymagane)
                  </span>
                  <textarea className="field" name="basis" required maxLength={4000} />
                </label>
                {[
                  ["circumstance_from", "Okoliczność — od", ""],
                  ["circumstance_to", "Okoliczność — do", ""],
                  ["notified_on", "Data pisemnego zawiadomienia", ""],
                  ["contract_end", "Koniec umowy", data.contract_end],
                  ["report_from", "Nowy początek terminu sprawozdania", data.report_from],
                  ["report_to", "Nowy koniec terminu sprawozdania", data.report_to],
                ].map(([name, label, value]) => (
                  <label key={name} className="block">
                    <span className="field-label">{label}</span>
                    <input
                      className="field"
                      type="date"
                      name={name!}
                      defaultValue={value ?? ""}
                      required
                    />
                  </label>
                ))}
                <Button type="submit" name="operation" value="deadlines">
                  Zapisz zmianę terminów
                </Button>
              </fieldset>
            </form>
          </details>
        </Card>
      ) : null}
      <DocumentsPanel
        assessment={assessment}
        initialFiles={files}
        initialDescriptions={descriptions}
        visible
        showPdf
        onSaved={setAssessment}
        onPendingChange={setDocumentsPending}
      />
    </>
  );
}
