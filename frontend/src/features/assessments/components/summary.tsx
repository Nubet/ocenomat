import { Card, Note } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatMean, periodicResult } from "../model/scoring";
import type { Assessment } from "../model/types";
import { useAssessment } from "./assessment-context";
import { FlowFrame, FlowFooter } from "./flow-frame";

export function Summary() {
  const { assessment, employee, update, go, notify } = useAssessment();
  const result = periodicResult(employee, assessment);

  function fill(one = false) {
    const scores: Assessment["scores"] = { ...assessment.scores };
    result.list.forEach(({ id }, index) => {
      if (one) scores[id] = index === 0 ? 1 : 9;
      else scores[id] ??= 5;
    });
    update({ scores });
    notify(
      one
        ? "Przykład: jedna ocena 1 pomimo wysokiej średniej."
        : "Uzupełniono przykładowe oceny (demo).",
    );
  }

  return (
    <FlowFrame
      eyebrow="Faza 3 / Wynik"
      title="Wynik, który można prześledzić"
      description="Średnia, poziom ogólny i pozytywna lub negatywna ocena wynikają z decyzji przełożonej."
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_17.8125rem]">
        <Card className="overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b px-6 py-5">
            <div>
              <h2 className="text-sm font-semibold">Formalne oceny cząstkowe</h2>
              <p className="mt-1 text-label text-muted-foreground">
                Pięć obowiązkowych i {assessment.extra.length} dodatkowych.
              </p>
            </div>
            <Badge tone={result.complete ? "success" : "warning"}>
              {result.scores.length}/{result.list.length} zatwierdzonych
            </Badge>
          </div>
          <div className="overflow-x-auto">
            <table className="clean-table min-w-[31.25rem]">
              <thead>
                <tr>
                  <th>Kryterium</th>
                  <th>Ocena</th>
                  <th>Status</th>
                  <th>
                    <span className="sr-only">Działanie</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {result.list.map((competency, index) => (
                  <tr key={competency.id}>
                    <td className="font-semibold">
                      {competency.name}
                      {index >= 5 ? (
                        <small className="mt-1 block font-normal text-subtle-foreground">
                          Dodatkowe
                        </small>
                      ) : null}
                    </td>
                    <td className="font-semibold">{assessment.scores[competency.id] ?? "—"}</td>
                    <td>
                      <Badge
                        tone={
                          assessment.scores[competency.id] !== undefined ? "success" : "warning"
                        }
                      >
                        {assessment.scores[competency.id] !== undefined
                          ? "Zatwierdzona"
                          : "Do oceny"}
                      </Badge>
                    </td>
                    <td>
                      <button
                        type="button"
                        onClick={() => {
                          update({
                            competencyIndex: index,
                            indicatorIndex: 0,
                            override: null,
                          });
                          go("rating");
                        }}
                        className="text-label font-semibold text-primary"
                      >
                        Edytuj
                        <span className="sr-only">: {competency.name}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap gap-2 border-t px-6 py-4">
            <Button onClick={() => fill()}>Wypełnij przykładowe oceny (demo)</Button>
            <Button onClick={() => fill(true)}>Sprawdź warunek 1 pkt</Button>
          </div>
        </Card>
        <aside className="space-y-4">
          <section className="rounded-card bg-feature-end p-6 text-white">
            <h2 className="text-caption font-semibold tracking-widest text-feature-accent">
              ŚREDNIA FORMALNA
            </h2>
            <p className="mt-3 text-[2.625rem] font-semibold tracking-heading tabular-nums">
              {formatMean(result.mean)}
            </p>
            <p className="mt-2 text-label text-feature-foreground">
              {result.complete ? result.level : "Wynik niekompletny"}
            </p>
            <div className="mt-5 border-t border-white/20 pt-4">
              <Badge tone={!result.complete ? "neutral" : result.positive ? "success" : "danger"}>
                {!result.complete
                  ? "W trakcie"
                  : result.positive
                    ? "Ocena pozytywna"
                    : "Ocena negatywna"}
              </Badge>
            </div>
          </section>
          <Card className="p-6">
            <h3 className="mb-3 text-body font-semibold">Reguła formalna</h3>
            <p className="text-body leading-6 text-muted-foreground">
              {!result.complete
                ? "Najpierw zatwierdź wszystkie oceny cząstkowe."
                : result.hasOne
                  ? "Co najmniej jedno kryterium ma 1 punkt — wynik negatywny, niezależnie od średniej."
                  : result.mean !== null && result.mean <= 4
                    ? "Średnia nie przekracza 4 — wynik negatywny."
                    : "Średnia przekracza 4 i żadne kryterium nie ma 1 punktu."}
            </p>
            <Note className="mt-3 bg-surface text-caption">
              Rozporządzenie PRM z 4.04.2016 r., § 11. Obliczenia bez zaokrąglania przed ustaleniem
              wyniku.
            </Note>
          </Card>
        </aside>
      </div>
      <FlowFooter
        onBack={() => go("rating")}
        onNext={() => go("document")}
        label="Przejdź do dokumentacji"
        disabled={!result.complete}
      />
    </FlowFrame>
  );
}
