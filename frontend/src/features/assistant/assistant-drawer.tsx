"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Note } from "@/components/ui/card";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import { employees, findEmployee } from "@/features/assessments/data/employees";
import { resolveAssessmentStep } from "@/features/assessments/model/navigation";
import { assistantReply, assistantSuggestions, type AssistantMode } from "./responses";

export function AssistantDrawer() {
  const { assistantOpen, closeAssistant, state } = useWorkspace();
  const pathname = usePathname();
  const query = useSearchParams();
  const employee = findEmployee(pathname.split("/")[2] ?? "") ?? employees[0];
  const assessment = state.assessments[employee.id];
  const step = resolveAssessmentStep(employee, assessment, query.get("step"));
  const [mode, setMode] = useState<AssistantMode>("formal");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<{ question: string; answer: string; source: string }[]>(
    [],
  );
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ block: "nearest" });
  }, [messages]);

  function ask(value: string) {
    const trimmed = value.trim();
    if (!trimmed) return;
    setMessages((previous) => [
      ...previous,
      { question: trimmed, ...assistantReply(trimmed, mode, employee) },
    ]);
    setQuestion("");
  }

  if (!assistantOpen) return null;
  if (pathname.startsWith("/assessments/"))
    return (
      <Dialog title="Zapytaj OcenoMat" onClose={closeAssistant} drawer="right">
        <Note className="m-5">
          Asystent dla zapisanych ocen jest w przygotowaniu. Na razie skorzystaj z sekcji Pomoc —
          znajdziesz tam instrukcję rozpoczęcia oceny, zapisu ustaleń i sprawdzania dostępu.
        </Note>
      </Dialog>
    );
  return (
    <Dialog title="Zapytaj OcenoMat" onClose={closeAssistant} drawer="right">
      <div className="flex h-full flex-col">
        <div className="border-b bg-surface-muted p-4">
          <p className="mb-3 text-caption text-subtle-foreground">
            Kontekst: {pathname.includes("/assessments/") ? employee.name : "Przestrzeń robocza"} ·{" "}
            {step}
          </p>
          <fieldset
            className="flex flex-wrap gap-1 rounded-xl border p-1"
            aria-label="Tryb asystenta"
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
                onClick={() => setMode(id)}
                className={`rounded-lg px-3 py-2 text-label ${mode === id ? "bg-surface font-semibold shadow-sm" : "text-muted-foreground"}`}
              >
                {label}
              </button>
            ))}
          </fieldset>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-5">
          <Note className="mb-5">
            Gotowe odpowiedzi demonstracyjne. Odwołania są wpisane ręcznie i nie są powiązane ze
            zweryfikowanymi fragmentami dokumentów. To nie jest odpowiedź systemu RAG.
          </Note>
          <div aria-live="polite" aria-relevant="additions">
            {messages.map((message, index) => (
              <div key={index} className="mb-4">
                <p className="mb-2 text-body font-semibold">{message.question}</p>
                <div className="rounded-xl border bg-surface-muted p-4">
                  <p className="text-body leading-6">{message.answer}</p>
                  <div className="mt-3 rounded-lg border bg-surface p-3 text-caption text-muted-foreground">
                    <Icon name="file" size={13} className="mr-1 inline" />
                    Niezweryfikowane odwołanie demo: {message.source}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <p className="eyebrow mb-3">Proponowane pytania</p>
          <div className="space-y-2">
            {assistantSuggestions(mode, step).map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => ask(suggestion)}
                className="flex w-full items-center gap-2 rounded-xl border px-3 py-3 text-left text-body hover:bg-surface-muted"
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
              maxLength={2000}
              onChange={(event) => setQuestion(event.target.value)}
            />
          </label>
          <Button
            type="submit"
            variant="primary"
            aria-label="Wyślij pytanie"
            disabled={!question.trim()}
          >
            <Icon name="send" size={17} />
          </Button>
        </form>
      </div>
    </Dialog>
  );
}
