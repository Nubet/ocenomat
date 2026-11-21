import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { criterionNames } from "../data/competencies";
import { activeCompetencies, formType } from "../model/scoring";
import { criterionIds } from "../model/types";
import { useAssessment } from "./assessment-context";
import { FlowFrame, FlowFooter } from "./flow-frame";

export function ObservationJournal() {
  const { assessment, employee, update, go, notify } = useAssessment();
  const list = activeCompetencies(employee, assessment.extra);
  const criterion = list.some(({ id }) => id === assessment.observationCriterion)
    ? assessment.observationCriterion
    : list[0].id;

  function add() {
    const text = assessment.observationDraft.trim();
    if (!text) {
      notify("Wpisz konkretny przykład obserwacji.");
      return;
    }
    update({
      observations: [
        ...assessment.observations,
        { date: new Date().toLocaleDateString("sv-SE"), text, criterion },
      ],
      observationDraft: "",
    });
    notify("Obserwacja zapisana lokalnie.");
  }

  return (
    <FlowFrame
      eyebrow="Faza 2 / Obserwacje"
      title="Dokumentuj konkretne zachowania"
      description="Okres oceny jest oddzielnym etapem pracy. Nie trzeba oceniać wszystkiego teraz."
    >
      <div className="grid gap-4 lg:grid-cols-[1.18fr_.82fr]">
        <Card className="p-6 sm:p-7">
          <div className="mb-6 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-[0.9375rem] font-semibold">Dziennik obserwacji</h2>
              <p className="mt-2 text-label text-muted-foreground">
                Przykłady zachowań podczas trwającego okresu oceny.
              </p>
            </div>
            <Badge tone="primary">{assessment.observations.length} wpis(y)</Badge>
          </div>
          <div className="space-y-3">
            {assessment.observations.length ? (
              assessment.observations.map((observation, index) => (
                <div key={index} className="rounded-xl border p-4">
                  <div className="mb-3 flex flex-wrap justify-between gap-2">
                    <span className="text-caption font-semibold">
                      {criterionNames[observation.criterion]}
                    </span>
                    <span className="text-caption text-subtle-foreground">{observation.date}</span>
                  </div>
                  <p className="text-body leading-6 whitespace-pre-wrap text-muted-foreground">
                    {observation.text}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-body text-muted-foreground">Nie dodano jeszcze obserwacji.</p>
            )}
          </div>
          <form
            className="mt-6 border-t pt-6"
            onSubmit={(event) => {
              event.preventDefault();
              add();
            }}
          >
            <label className="field-label" htmlFor="observation-draft">
              Dodaj fakt lub przykład z pracy
            </label>
            <textarea
              id="observation-draft"
              className="field"
              placeholder="Sytuacja · działanie · rezultat…"
              maxLength={10000}
              value={assessment.observationDraft}
              onChange={(event) => update({ observationDraft: event.target.value })}
            />
            <div className="mt-3 flex items-end gap-2 max-compact:flex-wrap">
              <label className="min-w-0 flex-1">
                <span className="sr-only">Powiąż z kryterium</span>
                <select
                  className="field"
                  value={criterion}
                  onChange={(event) => {
                    const id = criterionIds.find((id) => id === event.target.value);
                    if (id) update({ observationCriterion: id });
                  }}
                >
                  {list.map(({ id, name }) => (
                    <option key={id} value={id}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>
              <Button type="submit">
                <Icon name="plus" size={16} />
                Dodaj
              </Button>
            </div>
          </form>
        </Card>
        <aside className="space-y-4">
          <Card className="p-6">
            <p className="eyebrow mb-4">Faza 02 / Okres oceny</p>
            <h2 className="text-lg font-semibold tracking-tight">Praca trwa</h2>
            <p className="mt-3 text-body leading-6 text-muted-foreground">
              Zbieranie obserwacji jest opcjonalnym wsparciem. Nie zastępuje rozmowy oceniającej ani
              formalnych ocen cząstkowych.
            </p>
            <dl className="mt-5 space-y-3 text-label">
              {[
                ["Arkusz", formType(employee)],
                ["Kryteria", list.length],
                ["Termin", assessment.dateAssessment],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between gap-3">
                  <dt className="text-muted-foreground">{label}</dt>
                  <dd className="font-semibold">{value}</dd>
                </div>
              ))}
            </dl>
          </Card>
          <Card className="p-6">
            <h2 className="mb-3 text-label font-semibold">Symulacja do prezentacji</h2>
            <p className="mb-5 text-label leading-5 text-muted-foreground">
              Przejdź do kolejnej fazy tak, jakby ustalony okres oceny już minął.
            </p>
            <Button variant="primary" className="w-full" onClick={() => go("conversation")}>
              Symuluj koniec okresu
            </Button>
          </Card>
        </aside>
      </div>
      <FlowFooter onNext={() => go("conversation")} label="Przejdź do rozmowy oceniającej" />
    </FlowFrame>
  );
}
