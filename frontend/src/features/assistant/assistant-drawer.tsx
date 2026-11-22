"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Note } from "@/components/ui/card";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import { askAssistant, assistantAssessments } from "./actions";
import { assessmentStatusLabels } from "@/features/assessments/types";
import { assistantSuggestions } from "./responses";
import { assessmentContext, type AssistantAnswer, type AssistantMode } from "./types";
import { CitationCard } from "./citation-card";

const emptyMessages: { question: string; answer: AssistantAnswer }[] = [];

export function AssistantDrawer() {
  const { assistantOpen, closeAssistant } = useWorkspace();
  const pathname = usePathname();
  return (
    <aside
      hidden={!assistantOpen}
      aria-label="Asystent OcenoMat"
      className={`no-print fixed inset-y-0 right-0 z-50 w-[26.5625rem] max-w-full flex-col border-l bg-surface shadow-overlay min-[1200px]:sticky min-[1200px]:top-0 min-[1200px]:z-auto min-[1200px]:h-dvh min-[1200px]:w-full min-[1200px]:shadow-none ${assistantOpen ? "flex" : "hidden"}`}
    >
      <div className="flex shrink-0 items-center justify-between gap-3 border-b px-6 py-5">
        <h2 className="text-base font-semibold">Zapytaj OcenoMat</h2>
        <Button
          variant="ghost"
          className="size-9 p-0!"
          onClick={closeAssistant}
          aria-label="Zamknij asystenta"
        >
          <Icon name="close" />
        </Button>
      </div>
      <div className="min-h-0 flex-1">
        <AssistantSession assessmentId={assessmentContext(pathname)} open={assistantOpen} />
      </div>
    </aside>
  );
}

