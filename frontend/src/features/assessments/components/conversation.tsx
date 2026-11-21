"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import { nextUnrated } from "../model/scoring";
import type { ConversationTab } from "../model/types";
import { useAssessment } from "./assessment-context";
import { FlowFrame, FlowFooter } from "./flow-frame";

const tabs: { id: ConversationTab; label: string; prompts: string[] }[] = [
  {
    id: "agenda",
    label: "Agenda spotkania",
    prompts: [
      "Rozpocznij od celu spotkania.",
      "Omów zaobserwowane zachowania.",
      "Zapisz wspólne ustalenia.",
    ],
  },
  {
    id: "strengths",
    label: "Mocne strony",
    prompts: [
      "Odwołuj się do konkretnych przykładów.",
      "Nazwij wpływ działań na zespół.",
      "Zachęć do utrzymania dobrych praktyk.",
    ],
  },
  {
    id: "growth",
    label: "Obszary rozwoju",
    prompts: [
      "Opisuj zachowanie, nie cechy osoby.",
      "Daj pracownikowi przestrzeń na jego perspektywę.",
      "Ustal jeden możliwy następny krok.",
    ],
  },
];

export function Conversation() {
  const { assessment, employee, update, go, notify } = useAssessment();
  const { openAssistant } = useWorkspace();
  const [selected, setSelected] = useState(0);
  const tab = tabs[selected];

  function confirm() {
    const missing = nextUnrated(employee, assessment, -1);
    update({
      conversationDone: true,
      competencyIndex: missing >= 0 ? missing : 0,
      indicatorIndex: 0,
      override: null,
    });
    go("rating");
    notify("Rozmowę oznaczono jako przeprowadzoną (demo).");
  }

  return (
    <FlowFrame
      eyebrow="Etap 06 / Rozmowa"
      title="Przygotuj dobrą rozmowę"
      description="Przed sporządzeniem oceny porozmawiaj z pracownikiem o pracy, celach i rozwoju."
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_17.8125rem]">
        <Card className="overflow-hidden">
          <div
            className="flex flex-wrap gap-1 border-b p-4"
            role="tablist"
            aria-label="Materiały do rozmowy"
          >
            {tabs.map((item, index) => (
              <button
                key={item.id}
                type="button"
                id={`tab-${item.id}`}
                role="tab"
                aria-selected={selected === index}
                aria-controls={`panel-${item.id}`}
                tabIndex={selected === index ? 0 : -1}
                onClick={() => setSelected(index)}
                onKeyDown={(event) => {
                  let next = selected;
                  if (event.key === "ArrowRight") next = (selected + 1) % tabs.length;
                  else if (event.key === "ArrowLeft")
                    next = (selected + tabs.length - 1) % tabs.length;
                  else if (event.key === "Home") next = 0;
                  else if (event.key === "End") next = tabs.length - 1;
                  else return;
                  event.preventDefault();
                  setSelected(next);
                  document.getElementById(`tab-${tabs[next].id}`)?.focus();
                }}
                className={`rounded-lg px-3 py-2 text-label ${selected === index ? "bg-primary-muted font-semibold text-primary" : "text-muted-foreground"}`}
              >
                {item.label}
              </button>
            ))}
          </div>
          <div
            role="tabpanel"
            id={`panel-${tab.id}`}
            aria-labelledby={`tab-${tab.id}`}
            className="p-6 sm:p-7"
          >
            <label className="field-label" htmlFor="conversation-text">
              {tab.label}{" "}
              <span className="font-normal text-subtle-foreground">· szkic do edycji</span>
            </label>
            <textarea
              id="conversation-text"
              className="field min-h-[15.3125rem]! text-[0.8125rem]! leading-7!"
              value={assessment.conversation[tab.id]}
              maxLength={10000}
              onChange={(event) =>
                update({
                  conversation: {
                    ...assessment.conversation,
                    [tab.id]: event.target.value,
                  },
                })
              }
            />
            <p className="mt-4 flex items-center gap-2 text-caption text-muted-foreground">
              <Icon name="edit" size={15} />
              Tekst możesz zmienić przed rozmową. Nic nie zostanie automatycznie zatwierdzone.
            </p>
          </div>
        </Card>
        <aside className="space-y-4">
          <Card className="p-6">
            <h2 className="mb-4 flex items-center gap-2 text-body font-semibold text-primary">
              <Icon name="sparkles" size={17} />
              Podpowiedzi OcenoMat
            </h2>
            <ol className="space-y-3">
              {tab.prompts.map((prompt, index) => (
                <li key={prompt} className="flex items-start gap-2">
                  <span className="grid size-5 shrink-0 place-items-center rounded-md bg-primary-muted text-caption text-primary">
                    {index + 1}
                  </span>
                  <p className="text-label leading-5 text-muted-foreground">{prompt}</p>
                </li>
              ))}
            </ol>
          </Card>
          <Button className="w-full justify-start gap-3 p-5! text-primary" onClick={openAssistant}>
            <Icon name="message" size={19} />
            <span className="flex-1 text-left">
              <span className="block text-body font-semibold">Zapytaj OcenoMat</span>
              <span className="mt-1 block text-label font-normal text-muted-foreground">
                Pytania przed rozmową
              </span>
            </span>
            <Icon name="arrow-up-right" size={16} />
          </Button>
        </aside>
      </div>
      <FlowFooter
        onBack={() => go("period")}
        onNext={confirm}
        label="Potwierdź rozmowę i przejdź do oceny"
      />
    </FlowFrame>
  );
}
