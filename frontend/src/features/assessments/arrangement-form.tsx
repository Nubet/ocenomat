"use client";

import { useActionState, useState } from "react";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { Card, Note, PageHeading } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import type { components } from "@/lib/api/schema";
import { saveArrangements } from "./actions";
import { ActivityForm } from "./activity-form";
import { EvaluationForm } from "./evaluation-form";
import { CompletionForm } from "./completion-form";
import { DocumentsPanel } from "./documents-panel";
import { OspAnalysisPanel } from "./osp-analysis-panel";
import type { AssessmentDocument, JobDescription } from "./document-types";
import {
  assessmentHref,
  assessmentStatusLabels,
  type AssessmentRecord,
  type AssessmentActionState,
} from "./types";

const steps = [
  "analysis",
  "criteria",
  "timing",
  "period",
  "conversation",
  "evaluation",
  "summary",
  "documents",
] as const;
const labels = [
  "Stanowisko i kontekst",
  "Kryteria",
  "Terminy i rozmowa",
  "Obserwacje",
  "Rozmowa oceniająca",
  "Ocena zachowań",
  "Wynik i zakończenie",
  "Dokumenty i PDF",
];
const confirmations = [
  ["duties_discussed", "Omówiono obowiązki wynikające z opisu stanowiska"],
  ["expectations_discussed", "Przedstawiono kryteria i oczekiwania"],
  ["arrangements_shared", "Przekazano pracownikowi termin oceny i ustalenia"],
] as const;

