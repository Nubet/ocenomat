"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { usePathname } from "next/navigation";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Note } from "@/components/ui/card";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import { askAssistant } from "./actions";
import { assistantSuggestions } from "./responses";
import { assessmentContext, type AssistantAnswer, type AssistantMode } from "./types";
import { CitationCard } from "./citation-card";

export function AssistantDrawer() {
  const { assistantOpen, closeAssistant } = useWorkspace();
  const pathname = usePathname();
  if (!assistantOpen) return null;
  return (
    <Dialog title="Zapytaj OcenoMat" onClose={closeAssistant} drawer="right">
      <AssistantSession key={pathname} assessmentId={assessmentContext(pathname)} />
    </Dialog>
  );
}

function AssistantSession({ assessmentId }: { assessmentId?: string }) {
  const [mode, setMode] = useState<AssistantMode>("formal");
  const [kind, setKind] = useState<"first" | "periodic">("periodic");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<{ question: string; answer: AssistantAnswer }[]>([]);
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ block: "nearest" });
  }, [messages]);

  function ask(value: string, task: "question" | "assessment_result" = "question") {
    const trimmed = value.trim();
    if (!trimmed || pending) return;
    setQuestion(trimmed);
    setError("");
    startTransition(async () => {
      const result = await askAssistant({
        question: trimmed,
        mode,
        assessment_id: assessmentId,
        assessment_kind: assessmentId ? "unspecified" : kind,
        task,
      });
      if ("error" in result) {
        setError(result.error);
        return;
      }
      setMessages((previous) => [...previous, { question: trimmed, answer: result.answer }]);
      setQuestion("");
    });
  }

  function changeMode(value: AssistantMode) {
    setMode(value);
    setMessages([]);
    setError("");
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b bg-surface-muted p-4">
        <p className="mb-3 text-caption text-subtle-foreground">
          Kontekst:{" "}
          {assessmentId
            ? "Bieżąca zapisana ocena · zakres ustala backend"
            : "Pytanie ogólne · bez danych pracownika"}
        </p>
        <fieldset
          className="flex flex-wrap gap-1 rounded-xl border p-1"
          aria-label="Tryb asystenta"
          disabled={pending}
        >
          {(
            [
              ["formal", "Pomoc formalna"],
              ["conversation", "Przygotowanie rozmowy"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              aria-pressed={mode === id}
              onClick={() => changeMode(id)}
              className={`rounded-lg px-3 py-2 text-label ${mode === id ? "bg-surface font-semibold shadow-sm" : "text-muted-foreground"}`}
            >
              {label}
            </button>
          ))}
        </fieldset>
        {!assessmentId && (
          <label className="mt-3 block text-caption">
            Zakres pytania
            <select
              className="field mt-1"
              value={kind}
              disabled={pending}
              onChange={(event) => {
                setKind(event.target.value as "first" | "periodic");
                setMessages([]);
                setError("");
              }}
            >
              <option value="periodic">Ocena okresowa</option>
              <option value="first">Pierwsza ocena</option>
            </select>
          </label>
        )}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-5" aria-busy={pending}>
        <Note className="mb-5">
          Asystent korzysta z ograniczonego, zweryfikowanego korpusu. Może odmówić odpowiedzi przy
          brakujących podstawach. Decyzje pozostają po stronie przełożonego. Rozmowa znika po
          zamknięciu panelu.
        </Note>
        <div aria-live="polite" aria-relevant="additions">
          {messages.map((message, index) => (
            <div key={index} className="mb-4">
              <p className="mb-2 text-body font-semibold">{message.question}</p>
              <div className="rounded-xl border bg-surface-muted p-4">
                <p className="mb-2 text-label font-semibold">
                  {
                    {
                      answered: "Odpowiedź",
                      insufficient_evidence: "Brak wystarczających podstaw",
                      conflicting_sources: "Nierozstrzygnięte źródła",
                    }[message.answer.status]
                  }
                </p>
                {(message.answer.claims ?? []).map((claim, claimIndex) => (
                  <div key={claimIndex} className="mb-3">
                    <p className="text-body leading-6">{claim.text}</p>
                    {claim.citations.map((citation, citationIndex) => (
                      <CitationCard key={citationIndex} citation={citation} />
                    ))}
                  </div>
                ))}
                {message.answer.result && (
                  <p className="text-body">
                    Wynik z silnika reguł:{" "}
                    {
                      { incomplete: "niekompletny", positive: "pozytywny", negative: "negatywny" }[
                        message.answer.result.outcome
                      ]
                    }
                    {message.answer.result.mean != null
                      ? ` · średnia ${message.answer.result.mean}`
                      : ""}
                    .
                  </p>
                )}
                {(message.answer.limitations ?? []).map((limitation, i) => (
                  <p key={i} className="mt-2 text-caption text-muted-foreground">
                    {limitation}
                  </p>
                ))}
              </div>
            </div>
          ))}
          {pending && (
            <output className="mb-4 block text-body">
              Wyszukuję źródła i sprawdzam poparcie odpowiedzi…
            </output>
          )}
        </div>
        {error && (
          <p role="alert" className="mb-4 text-body text-danger">
            {error}
          </p>
        )}
        <p className="eyebrow mb-3">Proponowane pytania</p>
        <div className="space-y-2">
          {assessmentId && (
            <Button
              disabled={pending}
              onClick={() => ask("Jaki jest wynik tej oceny?", "assessment_result")}
            >
              Sprawdź zapisany wynik
            </Button>
          )}
          {assistantSuggestions(mode, kind).map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              disabled={pending}
              onClick={() => ask(suggestion)}
              className="flex w-full items-center gap-2 rounded-xl border px-3 py-3 text-left text-body hover:bg-surface-muted disabled:opacity-50"
            >
              <span className="flex-1">{suggestion}</span>
              <Icon name="arrow-up-right" size={14} />
            </button>
          ))}
        </div>
        <div ref={end} />
      </div>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          ask(question);
        }}
        className="flex shrink-0 items-end gap-2 border-t p-4"
      >
        <label className="flex-1">
          <span className="sr-only">Pytanie do asystenta</span>
          <input
            className="field"
            placeholder="Zadaj pytanie…"
            value={question}
            maxLength={1000}
            disabled={pending}
            onChange={(event) => setQuestion(event.target.value)}
          />
        </label>
        <Button
          type="submit"
          variant="primary"
          aria-label="Wyślij pytanie"
          disabled={pending || !question.trim()}
        >
          <Icon name="send" size={17} />
        </Button>
      </form>
    </div>
  );
}
