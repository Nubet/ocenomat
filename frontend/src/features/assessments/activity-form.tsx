"use client";

import { useActionState, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, Note } from "@/components/ui/card";
import type { components } from "@/lib/api/schema";
import { saveActivity } from "./activity-actions";
import { ConversationForm } from "./conversation-form";
import { assessmentHref, type AssessmentRecord, type AssessmentActionState } from "./types";

const recordedAtFormatter = new Intl.DateTimeFormat("pl-PL", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Europe/Warsaw",
});

function recordedAt(value: string) {
  return recordedAtFormatter.format(new Date(value));
}

export function ActivityForm({
  assessment,
  catalog,
  step,
  onSaved,
  onPendingChange,
}: {
  assessment: AssessmentRecord;
  catalog: components["schemas"]["CatalogResponse"];
  step: string;
  onSaved: (assessment: AssessmentRecord) => void;
  onPendingChange: (pending: boolean) => void;
}) {
  const [text, setText] = useState("");
  const [criterion, setCriterion] = useState(assessment.criteria[0]?.criterion_id ?? "");
  const [observationDate, setObservationDate] = useState("");
  const [conversation, setConversation] = useState({
    agenda: assessment.conversation?.agenda ?? "",
    strengths: assessment.conversation?.strengths ?? "",
    growth: assessment.conversation?.growth ?? "",
    occurred_on: assessment.conversation?.occurred_on ?? "",
  });
  const [state, action, pending] = useActionState(
    async (previous: AssessmentActionState, data: FormData) => {
      if (previous.conflict) return previous;
      onPendingChange(true);
      try {
        const result = await saveActivity(assessment.id, previous, data);
        if (result.assessment) {
          onSaved(result.assessment);
          if (data.get("operation") === "observation") setText("");
        }
        return result;
      } finally {
        onPendingChange(false);
      }
    },
    { error: "", conflict: false },
  );
  const visible = step === "period" || step === "conversation";
  const readonly = assessment.status !== "in_progress";
  const selectedCriteria = catalog.criteria.filter((item) =>
    assessment.criteria.some((selected) => selected.criterion_id === item.id),
  );

  return (
    <section hidden={!visible} aria-label="Obserwacje i rozmowa">
      {state.message ? (
        <output className="mb-5 block text-body text-success">{state.message}</output>
      ) : null}
      {state.error ? (
        <Note className="mb-5">
          <p role="alert">{state.error}</p>
          {state.conflict ? (
            <a
              className="mt-3 inline-block font-semibold text-primary underline"
              href={`${assessmentHref(assessment.id)}?step=${step}`}
              target="_blank"
              rel="noreferrer"
            >
              Otwórz zapisaną wersję w nowej karcie
            </a>
          ) : null}
        </Note>
      ) : null}
      {assessment.status === "draft" ? (
        <Note>
          Najpierw zapisz kryteria i terminy oraz potwierdź ustalenia z rozmowy rozpoczynającej.
        </Note>
      ) : null}
      {assessment.status === "criteria_agreed" ? (
        <Card className="mb-5 p-6">
          <h2 className="text-sm font-semibold">Rozpocznij okres obserwacji</h2>
          <p className="mt-3 text-body leading-6 text-muted-foreground">
            Kryteria i terminy są potwierdzone. Otwórz kolejny etap, aby zapisywać przykłady z pracy
            i przygotować rozmowę oceniającą.
          </p>
          <form action={action} className="mt-5">
            <input type="hidden" name="revision" value={assessment.revision} />
            <Button
              type="submit"
              name="operation"
              value="start_period"
              variant="primary"
              disabled={pending || state.conflict}
            >
              {pending ? "Zapisywanie…" : "Rozpocznij okres obserwacji"}
            </Button>
          </form>
        </Card>
      ) : null}
      {assessment.status === "evaluation" || assessment.status === "completed" ? (
        <Note className="mb-5">
          Rozmowa jest potwierdzona. Obserwacje i notatki możesz przeglądać. Zatwierdzanie ocen
          cząstkowych i wyniku będzie dostępne w kolejnym etapie aplikacji.
        </Note>
      ) : null}
      <div hidden={step !== "period"} className="grid gap-4 lg:grid-cols-[1.18fr_.82fr]">
        <Card className="p-6 sm:p-7">
          <div className="mb-6 flex items-center justify-between gap-3">
            <h2 className="text-sm font-semibold">Dziennik obserwacji</h2>
            <Badge tone="primary">{assessment.observations.length} wpis(y)</Badge>
          </div>
          <div className="space-y-3">
            {assessment.observations.length === 0 ? (
              <p className="text-body text-muted-foreground">Nie dodano jeszcze obserwacji.</p>
            ) : (
              assessment.observations.map((item) => (
                <div key={item.id} className="rounded-xl border p-4">
                  <div className="mb-3 flex flex-wrap justify-between gap-2 text-caption">
                    <span className="font-semibold">
                      {
                        selectedCriteria.find((criterion) => criterion.id === item.criterion_id)
                          ?.name
                      }
                    </span>
                    <time dateTime={item.occurred_on}>{item.occurred_on}</time>
                  </div>
                  <p className="text-body leading-6 whitespace-pre-wrap text-muted-foreground">
                    {item.text}
                  </p>
                  <p className="mt-3 text-caption text-subtle-foreground">
                    Autor: Ty, przełożony prowadzący ocenę · Zapis:{" "}
                    <time dateTime={item.recorded_at}>{recordedAt(item.recorded_at)}</time>
                  </p>
                </div>
              ))
            )}
          </div>
          <form action={action} className="mt-6 border-t pt-6">
            <input type="hidden" name="revision" value={assessment.revision} />
            <fieldset disabled={pending || readonly} className="space-y-4">
              <legend className="sr-only">Nowa obserwacja</legend>
              <label className="block">
                <span className="field-label">Dodaj fakt lub przykład z pracy</span>
                <textarea
                  name="text"
                  className="field min-h-28"
                  placeholder="Sytuacja · działanie · rezultat…"
                  required
                  maxLength={10000}
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                />
              </label>
              <div className="grid gap-4 sm:grid-cols-2">
                <label>
                  <span className="field-label">Powiąż z kryterium</span>
                  <select
                    name="criterion_id"
                    className="field"
                    required
                    value={criterion}
                    onChange={(event) => setCriterion(event.target.value)}
                  >
                    <option value="" disabled>
                      Wybierz kryterium
                    </option>
                    {selectedCriteria.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span className="field-label">Data obserwowanego zdarzenia</span>
                  <input
                    type="date"
                    name="observation_date"
                    className="field"
                    required
                    min={assessment.date_talk ?? undefined}
                    value={observationDate}
                    onChange={(event) => setObservationDate(event.target.value)}
                  />
                </label>
              </div>
              <Button type="submit" name="operation" value="observation" disabled={state.conflict}>
                {pending ? "Zapisywanie…" : "Dodaj obserwację"}
              </Button>
            </fieldset>
          </form>
        </Card>
        <aside>
          <Card className="p-6">
            <p className="eyebrow mb-4">Okres oceny</p>
            <h2 className="text-lg font-semibold">Dokumentuj konkretne zachowania</h2>
            <p className="mt-3 text-body leading-6 text-muted-foreground">
              Obserwacje są opcjonalnym wsparciem. Nie zastępują rozmowy ani formalnych ocen
              cząstkowych. Wpisz datę zdarzenia, a czas zapisu odnotujemy osobno.
            </p>
            <p className="mt-5 text-label text-muted-foreground">
              Termin sporządzenia oceny: {assessment.date_assessment ?? "nie ustalono"}
            </p>
          </Card>
        </aside>
      </div>
      <div hidden={step !== "conversation"}>
        <ConversationForm
          assessment={assessment}
          draft={conversation}
          onDraftChange={setConversation}
          action={action}
          pending={pending}
          conflict={state.conflict}
          hasUnsentObservation={text.trim().length > 0}
        />
        {assessment.conversation ? (
          <p className="mt-4 text-caption text-subtle-foreground">
            Autor ostatniego zapisu: Ty, przełożony prowadzący ocenę ·{" "}
            <time dateTime={assessment.conversation.recorded_at}>
              {recordedAt(assessment.conversation.recorded_at)}
            </time>
            {assessment.conversation.confirmed_at ? (
              <>
                {" "}
                · Rozmowę potwierdzono:{" "}
                <time dateTime={assessment.conversation.confirmed_at}>
                  {recordedAt(assessment.conversation.confirmed_at)}
                </time>
              </>
            ) : null}
          </p>
        ) : null}
      </div>
    </section>
  );
}
