import { Card, Note } from "@/components/ui/card";
import { Button, ButtonLink } from "@/components/ui/button";
import { CheckRow } from "@/components/ui/choice";
import { Icon } from "@/components/ui/icon";
import { timingError } from "../model/scoring";
import { useAssessment } from "./assessment-context";
import { FlowFrame, FlowFooter } from "./flow-frame";

const checks = [
  "Omówiono obowiązki wynikające z OSP",
  "Przedstawiono kryteria i oczekiwania",
  "Potwierdzono termin oceny i zapoznanie z ustaleniami",
];

export function Timing() {
  const { assessment, update, go, notify } = useAssessment();
  function save() {
    const error = timingError(assessment);
    if (error) {
      notify(error);
      return;
    }
    go("saved");
    notify("Ustalenia zapisano lokalnie.");
  }
  return (
    <FlowFrame
      eyebrow="Faza 1 / Ustalenia"
      title="Rozpocznij proces prawidłowo"
      description="Zapisz kryteria i daty, po czym wróć do oceny w czasie jej trwania."
    >
      <div className="grid gap-4 lg:grid-cols-[1.06fr_.94fr]">
        <Card className="p-6 sm:p-7">
          <h2 className="mb-6 text-sm font-semibold">Terminy oceny</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <label>
              <span className="field-label">Rozmowa rozpoczynająca</span>
              <input
                type="date"
                className="field"
                required
                value={assessment.dateTalk}
                onChange={(event) => update({ dateTalk: event.target.value })}
              />
            </label>
            <label>
              <span className="field-label">Termin sporządzenia oceny</span>
              <input
                type="date"
                className="field"
                required
                min={assessment.dateTalk}
                value={assessment.dateAssessment}
                onChange={(event) => update({ dateAssessment: event.target.value })}
              />
            </label>
          </div>
          <Note className="mt-6">
            W przypadku typowego rozpoczęcia oceny przepisy przewidują terminy na ustalenie
            kryteriów. Dla szczególnych przypadków, w tym poprzedniej oceny negatywnej, obowiązują
            odrębne reguły. Daty w demo są fikcyjne i wymagają ręcznej weryfikacji.
          </Note>
        </Card>
        <Card className="p-6 sm:p-7">
          <h2 className="mb-2 text-sm font-semibold">Potwierdzenia z rozmowy</h2>
          <p className="mb-6 text-label text-muted-foreground">
            Zaznacz wyłącznie wykonane czynności.
          </p>
          <div className="space-y-5">
            {checks.map((check, index) => (
              <CheckRow
                key={check}
                checked={assessment.agreed[index]}
                onChange={(checked) =>
                  update({
                    agreed: assessment.agreed.map((value, i) => (index === i ? checked : value)),
                  })
                }
              >
                {check}
              </CheckRow>
            ))}
          </div>
          <p className="mt-6 border-t pt-4 text-label text-subtle-foreground">
            {assessment.agreed.filter(Boolean).length} / 3 potwierdzone
          </p>
        </Card>
      </div>
      <FlowFooter
        onBack={() => go("criteria")}
        onNext={save}
        label="Zapisz ustalenia"
        disabled={!assessment.agreed.every(Boolean)}
      />
    </FlowFrame>
  );
}

export function TimingSaved() {
  const { go } = useAssessment();
  return (
    <FlowFrame
      eyebrow="Faza 1 / Zapis"
      title="Ustalenia zapisane"
      description="Ocena jest procesem rozłożonym w czasie, a nie jedną sesją w kreatorze."
    >
      <Card className="mx-auto max-w-[46.25rem] p-8 text-center sm:p-11">
        <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-success-muted text-success">
          <Icon name="check" size={29} />
        </span>
        <h2 className="mt-6 text-[1.4375rem] font-semibold tracking-tight">
          Teraz trwa okres oceny
        </h2>
        <p className="mx-auto mt-3 max-w-[28.125rem] text-body leading-6 text-muted-foreground">
          Przełożona wróci do procesu, aby dokumentować konkretne zdarzenia i zaobserwowane
          zachowania.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-2">
          <ButtonLink href="/">Wróć na pulpit</ButtonLink>
          <Button variant="primary" onClick={() => go("period")}>
            Zobacz okres obserwacji
          </Button>
        </div>
        <p className="mt-4 text-caption text-subtle-foreground">
          Na potrzeby prezentacji możesz przejść dalej bez rzeczywistego upływu czasu.
        </p>
      </Card>
    </FlowFrame>
  );
}
