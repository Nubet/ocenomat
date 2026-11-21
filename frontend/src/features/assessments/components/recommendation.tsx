import { Card, Note } from "@/components/ui/card";
import { RadioChoice } from "@/components/ui/choice";
import { levels } from "../data/competencies";
import { activeCompetencies, formatMean, nextUnrated, suggestScore } from "../model/scoring";
import { useAssessment } from "./assessment-context";
import { FlowFrame, FlowFooter } from "./flow-frame";

export function Recommendation() {
  const { assessment, employee, update, go, notify } = useAssessment();
  const list = activeCompetencies(employee, assessment.extra);
  const competency = list[assessment.competencyIndex] ?? list[0];
  const answers = assessment.answers[competency.id] ?? {};
  const suggested = suggestScore(answers);
  const chosen = assessment.override ?? suggested;
  const scores = Object.values(answers)
    .filter((answer) => answer >= 0)
    .map((answer) => levels[answer].score);
  const mean = scores.length
    ? scores.reduce<number>((sum, score) => sum + score, 0) / scores.length
    : null;

  function approve() {
    if (chosen === null) {
      notify("Wybierz poziom oceny.");
      return;
    }
    const nextAssessment = {
      ...assessment,
      scores: { ...assessment.scores, [competency.id]: chosen },
    };
    const next = nextUnrated(employee, nextAssessment, list.indexOf(competency));
    update({
      scores: nextAssessment.scores,
      competencyIndex: next >= 0 ? next : 0,
      indicatorIndex: 0,
      override: null,
    });
    go(next >= 0 ? "rating" : "summary");
    notify("Ocenę cząstkową zatwierdzono.");
  }

  return (
    <FlowFrame
      eyebrow="Faza 3 / Decyzja"
      title="System wyjaśnia. Człowiek decyduje."
      description="Wynik behawioralny i formalna ocena cząstkowa są rozdzielone."
    >
      <div className="grid gap-4 lg:grid-cols-[1.04fr_.96fr]">
        <Card className="p-6 sm:p-7">
          <p className="eyebrow mb-4">Wynik pomocniczy</p>
          <div className="flex items-center gap-4">
            <span className="grid size-16 shrink-0 place-items-center rounded-2xl bg-primary-muted text-[1.75rem] font-semibold text-primary">
              {suggested ?? "—"}
            </span>
            <div>
              <h2 className="text-[1.0625rem] font-semibold">
                {suggested === null
                  ? "Brak wystarczających obserwacji"
                  : levels.find(({ score }) => score === suggested)?.label}
              </h2>
              <p className="mt-2 text-label text-muted-foreground">{competency.name}</p>
            </div>
          </div>
          <Note className="mt-6">
            <b>Jak to policzono?</b> W demonstracji liczymy średnią z wybranych poziomów (
            {mean === null ? "brak ocen" : formatMean(mean)}) i wskazujemy najbliższą wartość z
            1/3/5/7/9. Pozycje „brak podstaw” pomijamy. Ta agregacja <b>nie jest urzędową regułą</b>{" "}
            i wymaga walidacji.
          </Note>
          <h3 className="mt-6 mb-4 text-body font-semibold">Podstawa sugestii</h3>
          <div className="space-y-3">
            {competency.indicators.map((indicator, index) => (
              <div key={indicator.question} className="rounded-xl border p-3">
                <p className="text-label font-semibold">{indicator.question}</p>
                <p className="mt-2 text-label leading-5 text-muted-foreground">
                  {answers[index] === -1
                    ? "Pominięto — brak podstaw"
                    : answers[index] === undefined
                      ? "Brak odpowiedzi"
                      : indicator.descriptions[answers[index]]}
                </p>
              </div>
            ))}
          </div>
        </Card>
        <Card className="p-6 sm:p-7">
          <p className="eyebrow mb-2">Ostateczna decyzja</p>
          <h2 className="text-[1.1875rem] font-semibold tracking-tight">
            Poziom zatwierdza przełożona
          </h2>
          <p className="mt-2 mb-6 text-label leading-5 text-muted-foreground">
            Możesz przyjąć sugestię albo wybrać inną ocenę.
          </p>
          <fieldset className="space-y-2">
            <legend className="sr-only">Formalna ocena cząstkowa</legend>
            {levels.map((level) => (
              <RadioChoice
                key={level.score}
                name="formal-score"
                value={String(level.score)}
                checked={chosen === level.score}
                onChange={() => update({ override: level.score })}
              >
                <span className="flex items-center gap-3">
                  <span
                    className={`grid size-8 shrink-0 place-items-center rounded-lg text-body font-bold ${chosen === level.score ? "bg-primary text-canvas" : "bg-surface-muted text-muted-foreground"}`}
                  >
                    {level.score}
                  </span>
                  <span className="text-body">{level.label}</span>
                </span>
              </RadioChoice>
            ))}
          </fieldset>
        </Card>
      </div>
      <FlowFooter
        onBack={() => go("rating")}
        onNext={approve}
        label="Zatwierdź ocenę"
        disabled={chosen === null}
      />
    </FlowFrame>
  );
}