function AssistantSession({
  assessmentId: routeId,
  open,
}: {
  assessmentId?: string;
  open: boolean;
}) {
  const [assessmentId, setAssessmentId] = useState(routeId);
  const [previousRouteId, setPreviousRouteId] = useState(routeId);
  if (routeId !== previousRouteId) {
    setPreviousRouteId(routeId);
    if (routeId) setAssessmentId(routeId);
  }
  const [assessments, setAssessments] = useState<
    NonNullable<Awaited<ReturnType<typeof assistantAssessments>>["assessments"]>
  >([]);
  const [selectionOpen, setSelectionOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [listError, setListError] = useState("");
  const [listLoaded, setListLoaded] = useState(false);
  const [copyMessage, setCopyMessage] = useState("");
  const [mode, setMode] = useState<AssistantMode>(assessmentId ? "conversation" : "formal");
  const [kind, setKind] = useState<"first" | "periodic">("periodic");
  const [question, setQuestion] = useState("");
  const [conversations, setConversations] = useState<
    Record<string, { question: string; answer: AssistantAnswer }[]>
  >({});
  const conversationKey = `${mode}:${mode === "conversation" ? (assessmentId ?? "general") : kind}`;
  const messages = conversations[conversationKey] ?? emptyMessages;
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();
  const end = useRef<HTMLDivElement>(null);
  const selected = assessments.find((item) => item.id === assessmentId);

  useEffect(() => {
    if (!open) return;
    let active = true;
    assistantAssessments().then((result) => {
      if (!active) return;
      setListLoaded(true);
      if (result.error) setListError(result.error);
      else {
        const available = result.assessments ?? [];
        setAssessments(available);
        setConversations((previous) =>
          Object.fromEntries(
            Object.entries(previous).filter(
              ([key]) =>
                !key.startsWith("conversation:") ||
                key === "conversation:general" ||
                available.some((item) => key === `conversation:${item.id}`),
            ),
          ),
        );
        if (assessmentId && !available.some((item) => item.id === assessmentId))
          setAssessmentId(undefined);
        setListError("");
      }
    });
    return () => {
      active = false;
    };
  }, [open, assessmentId]);

  useEffect(() => {
    end.current?.scrollIntoView({ block: "nearest" });
  }, [messages]);

  function ask(value: string) {
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
        task: "question",
        history:
          mode === "conversation" && assessmentId
            ? messages
                .filter(({ answer }) => answer.status === "answered" && answer.claims?.length)
                .slice(-4)
                .map(({ question, answer }) => ({
                  question,
                  answer: (answer.claims ?? [])
                    .map((claim) => claim.text)
                    .join("\n")
                    .slice(0, 4000),
                }))
            : [],
      });
      if ("error" in result) {
        if (result.accessLost && assessmentId) {
          setConversations((previous) =>
            Object.fromEntries(
              Object.entries(previous).filter(([key]) => key !== `conversation:${assessmentId}`),
            ),
          );
          setAssessmentId(undefined);
        }
        setError(result.error);
        return;
      }
      setConversations((previous) => ({
        ...previous,
        [conversationKey]: [
          ...(previous[conversationKey] ?? []),
          { question: trimmed, answer: result.answer },
        ],
      }));
      setQuestion("");
    });
  }

  function changeMode(value: AssistantMode) {
    setMode(value);
    setError("");
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b bg-surface-muted p-4">
        <p className="mb-2 text-label font-semibold">W czym Ci pomóc?</p>
        <fieldset className="grid grid-cols-2 gap-2" aria-label="Tryb asystenta" disabled={pending}>
          {(
            [
              ["formal", "Przepisy i procedury"],
              ["conversation", "Rozmowa z pracownikiem"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              aria-pressed={mode === id}
              onClick={() => changeMode(id)}
              className={`rounded-lg border px-3 py-3 text-left text-label transition-colors ${mode === id ? "border-primary bg-primary-muted font-semibold text-primary" : "bg-surface text-muted-foreground hover:border-border-interactive"}`}
            >
              {label}
            </button>
          ))}
        </fieldset>
        <div className="mt-3 rounded-lg border bg-surface px-3 py-3" aria-live="polite">
          <p className="text-label font-semibold">
            {mode === "formal"
              ? "Pytania o zasady oceny"
              : assessmentId
                ? (selected?.name ?? "Wybrana ocena")
                : "Rozmowa bez wybranego pracownika"}
          </p>
          <p className="mt-1 text-caption leading-5 text-muted-foreground">
            {mode === "formal"
              ? "Odpowiedzi opierają się na dostępnych źródłach. Zapisane dane oceny nie są automatycznie przekazywane."
              : assessmentId
                ? selected
                  ? `${selected.kind === "first" ? "Pierwsza ocena" : "Ocena okresowa"} · ${assessmentStatusLabels[selected.status]} · utworzona ${new Date(selected.created_at).toLocaleDateString("pl-PL", { timeZone: "Europe/Warsaw" })}`
                  : "Po wysłaniu pytania asystent sprawdzi dostęp do wybranej oceny."
                : "Otwórz ocenę pracownika, aby otrzymać wskazówki na podstawie jego zapisanych danych. Tutaj możesz zapytać ogólnie."}
          </p>
          {mode === "conversation" && (
            <>
              {selected && (
                <p className="mt-2 text-caption text-muted-foreground">
                  Przy otwarciu panelu: {selected.observations} obserwacji · {selected.ratings}{" "}
                  zatwierdzonych ocen · {selected.notes ? "notatki dostępne" : "bez notatek"}.
                  Niezapisane zmiany nie są uwzględniane.
                </p>
              )}
              <Button
                className="mt-3"
                disabled={pending}
                onClick={() => setSelectionOpen(!selectionOpen)}
              >
                {assessmentId ? "Zmień ocenę" : "Wybierz pracownika i ocenę"}
              </Button>
              {selectionOpen && (
                <div className="mt-3">
                  <label className="block">
                    <span className="field-label">Szukaj pracownika</span>
                    <input
                      className="field"
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                    />
                  </label>
                  {listError ? (
                    <p role="alert" className="mt-2 text-danger">
                      {listError}
                    </p>
                  ) : null}
                  <div className="mt-2 max-h-48 overflow-y-auto">
                    {assessments
                      .filter((item) =>
                        item.name.toLocaleLowerCase("pl").includes(search.toLocaleLowerCase("pl")),
                      )
                      .map((item) => (
                        <button
                          key={item.id}
                          type="button"
                          className="block w-full border-b px-2 py-3 text-left hover:bg-surface-muted"
                          onClick={() => {
                            setAssessmentId(item.id);
                            setSelectionOpen(false);
                            setError("");
                            setQuestion("");
                          }}
                        >
                          <strong className="block">{item.name}</strong>
                          <span className="text-caption text-muted-foreground">
                            {item.kind === "first" ? "Pierwsza" : "Okresowa"} ·{" "}
                            {assessmentStatusLabels[item.status]} ·{" "}
                            {new Date(item.created_at).toLocaleDateString("pl-PL", {
                              timeZone: "Europe/Warsaw",
                            })}
                          </span>
                        </button>
                      ))}
                    {!listLoaded && !listError && (
                      <p className="py-3 text-caption">Wczytywanie ocen…</p>
                    )}
                    {listLoaded && !assessments.length && !listError && (
                      <p className="py-3 text-caption">
                        Nie masz dostępnych ocen.{" "}
                        <Link href="/assessments" className="underline">
                          Otwórz listę ocen
                        </Link>
                        , aby rozpocząć nową ocenę lub sprawdzić dostęp.
                      </p>
                    )}
                    {assessments.length > 0 &&
                      !assessments.some((item) =>
                        item.name.toLocaleLowerCase("pl").includes(search.toLocaleLowerCase("pl")),
                      ) && (
                        <p className="py-3 text-caption">Nie znaleziono oceny dla tego nazwiska.</p>
                      )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
        {!assessmentId && (
          <label className="mt-3 block text-caption">
            Zakres pytania
            <select
              className="field mt-1"
              value={kind}
              disabled={pending}
              onChange={(event) => {
                setKind(event.target.value as "first" | "periodic");
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
          {mode === "conversation" && assessmentId
            ? "Asystent korzysta z zapisanych obserwacji, notatek i ocen tej osoby. Dane są wysyłane do zewnętrznej usługi AI; niezapisane zmiany nie są uwzględniane. Propozycje sprawdza przełożony."
            : "Asystent korzysta z ograniczonego, zweryfikowanego korpusu. Może odmówić odpowiedzi przy brakujących podstawach. Decyzje pozostają po stronie przełożonego."}{" "}
          Rozmowy są przechowywane tylko podczas tej sesji w panelu.
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
                    {(claim.context_references ?? []).map((reference, referenceIndex) => (
                      <details
                        key={referenceIndex}
                        className="mt-3 rounded-lg border bg-surface p-3 text-caption text-muted-foreground"
                      >
                        <summary className="font-semibold">Zapis oceny · {reference.label}</summary>
                        <blockquote className="mt-2 whitespace-pre-wrap">
                          {reference.quote}
                        </blockquote>
                      </details>
                    ))}
                  </div>
                ))}
                {message.answer.result && (
                  <p className="text-body">
                    Wynik oceny:{" "}
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
                {mode === "conversation" &&
                  assessmentId &&
                  message.answer.status === "insufficient_evidence" && (
                    <Link
                      href={`/assessments/${encodeURIComponent(assessmentId)}`}
                      className="mt-3 inline-block text-body font-semibold text-primary underline"
                    >
                      Otwórz ocenę i sprawdź zapisane dane
                    </Link>
                  )}
                {message.answer.claims?.length ? (
                  <Button
                    className="mt-3"
                    onClick={async () => {
                      try {
                        await navigator.clipboard.writeText(
                          (message.answer.claims ?? []).map((claim) => claim.text).join("\n\n"),
                        );
                        setCopyMessage("Skopiowano odpowiedź.");
                      } catch {
                        setCopyMessage("Nie udało się skopiować odpowiedzi.");
                      }
                    }}
                  >
                    Kopiuj odpowiedź
                  </Button>
                ) : null}
              </div>
            </div>
          ))}
          {pending && (
            <output className="mb-4 block text-body">
              {mode === "conversation" && assessmentId
                ? "Analizuję zapisane informacje i sprawdzam propozycje…"
                : "Wyszukuję źródła i sprawdzam poparcie odpowiedzi…"}
            </output>
          )}
        </div>
        <p className="sr-only" aria-live="polite">
          {copyMessage}
        </p>
        {error && (
          <p role="alert" className="mb-4 text-body text-danger">
            {error}
          </p>
        )}
        {messages.length > 0 && (
          <Button
            className="mb-4"
            onClick={() => setConversations((previous) => ({ ...previous, [conversationKey]: [] }))}
          >
            Nowa rozmowa
          </Button>
        )}
        {messages.length === 0 && (
          <>
            <p className="eyebrow mb-3">Proponowane pytania</p>
            <div className="space-y-2">
              {(mode === "conversation" && assessmentId
                ? [
                    "Jak przygotować rozmowę na podstawie zapisanych obserwacji?",
                    "Jakie mocne strony i obszary rozwoju warto omówić?",
                    "Zaproponuj pytania do pracownika na podstawie zapisanej oceny.",
                  ]
                : assistantSuggestions(mode, kind)
              ).map((suggestion) => (
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
          </>
        )}
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
