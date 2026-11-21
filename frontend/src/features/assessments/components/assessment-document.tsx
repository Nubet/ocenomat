"use client";

import { useState } from "react";
import { Card, Note } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckRow } from "@/components/ui/choice";
import { Icon } from "@/components/ui/icon";
import { formatMean, formType, periodicResult } from "../model/scoring";
import type { Assessment, Employee } from "../model/types";
import { useAssessment } from "./assessment-context";
import { FlowFrame, FlowFooter } from "./flow-frame";

export function DocumentPaper({
  employee,
  assessment,
  part,
}: {
  employee: Employee;
  assessment: Assessment;
  part: "I" | "II" | "III";
}) {
  const result = periodicResult(employee, assessment);
  return (
    <article className="report-paper mx-auto max-w-[43.125rem] border border-document-border bg-document p-[1.875rem] font-document text-body text-document-foreground shadow-card max-compact:p-3">
      <p className="text-center text-[0.5625rem] font-bold tracking-wider uppercase opacity-65">
        KOMPAS · PODGLĄD UKŁADU DOKUMENTU — NIE OFICJALNY WZÓR
      </p>
      <div className="mb-5 border-b-2 border-document-foreground py-5">
        <h2 className="text-center text-[1.0625rem] font-bold">
          Arkusz oceny okresowej — {formType(employee)}
        </h2>
        <p className="mt-2 text-center text-label">Część {part} · przykład wypełnienia</p>
      </div>
      {part === "I" ? (
        <>
          <h3 className="mb-3 font-bold">CZĘŚĆ I — Ustalenie kryteriów i terminu</h3>
          <table>
            <tbody>
              {[
                ["Osoba oceniana", employee.name],
                ["Stanowisko", employee.role],
                ["Arkusz", formType(employee)],
                ["Rozmowa rozpoczynająca", assessment.dateTalk],
                ["Termin oceny", assessment.dateAssessment],
              ].map(([label, value]) => (
                <tr key={label}>
                  <th scope="row">{label}</th>
                  <td>{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <h3 className="mt-6 mb-3 font-bold">Przyjęte kryteria</h3>
          <table>
            <tbody>
              {result.list.map((competency, index) => (
                <tr key={competency.id}>
                  <th scope="row" className="w-7">
                    {index + 1}.
                  </th>
                  <td>
                    {competency.name}
                    {index >= 5 ? " (dodatkowe)" : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ) : part === "II" ? (
        <>
          <h3 className="mb-3 font-bold">CZĘŚĆ II — Sporządzenie oceny</h3>
          <table>
            <tbody>
              {result.list.map((competency) => (
                <tr key={competency.id}>
                  <th scope="row">{competency.name}</th>
                  <td className="w-18">{assessment.scores[competency.id] ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <table className="mt-6">
            <tbody>
              {[
                ["Średnia punktowa", formatMean(result.mean)],
                ["Poziom ogólny", result.complete ? result.level : "W trakcie"],
                [
                  "Wynik",
                  !result.complete ? "Do ustalenia" : result.positive ? "Pozytywny" : "Negatywny",
                ],
              ].map(([label, value]) => (
                <tr key={label}>
                  <th scope="row">{label}</th>
                  <td>{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <h3 className="mt-6 mb-3 font-bold">Uzasadnienie i rozwój</h3>
          <p className="min-h-20 border border-document-border p-3 text-label whitespace-pre-wrap">
            {assessment.conversation.growth}
          </p>
        </>
      ) : (
        <>
          <h3 className="mb-4 font-bold">CZĘŚĆ III — Przypadki szczególne</h3>
          <p className="border border-document-border p-4 text-label leading-6">
            Ta część dotyczy określonych przypadków urzędników służby cywilnej (wniosek dotyczący
            stopnia służbowego). Nie każda osoba oceniana wypełnia część III. W demo pole pozostaje
            poglądowe.
          </p>
        </>
      )}
      <div className="mt-12 grid grid-cols-2 gap-8 text-center text-caption">
        <p className="border-t border-document-border pt-2">Podpis oceniającego</p>
        <p className="border-t border-document-border pt-2">Potwierdzenie zapoznania</p>
      </div>
      <p className="mt-8 text-[0.5625rem] opacity-65">
        Nie jest urzędowym formularzem B/C; drukowanie służy wyłącznie pokazaniu danych w makiecie.
      </p>
    </article>
  );
}

const checks = [
  "Rozmowa oceniająca przeprowadzona",
  "Arkusz sprawdzony i podpisany",
  "Pracownik zapoznany z oceną",
];

export function AssessmentDocument() {
  const { assessment, employee, update, go } = useAssessment();
  const [part, setPart] = useState<"I" | "II" | "III">("I");
  const result = periodicResult(employee, assessment);
  return (
    <FlowFrame
      eyebrow="Faza 3 / Dokumentacja"
      title="Dokument i formalności"
      description="Zgodność wymaga oficjalnego wzoru arkusza; ten podgląd pokazuje strukturę i stan czynności."
    >
      <div className="print-layout grid gap-4 lg:grid-cols-[minmax(0,1fr)_17.5rem]">
        <Card className="print-layout bg-surface-muted p-5 sm:p-6">
          <div className="no-print mb-5 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-body font-semibold">
              Podgląd struktury arkusza {formType(employee)}
            </h2>
            <Badge>Nieoficjalny podgląd</Badge>
          </div>
          <fieldset
            aria-label="Części dokumentu"
            className="no-print mb-5 inline-flex rounded-xl border bg-surface-muted p-1"
          >
            {(["I", "II", "III"] as const).map((value) => (
              <button
                type="button"
                key={value}
                aria-pressed={part === value}
                onClick={() => setPart(value)}
                className={`rounded-lg px-3 py-2 text-label ${part === value ? "bg-surface font-semibold shadow-sm" : "text-muted-foreground"}`}
              >
                Część {value}
              </button>
            ))}
          </fieldset>
          <DocumentPaper employee={employee} assessment={assessment} part={part} />
        </Card>
        <aside className="no-print space-y-4">
          <Card className="p-6">
            <h2 className="text-[0.8125rem] font-semibold">Formalności i potwierdzenia</h2>
            <p className="mt-2 mb-6 text-label leading-5 text-muted-foreground">
              Samo pobranie dokumentu nie zamyka prawnie procesu.
            </p>
            <div className="space-y-5">
              {checks.map((check, index) => (
                <CheckRow
                  key={check}
                  checked={assessment.formal[index]}
                  onChange={(checked) =>
                    update({
                      formal: assessment.formal.map((value, i) => (i === index ? checked : value)),
                    })
                  }
                >
                  {check}
                </CheckRow>
              ))}
            </div>
            <p className="mt-5 border-t pt-4 text-label text-subtle-foreground">
              {assessment.formal.filter(Boolean).length}/3 potwierdzone
            </p>
          </Card>
          <Card className="p-6">
            <h3 className="mb-3 text-body font-semibold">Eksport podglądu</h3>
            <p className="mb-4 text-label leading-5 text-muted-foreground">
              Wydruk z przeglądarki nie zastępuje wzoru urzędowego.
            </p>
            <Button className="w-full" onClick={() => window.print()}>
              <Icon name="download" size={15} />
              Drukuj / Zapisz PDF
            </Button>
          </Card>
          {result.complete && !result.positive ? (
            <Note>
              Wynik negatywny wymaga formalnego uzasadnienia. Tutaj pokazujemy jedynie makietę
              układu dokumentu.
            </Note>
          ) : null}
        </aside>
      </div>
      <FlowFooter
        onBack={() => go("summary")}
        onNext={() => {
          if (result.complete && assessment.formal.every(Boolean)) go("finished");
        }}
        label="Zamknij prezentację procesu"
        disabled={!assessment.formal.every(Boolean) || !result.complete}
      />
    </FlowFrame>
  );
}
