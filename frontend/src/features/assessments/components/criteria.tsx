"use client";

import { useState } from "react";
import { Card, Note } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Icon } from "@/components/ui/icon";
import { criterionNames } from "../data/competencies";
import { criterionIds, type CriterionId } from "../model/types";
import { requiredCriteria, suggestedCriteria, formType } from "../model/scoring";
import { useAssessment } from "./assessment-context";
import { FlowFrame, FlowFooter } from "./flow-frame";

function useExtraCriteria() {
  const { assessment, employee, update, notify } = useAssessment();
  return (id: CriterionId) => {
    if (requiredCriteria(employee).includes(id)) return;
    const selected = assessment.extra.includes(id);
    if (!selected && assessment.extra.length >= 3) {
      notify("Można wybrać maksymalnie trzy dodatkowe kryteria.");
      return;
    }
    update({
      extra: selected ? assessment.extra.filter((item) => item !== id) : [...assessment.extra, id],
      override: null,
    });
  };
}

export function PositionAnalysis() {
  const { employee, assessment, go } = useAssessment();
  const toggle = useExtraCriteria();
  const [preview, setPreview] = useState(false);
  const suggestions = suggestedCriteria(employee);
  return (
    <FlowFrame
      eyebrow="Faza 1 / Analiza OSP"
      title="Stanowisko i kontekst"
      description="Sprawdź pochodzenie rekomendacji, zanim zatwierdzisz kryteria."
    >
      <div className="grid gap-4 lg:grid-cols-[1.07fr_.93fr]">
        <Card className="p-6 sm:p-7">
          <div className="flex flex-wrap justify-between gap-2">
            <p className="eyebrow">Profil stanowiska</p>
            <Badge>Źródło: OSP · streszczenie</Badge>
          </div>
          <div className="my-7 flex items-center gap-4">
            <span className="grid h-16 w-14 shrink-0 place-items-center rounded-xl bg-primary-muted text-primary">
              <Icon name="file" size={27} />
            </span>
            <div>
              <h2 className="text-sm font-semibold">{employee.role}</h2>
              <p className="mt-2 text-label text-muted-foreground">
                {employee.osp} · przykładowy OSP
              </p>
              <button
                type="button"
                className="mt-2 inline-flex items-center gap-1 text-label font-semibold text-primary"
                onClick={() => setPreview(true)}
              >
                Zobacz powiązanie z OSP
                <Icon name="arrow-up-right" size={13} />
              </button>
            </div>
          </div>
          <div className="border-t pt-5">
            <p className="eyebrow mb-3">Zakres obowiązków · parafraza</p>
            <p className="text-body leading-6 text-muted-foreground">
              {employee.manager
                ? "Koordynacja zadań 5–9 pracowników, nadzór nad pracą wydziału."
                : employee.id === "maria"
                  ? "Analiza zagadnień prawnych i przygotowywanie opinii dotyczących AI."
                  : "Analizy, przegląd dokumentacji i przygotowywanie rekomendacji."}
            </p>
          </div>
          <Note className="mt-5">
            Opis stanowiska mówi, <b>czego wymaga rola</b>. Nie dowodzi, jak konkretny pracownik
            wykonywał zadania.
          </Note>
        </Card>
        <Card className="p-6 sm:p-7">
          <div className="flex items-center gap-2 text-primary">
            <Icon name="sparkles" size={17} />
            <p className="text-label font-semibold">REKOMENDACJA DODATKOWYCH KRYTERIÓW</p>
          </div>
          <h2 className="mt-5 text-[1.1875rem] font-semibold tracking-tight">
            {criterionNames[suggestions[0]]}
          </h2>
          <p className="mt-3 text-body leading-6 text-muted-foreground">
            {employee.manager
              ? "Obowiązki kierownicze sugerują potrzebę negocjowania i analizowania zależności."
              : "Praca z dokumentami i formułowanie wniosków uzasadniają rozważenie kompetencji analitycznych."}
          </p>
          <Note className="mt-3 bg-surface text-caption">
            OSP: {employee.osp} · powiązanie koncepcyjne, bez cytatu dosłownego. Decyzję podejmuje
            przełożony.
          </Note>
          <div className="mt-7 space-y-2">
            {suggestions.map((id) => (
              <label
                key={id}
                className="flex cursor-pointer items-center gap-3 rounded-choice border px-4 py-3 text-body"
              >
                <input
                  type="checkbox"
                  className="size-4 shrink-0"
                  checked={assessment.extra.includes(id)}
                  onChange={() => toggle(id)}
                />
                <span>{criterionNames[id]}</span>
              </label>
            ))}
          </div>
        </Card>
      </div>
      <FlowFooter
        onBack={() => go("setup")}
        onNext={() => go("criteria")}
        label="Przejdź do kryteriów"
      />
      {preview ? (
        <Dialog title="Opis stanowiska pracy" onClose={() => setPreview(false)}>
          <div className="space-y-4 p-6 text-body leading-6 text-muted-foreground">
            <p className="font-semibold text-foreground">
              {employee.name} · {employee.role}
            </p>
            <p>Zakres obowiązków (dokument demonstracyjny):</p>
            <ul className="list-disc space-y-2 pl-5">
              <li>Analiza dokumentów i danych.</li>
              <li>Przygotowywanie rekomendacji i materiałów.</li>
              <li>Współpraca z innymi komórkami organizacyjnymi.</li>
            </ul>
            <p className="text-label">
              W prawdziwej aplikacji można byłoby otworzyć oryginalny plik OSP.
            </p>
            <Button onClick={() => setPreview(false)}>Zamknij</Button>
          </div>
        </Dialog>
      ) : null}
    </FlowFrame>
  );
}

