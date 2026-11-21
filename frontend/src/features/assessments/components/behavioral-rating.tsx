import { Card, Note } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RadioChoice } from "@/components/ui/choice";
import { Icon } from "@/components/ui/icon";
import { levels } from "../data/competencies";
import { activeCompetencies } from "../model/scoring";
import type { Answer } from "../model/types";
import { useAssessment } from "./assessment-context";
import { FlowFrame, FlowFooter } from "./flow-frame";

export function BehavioralRating() {
  const { assessment, employee, update, go } = useAssessment();
  const list = activeCompetencies(employee, assessment.extra);
  const competency = list[assessment.competencyIndex] ?? list[0];
  const index = Math.min(assessment.indicatorIndex, competency.indicators.length - 1);
  const indicator = competency.indicators[index];
  const answer = assessment.answers[competency.id]?.[index];
  const noteKey = `${competency.id}-${index}`;

  function select(value: Answer) {
    update({
      answers: {
        ...assessment.answers,
        [competency.id]: {
          ...assessment.answers[competency.id],
          [index]: value,
        },
      },
      override: null,
    });
  }

  return (
    <FlowFrame
      eyebrow="Faza 3 / Ocena zachowań"
      title="Zobacz zachowanie, nie liczbę"
      description="Rozmowa odbyła się wcześniej. Teraz przełożona ustala oceny cząstkowe."
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_16.875rem]">
        <Card className="overflow-hidden">
          <div className="flex items-start justify-between gap-3 border-b p-6">
            <div>
              <p className="eyebrow mb-2">
                Kryterium {list.indexOf(competency) + 1} z {list.length}
              </p>
              <h2 className="text-lg font-semibold tracking-tight">{competency.name}</h2>
            </div>
            <Badge>
              Wskaźnik {index + 1}/{competency.indicators.length}
            </Badge>
          </div>
          <div className="p-6 sm:p-7">
            <h3
              id="indicator-question"
              className="mb-2 text-[1.0625rem] leading-7 font-semibold tracking-tight"
            >
              {indicator.question}
            </h3>
            <p className="mb-6 text-label text-muted-foreground">
              Wybierz najbliższy opis zachowania. Skala punktowa pozostaje oddzielną decyzją.
            </p>
            <fieldset aria-labelledby="indicator-question" className="space-y-2">
              {levels.map((level, value) => (
                <RadioChoice
                  key={level.score}
                  name="behavior"
                  value={String(value)}
                  checked={answer === value}
                  onChange={() => select(value as Answer)}
                >
                  {indicator.descriptions[value]}
                </RadioChoice>
              ))}
              <RadioChoice
                name="behavior"
                value="none"
                checked={answer === -1}
                onChange={() => select(-1)}
              >
                Brak podstaw do oceny tego zachowania
              </RadioChoice>
            </fieldset>
          </div>
        </Card>
        <aside className="space-y-4">
          <Card className="p-5">
            <h2 className="mb-3 flex items-center gap-2 text-label font-semibold text-primary">
              <Icon name="sparkles" size={17} />
              OcenoMat podpowiada
            </h2>
            <p className="text-label leading-6 text-muted-foreground">
              Odnieś odpowiedź do konkretnego zdarzenia, nie do ogólnego wrażenia. Brak obserwacji
              nie oznacza poziomu 1.
            </p>
          </Card>
          <Card className="p-5">
            <label className="field-label" htmlFor="behavior-note">
              Przykład z pracy (opcjonalnie)
            </label>
            <textarea
              id="behavior-note"
              className="field"
              rows={5}
              maxLength={10000}
              placeholder="Sytuacja, działanie, rezultat…"
              value={assessment.notes[noteKey] ?? ""}
              onChange={(event) =>
                update({
                  notes: { ...assessment.notes, [noteKey]: event.target.value },
                })
              }
            />
          </Card>
          <Note>
            Opisy pięciu poziomów są <b>autorskimi przykładami do demo</b> — nie są pełnym tekstem
            Model_kompetencji.xlsx.
          </Note>
        </aside>
      </div>
      <FlowFooter
        onBack={() => (index ? update({ indicatorIndex: index - 1 }) : go("conversation"))}
        onNext={() => {
          if (answer === undefined) return;
          if (index < competency.indicators.length - 1) update({ indicatorIndex: index + 1 });
          else {
            update({ override: null });
            go("recommendation");
          }
        }}
        label={
          index === competency.indicators.length - 1 ? "Pokaż rekomendację" : "Kolejne zachowanie"
        }
        disabled={answer === undefined}
      />
    </FlowFrame>
  );
}
