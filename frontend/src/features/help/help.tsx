"use client";

import { useState } from "react";
import { Card, PageHeading } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Icon } from "@/components/ui/icon";
import { useWorkspace } from "@/features/workspace/workspace-provider";

const questions = [
  [
    "Kto zatwierdza ocenę?",
    "Ostateczny poziom każdej kompetencji zatwierdza przełożony. Kompas wyłącznie pomaga uporządkować obserwacje.",
  ],
  [
    "Czy mogę wrócić do rozpoczętej oceny?",
    "Tak. W tym prototypie stan pracy zapisuje się lokalnie w przeglądarce.",
  ],
  [
    "Skąd pochodzą opisy zachowań?",
    "Są przygotowane wyłącznie na potrzeby demonstracji. W produkcie należy je zastąpić opisami z odpowiedniego Modelu kompetencji.",
  ],
  [
    "Czy wydruk jest oficjalnym arkuszem?",
    "Nie. W tej makiecie jest to przykładowy podgląd. Docelowy eksport ma wypełniać autentyczny wzór dokumentu B/C.",
  ],
];

export function Help() {
  const { openAssistant, reset } = useWorkspace();
  const [confirm, setConfirm] = useState(false);
  return (
    <>
      <PageHeading
        eyebrow="Centrum pomocy"
        title="W czym możemy pomóc?"
        description="Najczęstsze pytania i zasady działania demonstracyjnego Kompasu."
      />
      <div className="grid gap-4 lg:grid-cols-[1fr_18.75rem]">
        <Card className="p-6 sm:p-7">
          <h2 className="mb-5 text-sm font-semibold">Częste pytania</h2>
          {questions.map(([question, answer]) => (
            <details key={question} className="group border-b py-4">
              <summary className="flex list-none items-center justify-between gap-3 text-body font-semibold">
                {question}
                <Icon
                  name="chevron-down"
                  size={17}
                  className="shrink-0 text-subtle-foreground group-open:rotate-180"
                />
              </summary>
              <p className="mt-3 pr-5 text-body leading-6 text-muted-foreground">
                {answer}
              </p>
            </details>
          ))}
        </Card>
        <Card className="h-fit p-6">
          <span className="mb-4 grid size-10 place-items-center rounded-xl bg-primary-muted text-primary">
            <Icon name="sparkles" size={20} />
          </span>
          <h2 className="text-[0.8125rem] font-semibold">
            Asystent w kontekście
          </h2>
          <p className="mt-3 mb-5 text-label leading-6 text-muted-foreground">
            Zapytaj Kompas na dowolnym etapie pracy. Wersja demo korzysta z
            gotowych odpowiedzi.
          </p>
          <Button className="w-full" onClick={openAssistant}>
            Otwórz asystenta
          </Button>
        </Card>
      </div>
      <div className="mt-6 flex flex-wrap items-center gap-2">
        <Button onClick={() => setConfirm(true)}>
          <Icon name="refresh" size={15} />
          Zresetuj demo
        </Button>
        <Badge>Bez backendu · tylko dane testowe</Badge>
      </div>
      {confirm ? (
        <Dialog
          title="Zresetować dane demonstracyjne?"
          onClose={() => setConfirm(false)}
        >
          <div className="p-6">
            <p className="text-body leading-6 text-muted-foreground">
              Przywrócimy przykładowe postępy, oceny i notatki. Zmiany zapisane
              w tej przeglądarce zostaną utracone.
            </p>
            <div className="mt-6 flex justify-end gap-2">
              <Button onClick={() => setConfirm(false)}>Anuluj</Button>
              <Button
                variant="primary"
                onClick={() => {
                  reset();
                  setConfirm(false);
                }}
              >
                Resetuj demo
              </Button>
            </div>
          </div>
        </Dialog>
      ) : null}
    </>
  );
}