export function Criteria() {
  const { employee, assessment, go } = useAssessment();
  const required = requiredCriteria(employee);
  const suggestions = suggestedCriteria(employee);
  const toggle = useExtraCriteria();
  return (
    <FlowFrame
      eyebrow="Faza 1 / Kryteria"
      title="Ustal, co będzie oceniane"
      description="System dobiera obowiązkowe kryteria na podstawie typu arkusza. Ty wybierasz dodatkowe."
    >
      <div className="grid gap-4 lg:grid-cols-[.93fr_1.07fr]">
        <Card className="p-6">
          <div className="mb-5 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold">Kryteria obowiązkowe</h2>
              <p className="mt-2 text-label text-muted-foreground">
                Arkusz {formType(employee)} · zestaw niezmienny
              </p>
            </div>
            <Badge tone="success">5 wymaganych</Badge>
          </div>
          {required.map((id) => (
            <div key={id} className="flex items-center gap-3 border-b py-4 last:border-0">
              <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-success-muted text-success">
                <Icon name="lock" size={14} />
              </span>
              <span className="flex-1 text-body leading-5 font-medium">{criterionNames[id]}</span>
              <Icon name="check" size={15} className="text-subtle-foreground" />
            </div>
          ))}
        </Card>
        <Card className="p-6">
          <div className="mb-5 flex items-start justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold">Kryteria dodatkowe</h2>
              <p className="mt-2 text-label text-muted-foreground">Wybierz 0–3 na podstawie OSP.</p>
            </div>
            <Badge tone="primary">{assessment.extra.length} / 3</Badge>
          </div>
          <fieldset className="max-h-120 space-y-2 overflow-y-auto pr-1">
            <legend className="sr-only">Dodatkowe kryteria oceny</legend>
            {criterionIds
              .filter((id) => !required.includes(id))
              .map((id) => (
                <label
                  key={id}
                  className={`flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-3 text-body ${assessment.extra.includes(id) ? "border-primary bg-primary-muted" : "bg-surface"}`}
                >
                  <input
                    type="checkbox"
                    checked={assessment.extra.includes(id)}
                    onChange={() => toggle(id)}
                    className="size-4 shrink-0"
                  />
                  <span className="flex-1 leading-5">{criterionNames[id]}</span>
                  {suggestions.includes(id) ? <Badge tone="primary">OSP</Badge> : null}
                </label>
              ))}
          </fieldset>
        </Card>
      </div>
      <Note className="mt-4">
        Źródło reguł: rozporządzenie PRM z 4 kwietnia 2016 r., §§ 2–5. Oficjalny katalog obejmuje 14
        kryteriów. Wybór opcjonalnych kryteriów wymaga uzasadnienia obowiązkami z OSP.
      </Note>
      <FlowFooter
        onBack={() => go("analysis")}
        onNext={() => go("timing")}
        label="Zatwierdź kryteria"
      />
    </FlowFrame>
  );
}
