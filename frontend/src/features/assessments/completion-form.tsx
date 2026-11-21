"use client";

import { useActionState, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { Card, Note } from "@/components/ui/card";
import type { components } from "@/lib/api/schema";
import { saveActivity } from "./activity-actions";
import { assessmentHref, type AssessmentActionState, type AssessmentRecord } from "./types";

const completedAtFormatter = new Intl.DateTimeFormat("pl-PL", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Europe/Warsaw",
});
const outcomeLabels = {
  incomplete: "Wynik niekompletny",
  positive: "Ocena pozytywna",
  negative: "Ocena negatywna",
};

export function CompletionForm({
  assessment,
  catalog,
  visible,
  evaluationDirty,
  onSaved,
  onPendingChange,
}: {
  assessment: AssessmentRecord;
  catalog: components["schemas"]["CatalogResponse"];
  visible: boolean;
  evaluationDirty: boolean;
  onSaved: (assessment: AssessmentRecord) => void;
  onPendingChange: (pending: boolean) => void;
}) {
  const [draft, setDraft] = useState({
    negative_justification: assessment.summary?.negative_justification ?? "",
    development_conclusions: assessment.summary?.development_conclusions ?? "",
  });
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
  const { result, summary } = assessment;
  const available = assessment.status === "evaluation" || assessment.status === "completed";
  const readonly = assessment.status !== "evaluation";
  const dirty = Object.entries(draft).some(
    ([name, value]) => value.trim() !== (summary?.[name as keyof typeof draft] ?? ""),
  );
  const ready =
    summary !== null &&
    result.outcome !== "incomplete" &&
    (result.outcome !== "negative" || Boolean(summary.negative_justification.trim())) &&
    !dirty &&
    !evaluationDirty;

  return (
    <section hidden={!visible} aria-label="Wynik i zakończenie oceny">
      {!available ? (
        <Note>Podsumowanie będzie dostępne po potwierdzeniu rozmowy oceniającej.</Note>
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_18rem]">
            <Card className="overflow-hidden">
              <h2 className="border-b px-6 py-5 text-sm font-semibold">
                Zatwierdzone oceny cząstkowe
              </h2>
              <div className="overflow-x-auto">
                <table className="clean-table w-full">
                  <thead>
                    <tr>
                      <th>Kryterium</th>
                      <th>Ocena</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assessment.criteria.map((selection) => {
                      const criterion = catalog.criteria.find(
                        (item) => item.id === selection.criterion_id,
                      );
                      const rating = assessment.ratings.find(
                        (item) => item.criterion_id === selection.criterion_id,
                      );
                      return (
                        <tr key={selection.criterion_id}>
                          <th scope="row" className="font-semibold">
                            {criterion?.name}
                          </th>
                          <td>{rating?.score ?? "—"}</td>
                          <td>{rating?.score != null ? "Zatwierdzona" : "Wymaga zatwierdzenia"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
            <Card className="p-6">
              <h2 className="text-caption font-semibold">Średnia zatwierdzonych ocen</h2>
              <p className="my-4 text-4xl font-semibold tabular-nums">
                {result.mean?.replace(".", ",") ?? "—"}
              </p>
              <Badge
                tone={
                  result.outcome === "incomplete"
                    ? "neutral"
                    : result.outcome === "positive"
                      ? "success"
                      : "danger"
                }
              >
                {outcomeLabels[result.outcome]}
              </Badge>
              <p className="mt-4 text-body text-muted-foreground">
                Wynik pozytywny wymaga średniej większej niż 4 i braku oceny 1. Średnia jest
                wyświetlana do dwóch miejsc; wynik ustalany jest bez wcześniejszego zaokrąglania.
              </p>
            </Card>
          </div>
          {result.outcome === "incomplete" ? (
            <Note className="mt-5">
              Zatwierdź wszystkie wybrane kryteria w zakładce „Ocena zachowań”. Sama propozycja
              oceny nie wystarcza do ustalenia wyniku.
            </Note>
          ) : null}
          {evaluationDirty ? (
            <Note className="mt-5">
              W zakładce „Ocena zachowań” masz niezapisane odpowiedzi lub wybrane oceny. Zapisz
              zmiany i zatwierdź oceny przed zakończeniem procesu.
            </Note>
          ) : null}
          {state.message ? (
            <output className="mt-5 block text-body text-success">{state.message}</output>
          ) : null}
          {state.error ? (
            <Note className="mt-5">
              <p role="alert">{state.error}</p>
              {state.conflict ? (
                <a
                  className="mt-3 inline-block font-semibold text-primary underline"
                  href={`${assessmentHref(assessment.id)}?step=summary`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Otwórz zapisaną wersję w nowej karcie
                </a>
              ) : null}
            </Note>
          ) : null}
          <Card className="mt-5 p-6 sm:p-7">
            <h2 className="mb-5 text-base font-semibold">Podsumowanie oceny</h2>
            <form action={action}>
              <input type="hidden" name="revision" value={assessment.revision} />
              <fieldset disabled={pending || readonly}>
                <legend className="sr-only">Uzasadnienie i wnioski rozwojowe</legend>
                <div className="space-y-5">
                  <label className="block">
                    <span className="field-label">
                      Uzasadnienie wyniku negatywnego
                      {result.outcome === "negative"
                        ? " — wymagane przed zakończeniem"
                        : " — jeśli dotyczy"}
                    </span>
                    <textarea
                      className="field min-h-32"
                      name="negative_justification"
                      aria-required={result.outcome === "negative"}
                      maxLength={10000}
                      value={draft.negative_justification}
                      onChange={(event) =>
                        setDraft({ ...draft, negative_justification: event.target.value })
                      }
                    />
                  </label>
                  <label className="block">
                    <span className="field-label">Wnioski rozwojowe</span>
                    <textarea
                      className="field min-h-32"
                      name="development_conclusions"
                      maxLength={10000}
                      value={draft.development_conclusions}
                      onChange={(event) =>
                        setDraft({ ...draft, development_conclusions: event.target.value })
                      }
                    />
                  </label>
                </div>
                <p className="mt-3 text-body text-muted-foreground">
                  Wnioski rozwojowe są opcjonalne. Możesz zapisać szkic i wrócić do niego później.
                </p>
                <Button
                  className="mt-5"
                  type="submit"
                  name="operation"
                  value="summary"
                  disabled={state.conflict}
                >
                  {pending ? "Zapisywanie…" : "Zapisz podsumowanie"}
                </Button>
                <div className="mt-6 border-t pt-5">
                  {!readonly && (!summary || dirty) ? (
                    <p className="mb-4 text-body text-muted-foreground">
                      Przed zakończeniem zapisz podsumowanie, nawet jeśli wnioski rozwojowe
                      pozostają puste.
                    </p>
                  ) : null}
                  {!readonly &&
                  result.outcome === "negative" &&
                  !draft.negative_justification.trim() ? (
                    <p className="mb-4 text-body text-muted-foreground">
                      Uzupełnij i zapisz uzasadnienie wyniku negatywnego.
                    </p>
                  ) : null}
                  <p className="mb-4 text-body">
                    Zakończenie zamknie edycję całej oceny. Nie oznacza podpisania ani doręczenia
                    dokumentu. PDF przygotujesz w zakładce „Dokumenty i PDF” po zakończeniu oceny.
                  </p>
                  <Button
                    className="mt-5"
                    type="submit"
                    name="operation"
                    value="complete"
                    variant="primary"
                    disabled={!ready || state.conflict}
                  >
                    Zakończ ocenę
                  </Button>
                </div>
              </fieldset>
            </form>
            {summary?.completed_at ? (
              <div className="mt-5 space-y-4">
                <p className="mt-5 text-body text-success">
                  Ocena zakończona: {completedAtFormatter.format(new Date(summary.completed_at))}.
                  Dane są tylko do odczytu.
                </p>
                <ButtonLink href={`${assessmentHref(assessment.id)}?step=documents`}>
                  Przygotuj lub pobierz arkusz {assessment.form}
                </ButtonLink>
              </div>
            ) : null}
          </Card>
        </>
      )}
    </section>
  );
}
