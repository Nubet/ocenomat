"use client";

import { useActionState, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, Note } from "@/components/ui/card";
import { RadioChoice } from "@/components/ui/choice";
import type { components } from "@/lib/api/schema";
import { saveActivity } from "./activity-actions";
import { assessmentHref, type AssessmentActionState, type AssessmentRecord } from "./types";

const confirmedAtFormatter = new Intl.DateTimeFormat("pl-PL", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Europe/Warsaw",
});

export function EvaluationForm({
  assessment,
  catalog,
  visible,
  onSaved,
  onPendingChange,
}: {
  assessment: AssessmentRecord;
  catalog: components["schemas"]["CatalogResponse"];
  visible: boolean;
  onSaved: (assessment: AssessmentRecord) => void;
  onPendingChange: (pending: boolean) => void;
}) {
  const [state, action, pending] = useActionState(
    async (previous: AssessmentActionState, data: FormData) => {
      if (previous.conflict) return previous;
      onPendingChange(true);
      try {
        const result = await saveActivity(assessment.id, previous, data);
        if (result.assessment) onSaved(result.assessment);
        return result;
      } finally {
        onPendingChange(false);
      }
    },
    { error: "", conflict: false },
  );
  const selected = catalog.criteria.filter((item) =>
    assessment.criteria.some((selection) => selection.criterion_id === item.id),
  );
  const available = assessment.status === "evaluation" || assessment.status === "completed";

  return (
    <section hidden={!visible} aria-label="Ocena zachowań i decyzje przełożonego">
      <Note className="mb-5">
        {available
          ? "Propozycja oceny pomaga podjąć decyzję. Zapisz odpowiedzi, a następnie wybierz i zatwierdź ocenę każdego kryterium. Możesz wybrać inną ocenę niż proponowana. Po zmianie odpowiedzi lub notatki zatwierdź ocenę tego kryterium ponownie."
          : "Najpierw potwierdź odbytą rozmowę oceniającą. Wtedy otworzy się zapis odpowiedzi i ocen cząstkowych."}
      </Note>
      {state.message ? (
        <output className="mb-5 block text-body text-success">{state.message}</output>
      ) : null}
      {state.error ? (
        <Note className="mb-5">
          <p role="alert">{state.error}</p>
          {state.conflict ? (
            <a
              className="mt-3 inline-block font-semibold text-primary underline"
              href={`${assessmentHref(assessment.id)}?step=evaluation`}
              target="_blank"
              rel="noreferrer"
            >
              Otwórz zapisaną wersję w nowej karcie
            </a>
          ) : null}
        </Note>
      ) : null}
      {available ? (
        <>
          <p className="mb-5 text-body">
            Zatwierdzono {assessment.ratings.filter((item) => item.score !== null).length} z{" "}
            {selected.length} kryteriów. Podsumowanie wyniku i zakończenie procesu oceny są jeszcze
            w przygotowaniu.
          </p>
          <div className="space-y-5">
            {selected.map((criterion) => (
              <CriterionEvaluation
                key={criterion.id}
                criterion={criterion}
                assessment={assessment}
                action={action}
                pending={pending}
                conflict={state.conflict}
              />
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}

function CriterionEvaluation({
  criterion,
  assessment,
  action,
  pending,
  conflict,
}: {
  criterion: components["schemas"]["Criterion"];
  assessment: AssessmentRecord;
  action: (data: FormData) => void;
  pending: boolean;
  conflict: boolean;
}) {
  const rating = assessment.ratings.find((item) => item.criterion_id === criterion.id);
  const [answers, setAnswers] = useState(() =>
    Object.fromEntries(
      criterion.indicators.map((indicator) => {
        const saved = rating?.answers.find((item) => item.indicator_id === indicator.id);
        return [indicator.id, { level: saved?.level?.toString() ?? "", note: saved?.note ?? "" }];
      }),
    ),
  );
  const [score, setScore] = useState(rating?.score?.toString() ?? "");
  const dirty = criterion.indicators.some((indicator) => {
    const saved = rating?.answers.find((item) => item.indicator_id === indicator.id);
    const draft = answers[indicator.id];
    return (
      draft.level !== (saved?.level?.toString() ?? "") || draft.note.trim() !== (saved?.note ?? "")
    );
  });

  return (
    <Card className="p-6 sm:p-7">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-base font-semibold">{criterion.name}</h2>
        <Badge tone={rating?.score != null ? "success" : "primary"}>
          {rating?.score != null ? `Zatwierdzono: ${rating.score}` : "Wymaga decyzji"}
        </Badge>
      </div>
      <form action={action}>
        <input type="hidden" name="revision" value={assessment.revision} />
        <input type="hidden" name="criterion_id" value={criterion.id} />
        <fieldset disabled={pending || assessment.status !== "evaluation"}>
          <legend className="sr-only">Odpowiedzi i ocena: {criterion.name}</legend>
          <div className="space-y-6">
            {criterion.indicators.map((indicator) => (
              <fieldset key={indicator.id} className="rounded-xl border p-4">
                <legend className="px-2 text-body font-semibold">{indicator.description}</legend>
                <input type="hidden" name="indicator_id" value={indicator.id} />
                <div className="space-y-2">
                  {indicator.levels.map((level) => (
                    <RadioChoice
                      key={level.level}
                      name={`level:${indicator.id}`}
                      value={String(level.level)}
                      checked={answers[indicator.id].level === String(level.level)}
                      onChange={() => {
                        setAnswers({
                          ...answers,
                          [indicator.id]: { ...answers[indicator.id], level: String(level.level) },
                        });
                        setScore("");
                      }}
                    >
                      <strong>{level.name}</strong>
                      <span className="mt-1 block text-muted-foreground">{level.description}</span>
                    </RadioChoice>
                  ))}
                  <RadioChoice
                    name={`level:${indicator.id}`}
                    value=""
                    checked={answers[indicator.id].level === ""}
                    onChange={() => {
                      setAnswers({
                        ...answers,
                        [indicator.id]: { ...answers[indicator.id], level: "" },
                      });
                      setScore("");
                    }}
                  >
                    Brak obserwacji — pomiń w obliczeniach
                  </RadioChoice>
                </div>
                <label className="mt-4 block">
                  <span className="field-label">Notatka: {indicator.description}</span>
                  <textarea
                    className="field min-h-24"
                    name={`note:${indicator.id}`}
                    maxLength={4000}
                    value={answers[indicator.id].note}
                    onChange={(event) => {
                      setAnswers({
                        ...answers,
                        [indicator.id]: { ...answers[indicator.id], note: event.target.value },
                      });
                      setScore("");
                    }}
                  />
                </label>
              </fieldset>
            ))}
          </div>
          <Button
            className="mt-5"
            type="submit"
            name="operation"
            value="answers"
            disabled={conflict}
          >
            {pending ? "Zapisywanie…" : "Zapisz odpowiedzi"}
          </Button>
          <div className="mt-6 rounded-xl border bg-primary-muted/30 p-5">
            <h3 className="text-sm font-semibold">
              Proponowana ocena: {rating?.suggested_score ?? "brak propozycji"}
            </h3>
            <p className="mt-2 text-body text-muted-foreground">
              {dirty
                ? "Masz niezapisane odpowiedzi. Zapisz je, aby zaktualizować propozycję oceny."
                : "Propozycja opiera się na wybranych opisach zachowań. Brak obserwacji nie obniża oceny — jest pomijany w obliczeniach. Jeśli dwa poziomy są równie bliskie średniej, proponowany jest niższy."}
            </p>
            <fieldset className="mt-5">
              <legend className="mb-3 text-body font-semibold">
                Twoja ocena cząstkowa: {criterion.name}
              </legend>
              <div className="flex flex-wrap gap-2">
                {[1, 3, 5, 7, 9].map((value) => (
                  <RadioChoice
                    key={value}
                    name="score"
                    value={String(value)}
                    checked={score === String(value)}
                    onChange={() => setScore(String(value))}
                  >
                    {value}
                  </RadioChoice>
                ))}
              </div>
            </fieldset>
            <Button
              className="mt-5"
              type="submit"
              name="operation"
              value="rating"
              variant="primary"
              disabled={conflict || dirty || !score}
            >
              Zatwierdź ocenę kryterium
            </Button>
          </div>
        </fieldset>
      </form>
      {rating?.confirmed_at ? (
        <p className="mt-4 text-caption text-muted-foreground">
          Twoje zatwierdzenie: {confirmedAtFormatter.format(new Date(rating.confirmed_at))}
        </p>
      ) : null}
    </Card>
  );
}