export function ArrangementForm({
  assessment,
  catalog,
  requestedStep,
  files = [],
  descriptions = [],
}: {
  assessment: AssessmentRecord;
  catalog: components["schemas"]["CatalogResponse"];
  requestedStep?: string;
  files?: AssessmentDocument[];
  descriptions?: JobDescription[];
}) {
  const [current, setCurrent] = useState(assessment);
  const [step, setStep] = useState(
    steps.find((value) => value === requestedStep) ??
      (assessment.status === "draft"
        ? "analysis"
        : assessment.status === "completed"
          ? "summary"
          : assessment.status === "evaluation"
            ? "evaluation"
            : "period"),
  );
  const [activityPending, setActivityPending] = useState(false);
  const [evaluationDirty, setEvaluationDirty] = useState(false);
  const [additional, setAdditional] = useState(
    assessment.criteria.filter((item) => !item.required).map((item) => item.criterion_id),
  );
  const [reasons, setReasons] = useState<Record<string, string>>(
    Object.fromEntries(
      assessment.criteria
        .filter((item) => !item.required)
        .map((item) => [item.criterion_id, item.justification ?? ""]),
    ),
  );
  const [dates, setDates] = useState({
    date_talk: assessment.date_talk ?? "",
    date_assessment: assessment.date_assessment ?? "",
    duties_discussed: assessment.duties_discussed,
    expectations_discussed: assessment.expectations_discussed,
    arrangements_shared: assessment.arrangements_shared,
  });
  const [state, action, pending] = useActionState(
    async (previous: AssessmentActionState, data: FormData) => {
      if (previous.conflict) return previous;
      const result = await saveArrangements(assessment.id, previous, data);
      if (result.assessment) {
        setCurrent(result.assessment);
        if (data.get("operation") === "criteria") setStep("timing");
        if (data.get("operation") === "agree") setStep("period");
      }
      return result;
    },
    { error: "", conflict: false },
  );
  const readonly = current.status !== "draft";
  const employee = current.employee_snapshot;
  const required = new Set(current.required_criterion_ids);
  const dirtyDates = Object.entries(dates).some(
    ([name, value]) => value !== (current[name as keyof typeof dates] ?? ""),
  );
  const savedExtras = current.criteria.filter((item) => !item.required);
  const dirtyCriteria =
    additional.length !== savedExtras.length ||
    savedExtras.some(
      (item) =>
        !additional.includes(item.criterion_id) ||
        reasons[item.criterion_id]?.trim() !== item.justification,
    );
  const ready =
    current.criteria.length >= 5 &&
    dates.date_talk &&
    dates.date_assessment &&
    confirmations.every(([name]) => dates[name]) &&
    !dirtyDates &&
    !dirtyCriteria;

  return (
    <>
      <PageHeading
        eyebrow="Ocena okresowa · Arkusz C"
        title={employee.name}
        description="Zapisuj ustalenia, konkretne obserwacje i notatki z rozmowy. Możesz wrócić do zapisanej oceny później."
      />
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <Avatar employee={employee} size={40} />
        <p className="flex-1 text-body">
          {employee.position} · {employee.department}
        </p>
        <Badge tone={readonly ? "success" : "primary"}>
          {assessmentStatusLabels[current.status]}
        </Badge>
      </div>
      {readonly ? (
        <Note className="mb-5">
          {current.status === "completed"
            ? "Ocena została zakończona. Wszystkie zapisane dane są tylko do odczytu."
            : "Ustalenia zostały potwierdzone. Możesz je przeglądać, ale nie zmienisz już kryteriów ani terminów na tym etapie. Obserwacje i notatki znajdziesz w kolejnych zakładkach."}
        </Note>
      ) : null}
      <nav aria-label="Etapy oceny" className="mb-6 flex flex-wrap gap-2">
        {steps.map((value, index) => (
          <Button
            key={value}
            variant={step === value ? "primary" : "secondary"}
            aria-current={step === value ? "step" : undefined}
            onClick={() => setStep(value)}
            disabled={pending || activityPending}
          >
            {index + 1}. {labels[index]}
          </Button>
        ))}
      </nav>
      {state.message ? (
        <output className="mb-5 block text-body text-success">{state.message}</output>
      ) : null}
      {state.error ? (
        <Note className="mb-5">
          <p role="alert">{state.error}</p>
          {state.conflict ? (
            <a
              className="mt-3 inline-block font-semibold text-primary underline"
              href={assessmentHref(assessment.id)}
              target="_blank"
              rel="noreferrer"
            >
              Otwórz zapisaną wersję w nowej karcie
            </a>
          ) : null}
        </Note>
      ) : null}
      <form action={action}>
        <input type="hidden" name="revision" value={current.revision} />
        <fieldset disabled={pending || readonly}>
          <legend className="sr-only">Ustalenia oceny</legend>
          {step === "analysis" ? (
            <Card className="p-6 sm:p-8">
              <p className="eyebrow">Profil stanowiska</p>
              <h2 className="mt-4 text-lg font-semibold">{employee.position}</h2>
              <p className="mt-3 text-body text-muted-foreground">{employee.department}</p>
              <Note className="mt-6">
                Przed wyborem dodatkowych kryteriów sprawdź aktualny opis stanowiska pracy (OSP).
                Wybierz tylko kryteria związane z obowiązkami tej osoby i krótko wyjaśnij swój
                wybór.
              </Note>
              <p className="mt-5 text-body leading-6 text-muted-foreground">
                Poniżej dodasz OSP lub wybierzesz jego zapisaną wersję. Analiza może zaproponować
                dodatkowe kryteria z cytatami. Wybór i uzasadnienie zapisujesz samodzielnie.
              </p>
              <OspAnalysisPanel
                key={`${current.id}:${current.job_description_id}:${current.revision}`}
                assessmentId={current.id}
                jobDescriptionId={current.job_description_id ?? null}
                revision={current.revision}
              />
              <Button className="mt-6" variant="primary" onClick={() => setStep("criteria")}>
                Wybierz kryteria <Icon name="chevron-right" size={15} />
              </Button>
            </Card>
          ) : null}
          {step === "criteria" ? (
            <>
              <div className="grid gap-4 lg:grid-cols-[.93fr_1.07fr]">
                <Card className="p-6">
                  <div className="mb-4 flex justify-between gap-3">
                    <h2 className="text-sm font-semibold">Kryteria obowiązkowe</h2>
                    <Badge tone="success">5 wymaganych</Badge>
                  </div>
                  {catalog.criteria
                    .filter((item) => required.has(item.id))
                    .map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center gap-3 border-b py-4 last:border-0"
                      >
                        <Icon name="lock" size={15} className="shrink-0 text-success" />
                        <span className="text-body">{item.name}</span>
                      </div>
                    ))}
                </Card>
                <Card className="p-6">
                  <div className="mb-3 flex justify-between gap-3">
                    <h2 className="text-sm font-semibold">Kryteria dodatkowe</h2>
                    <Badge tone="primary">{additional.length} / 3</Badge>
                  </div>
                  <p className="mb-5 text-body text-muted-foreground">
                    Możesz wybrać od zera do trzech. Każdy wybór uzasadnij obowiązkami z opisu
                    stanowiska.
                  </p>
                  <div className="space-y-3">
                    {catalog.criteria
                      .filter((item) => !required.has(item.id))
                      .map((item) => (
                        <div
                          key={item.id}
                          className={`rounded-xl border p-4 ${additional.includes(item.id) ? "border-primary bg-primary-muted" : "bg-surface"}`}
                        >
                          <label className="flex items-start gap-3 text-body">
                            <input
                              type="checkbox"
                              name="additional"
                              value={item.id}
                              checked={additional.includes(item.id)}
                              disabled={!additional.includes(item.id) && additional.length >= 3}
                              onChange={(event) =>
                                setAdditional(
                                  event.target.checked
                                    ? [...additional, item.id]
                                    : additional.filter((id) => id !== item.id),
                                )
                              }
                              className="mt-1 size-4 shrink-0"
                            />
                            <span>{item.name}</span>
                          </label>
                          {additional.includes(item.id) ? (
                            <label className="mt-4 block">
                              <span className="field-label">
                                Dlaczego to kryterium jest ważne na tym stanowisku?
                              </span>
                              <textarea
                                className="field min-h-24"
                                name={`reason:${item.id}`}
                                required
                                maxLength={4000}
                                value={reasons[item.id] ?? ""}
                                onChange={(event) =>
                                  setReasons({ ...reasons, [item.id]: event.target.value })
                                }
                              />
                            </label>
                          ) : null}
                        </div>
                      ))}
                  </div>
                </Card>
              </div>
              <div className="mt-6 flex justify-between gap-3">
                <Button onClick={() => setStep("analysis")}>Wstecz</Button>
                <Button
                  type="submit"
                  name="operation"
                  value="criteria"
                  variant="primary"
                  disabled={state.conflict}
                >
                  {pending ? "Zapisywanie…" : "Zapisz kryteria i przejdź do terminów"}
                </Button>
              </div>
            </>
          ) : null}
          {step === "timing" ? (
            <>
              <div className="grid gap-4 lg:grid-cols-2">
                <Card className="p-6">
                  <h2 className="mb-6 text-sm font-semibold">Terminy oceny</h2>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <label>
                      <span className="field-label">Rozmowa rozpoczynająca</span>
                      <input
                        type="date"
                        name="date_talk"
                        className="field"
                        required
                        value={dates.date_talk}
                        onChange={(event) => setDates({ ...dates, date_talk: event.target.value })}
                      />
                    </label>
                    <label>
                      <span className="field-label">Termin sporządzenia oceny</span>
                      <input
                        type="date"
                        name="date_assessment"
                        className="field"
                        required
                        min={dates.date_talk}
                        value={dates.date_assessment}
                        onChange={(event) =>
                          setDates({ ...dates, date_assessment: event.target.value })
                        }
                      />
                    </label>
                  </div>
                  <Note className="mt-6">
                    Wpisz daty właściwe dla tego pracownika. Jeśli masz wątpliwości co do terminu,
                    ustal go z HR przed potwierdzeniem ustaleń.
                  </Note>
                </Card>
                <Card className="p-6">
                  <h2 className="mb-3 text-sm font-semibold">Czynności z rozmowy</h2>
                  <p className="mb-6 text-body text-muted-foreground">
                    Zaznacz tylko to, co już zostało wykonane. Możesz zapisać terminy i uzupełnić
                    potwierdzenia później.
                  </p>
                  <div className="space-y-5">
                    {confirmations.map(([name, label]) => (
                      <label key={name} className="flex items-start gap-3 text-body">
                        <input
                          type="checkbox"
                          name={name}
                          checked={dates[name]}
                          onChange={(event) => setDates({ ...dates, [name]: event.target.checked })}
                          className="mt-1 size-4 shrink-0"
                        />
                        <span>{label}</span>
                      </label>
                    ))}
                  </div>
                </Card>
              </div>
              <div className="mt-6 flex flex-wrap justify-between gap-3">
                <Button onClick={() => setStep("criteria")}>Wróć do kryteriów</Button>
                <div className="flex flex-wrap gap-2">
                  <Button type="submit" name="operation" value="dates" disabled={state.conflict}>
                    {pending ? "Zapisywanie…" : "Zapisz terminy i czynności"}
                  </Button>
                  <Button
                    type="submit"
                    name="operation"
                    value="agree"
                    variant="primary"
                    disabled={!ready || state.conflict}
                  >
                    Potwierdź ustalenia
                  </Button>
                </div>
              </div>
              {!readonly ? (
                <p className="mt-4 text-body text-muted-foreground">
                  Aby potwierdzić ustalenia, zapisz kryteria, daty i wszystkie trzy wykonane
                  czynności. Po potwierdzeniu nie zmienisz ich na tym etapie. Ten zapis nie
                  zastępuje podpisu ani doręczenia dokumentu.
                </p>
              ) : null}
            </>
          ) : null}
        </fieldset>
      </form>
      <DocumentsPanel
        assessment={current}
        initialFiles={files}
        initialDescriptions={descriptions}
        visible={step === "analysis" || step === "documents"}
        showPdf={step === "documents"}
        onSaved={setCurrent}
        onPendingChange={setActivityPending}
      />
      <ActivityForm
        assessment={current}
        catalog={catalog}
        step={step}
        onSaved={setCurrent}
        onPendingChange={setActivityPending}
      />
      <CompletionForm
        assessment={current}
        catalog={catalog}
        visible={step === "summary"}
        evaluationDirty={evaluationDirty}
        onSaved={setCurrent}
        onPendingChange={setActivityPending}
      />
      <EvaluationForm
        assessment={current}
        catalog={catalog}
        visible={step === "evaluation"}
        onSaved={setCurrent}
        onPendingChange={setActivityPending}
        onDirtyChange={setEvaluationDirty}
      />
      <div className="mt-6 flex flex-wrap justify-between gap-3">
        <ButtonLink href="/assessments">Wróć do ocen</ButtonLink>
        <p className="text-caption text-subtle-foreground">
          Wersja zapisu: {current.revision} · Katalog: {catalog.version}
        </p>
      </div>
    </>
  );
}
