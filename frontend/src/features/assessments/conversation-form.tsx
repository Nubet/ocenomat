"use client";

import { useState, type Dispatch, type SetStateAction } from "react";
import { Button } from "@/components/ui/button";
import { Card, Note } from "@/components/ui/card";
import type { AssessmentRecord } from "./types";

export type ConversationDraft = {
  agenda: string;
  strengths: string;
  growth: string;
  occurred_on: string;
};

const fields = [
  [
    "agenda",
    "Agenda spotkania",
    "Rozpocznij od celu spotkania. Omów konkretne przykłady i zapisz wspólne ustalenia.",
  ],
  [
    "strengths",
    "Mocne strony",
    "Nazwij działania, które warto kontynuować, i ich wpływ na pracę zespołu.",
  ],
  [
    "growth",
    "Obszary rozwoju",
    "Opisz zachowanie, wysłuchaj perspektywy pracownika i ustal możliwy następny krok.",
  ],
] as const;

export function ConversationForm({
  assessment,
  draft,
  onDraftChange,
  action,
  pending,
  conflict,
  hasUnsentObservation,
}: {
  assessment: AssessmentRecord;
  draft: ConversationDraft;
  onDraftChange: Dispatch<SetStateAction<ConversationDraft>>;
  action: (data: FormData) => void;
  pending: boolean;
  conflict: boolean;
  hasUnsentObservation: boolean;
}) {
  const [selectedTab, setSelectedTab] = useState(0);
  const dirty = Object.entries(draft).some(
    ([key, value]) =>
      value.trim() !== (assessment.conversation?.[key as keyof ConversationDraft] ?? ""),
  );
  return (
    <>
      <Card className="overflow-hidden">
        <div
          className="flex flex-wrap gap-1 border-b p-4"
          role="tablist"
          aria-label="Materiały do rozmowy"
        >
          {fields.map(([key, label], index) => (
            <button
              key={key}
              type="button"
              id={`conversation-tab-${key}`}
              role="tab"
              aria-selected={selectedTab === index}
              aria-controls={`conversation-panel-${key}`}
              tabIndex={selectedTab === index ? 0 : -1}
              disabled={pending}
              onClick={() => setSelectedTab(index)}
              onKeyDown={(event) => {
                let next = selectedTab;
                if (event.key === "ArrowRight") next = (selectedTab + 1) % fields.length;
                else if (event.key === "ArrowLeft")
                  next = (selectedTab + fields.length - 1) % fields.length;
                else if (event.key === "Home") next = 0;
                else if (event.key === "End") next = fields.length - 1;
                else return;
                event.preventDefault();
                setSelectedTab(next);
                document.getElementById(`conversation-tab-${fields[next][0]}`)?.focus();
              }}
              className={`rounded-lg px-3 py-2 text-label ${selectedTab === index ? "bg-primary-muted font-semibold text-primary" : "text-muted-foreground"}`}
            >
              {label}
            </button>
          ))}
        </div>
        <form action={action} className="p-6 sm:p-7">
          <input type="hidden" name="revision" value={assessment.revision} />
          <fieldset disabled={pending || assessment.status !== "in_progress"}>
            <legend className="sr-only">Notatki z rozmowy oceniającej</legend>
            {fields.map(([key, label, prompt], index) => (
              <div
                key={key}
                hidden={selectedTab !== index}
                role="tabpanel"
                id={`conversation-panel-${key}`}
                aria-labelledby={`conversation-tab-${key}`}
              >
                <label className="block">
                  <span className="field-label">{label} · notatki do edycji</span>
                  <textarea
                    name={key}
                    className="field min-h-64"
                    maxLength={10000}
                    value={draft[key]}
                    onChange={(event) => onDraftChange({ ...draft, [key]: event.target.value })}
                  />
                </label>
                <p className="mt-3 text-body text-muted-foreground">{prompt}</p>
              </div>
            ))}
            <label className="mt-6 block max-w-sm">
              <span className="field-label">Data odbytej rozmowy oceniającej</span>
              <input
                type="date"
                name="conversation_date"
                className="field"
                min={assessment.date_talk ?? undefined}
                value={draft.occurred_on}
                onChange={(event) => onDraftChange({ ...draft, occurred_on: event.target.value })}
              />
            </label>
            <p className="mt-3 text-body leading-6 text-muted-foreground">
              Możesz zapisać szkic bez daty. Datę wpisz po rozmowie. Najpierw zapisz notatki i datę,
              potem potwierdź, że rozmowa się odbyła. Potwierdzenie zamknie edycję obserwacji i
              rozmowy; nie zastępuje podpisu ani doręczenia.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button type="submit" name="operation" value="conversation" disabled={conflict}>
                {pending ? "Zapisywanie…" : "Zapisz notatki i datę"}
              </Button>
              <Button
                type="submit"
                name="operation"
                value="confirm_conversation"
                variant="primary"
                disabled={
                  conflict || dirty || !assessment.conversation?.occurred_on || hasUnsentObservation
                }
              >
                Potwierdź odbytą rozmowę
              </Button>
            </div>
          </fieldset>
        </form>
      </Card>
      {hasUnsentObservation ? (
        <Note className="mt-5">
          Masz niewysłaną obserwację w dzienniku. Zapisz ją lub wyczyść przed potwierdzeniem
          rozmowy.
        </Note>
      ) : null}
    </>
  );
}
