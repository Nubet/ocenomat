import { Card, Note, PageHeading } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { Icon } from "@/components/ui/icon";
import { firstNames } from "../data/competencies";
import { firstResult, formatMean } from "../model/scoring";
import { useAssessment } from "./assessment-context";
import { FlowFooter } from "./flow-frame";
import { useRouter } from "next/navigation";

const tabs = ["Kwalifikacja", "Rozmowa wstępna", "Oceny 3/5/7", "Wynik"];

export function FirstAssessment() {
  const { assessment, employee, update } = useAssessment();
  const router = useRouter();
  const step = assessment.firstStep;
  const result = firstResult(assessment.firstScores, assessment.firstReport, assessment.firstExam);
  return (
    <div className="mx-auto max-w-flow">
      <PageHeading
        eyebrow="Osobna ścieżka / Pierwsza ocena"
        title="Pierwsza ocena"
        description="Inny formularz, inna skala i cztery łączne warunki oceny pozytywnej."
      />
      <fieldset
        aria-label="Etapy pierwszej oceny"
        className="mb-6 inline-flex flex-wrap gap-1 rounded-xl border bg-surface-muted p-1"
      >
        {tabs.map((label, index) => (
          <button
            key={label}
            type="button"
            aria-pressed={step === index}
            onClick={() => update({ firstStep: index })}
            className={`rounded-lg px-3 py-2 text-label ${step === index ? "bg-surface font-semibold shadow-sm" : "text-muted-foreground"}`}
          >
            {index + 1}. {label}
          </button>
        ))}
      </fieldset>
      {step === 0 ? (
        <div className="grid gap-4 lg:grid-cols-[1.1fr_.9fr]">
          <Card className="p-7">
            <p className="eyebrow mb-4">Pracownik</p>
            <div className="mb-6 flex items-center gap-3">
              <Avatar employee={employee} size={44} />
              <div>
                <h2 className="text-base font-semibold">{employee.name}</h2>
                <p className="mt-1 text-label text-muted-foreground">{employee.role}</p>
              </div>
            </div>
            <label>
              <span className="field-label">Przykładowa data zatrudnienia</span>
              <input
                type="date"
                className="field"
                value={assessment.firstHire}
                onChange={(event) => update({ firstHire: event.target.value })}
              />
            </label>
            <Note className="mt-5">
              Rozmowa wstępna co do zasady w ciągu 21 dni. W wybranych przypadkach obowiązują
              odrębne zasady kwalifikacji.
            </Note>
          </Card>
          <Card className="p-7">
            <h3 className="mb-3 text-sm font-semibold">Jak wygląda proces?</h3>
            <ol>
              {[
                "Rozmowa wstępna i terminy",
                "Sprawozdanie pracownika",
                "Rozmowa oceniająca",
                "Pięć ocen 3/5/7",
                "Egzamin, warunki i arkusz",
              ].map((label, index) => (
                <li key={label} className="flex gap-3 border-b py-3 text-body last:border-0">
                  <span className="font-semibold text-primary">{index + 1}.</span>
                  <span>{label}</span>
                </li>
              ))}
            </ol>
          </Card>
        </div>
      ) : null}
      {step === 1 ? (
        <Card className="p-7">
          <p className="eyebrow mb-3">Rozmowa wstępna</p>
          <h2 className="text-[1.1875rem] font-semibold">Co należy omówić?</h2>
          <div className="mt-6 grid gap-3 md:grid-cols-2">
            {[
              "Główne obowiązki wynikające z OSP",
              "Oczekiwania dotyczące pracy i zachowania",
              "Sposób przeprowadzenia pierwszej oceny",
              "Termin i zakres sprawozdania",
            ].map((label) => (
              <div key={label} className="flex gap-3 rounded-xl border p-5 text-body">
                <Icon name="check" size={17} className="shrink-0 text-primary" />
                {label}
              </div>
            ))}
          </div>
          <Note className="mt-6">
            Źródło: rozporządzenie PRM z 23.07.2015 r., § 3. Potwierdzenia i podpisy są w
            rzeczywistym arkuszu odrębnymi czynnościami.
          </Note>
        </Card>
      ) : null}
      {step === 2 ? (
        <Card className="p-6 sm:p-7">
          <div className="mb-5 flex items-center justify-between gap-3">
            <h2 className="text-[0.9375rem] font-semibold">Pięć elementów oceny</h2>
            <Badge tone="primary">Skala: 3 / 5 / 7</Badge>
          </div>
          {firstNames.map((name, index) => (
            <fieldset
              key={name}
              className="flex flex-wrap items-center justify-between gap-3 border-b py-4 last:border-0"
            >
              <legend className="sr-only">{name}</legend>
              <span className="text-body font-semibold" aria-hidden="true">
                {name}
              </span>
              <div className="inline-flex gap-1 rounded-xl border bg-surface-muted p-1">
                {([3, 5, 7] as const).map((value) => (
                  <label
                    key={value}
                    className={`relative cursor-pointer rounded-lg px-3 py-2 text-label has-focus-visible:outline-3 has-focus-visible:outline-ring ${assessment.firstScores[index] === value ? "bg-surface font-semibold shadow-sm" : "text-muted-foreground"}`}
                  >
                    <input
                      type="radio"
                      name={`first-score-${index}`}
                      className="sr-only"
                      checked={assessment.firstScores[index] === value}
                      onChange={() =>
                        update({
                          firstScores: assessment.firstScores.map((score, i) =>
                            i === index ? value : score,
                          ),
                        })
                      }
                    />
                    {value}
                  </label>
                ))}
              </div>
            </fieldset>
          ))}
        </Card>
      ) : null}
      {step === 3 ? (
        <div className="grid gap-4 lg:grid-cols-[1.05fr_.95fr]">
          <Card className="p-7">
            <p className="eyebrow mb-2">Wynik formalny</p>
            <div className="mt-5 flex items-center gap-5">
              <p className="text-[2.8125rem] font-semibold tracking-heading">
                {formatMean(result.mean, 1)}
              </p>
              <div>
                <Badge tone={result.positive ? "success" : "danger"}>
                  {result.positive ? "Ocena pozytywna" : "Ocena negatywna"}
                </Badge>
                <p className="mt-2 text-label text-muted-foreground">Średnia z pięciu ocen</p>
              </div>
            </div>
            <ul className="mt-6 space-y-4">
              {[
                {
                  label: "Średnia co najmniej 5",
                  pass: result.mean !== null && result.mean >= 5,
                },
                {
                  label: "Nie więcej niż jedna ocena 3",
                  pass: result.threes <= 1,
                },
                {
                  label: "Sprawozdanie w terminie",
                  pass: assessment.firstReport === "yes",
                },
                {
                  label: "Egzamin zaliczony / nie dotyczy",
                  pass: assessment.firstExam !== "no",
                },
              ].map(({ label, pass }) => (
                <li key={label} className="flex gap-3 text-body">
                  <Icon
                    name={pass ? "check" : "info"}
                    size={16}
                    className={pass ? "shrink-0 text-success" : "shrink-0 text-warning"}
                  />
                  <span>
                    <span className="sr-only">{pass ? "Spełniono: " : "Nie spełniono: "}</span>
                    {label}
                  </span>
                </li>
              ))}
            </ul>
            <Note className="mt-6 bg-surface text-caption">
              Rozporządzenie PRM z 23.07.2015 r., §§ 9–10. Cztery warunki muszą być spełnione
              jednocześnie.
            </Note>
          </Card>
          <Card className="p-7">
            <h3 className="mb-5 text-sm font-semibold">Warunki pozapunktowe</h3>
            <label>
              <span className="field-label">Egzamin ze służby przygotowawczej</span>
              <select
                className="field"
                value={assessment.firstExam}
                onChange={(event) => {
                  const value = event.target.value;
                  if (value === "yes" || value === "no" || value === "na")
                    update({ firstExam: value });
                }}
              >
                <option value="yes">Zaliczony</option>
                <option value="no">Niezaliczony</option>
                <option value="na">Nie dotyczy</option>
              </select>
            </label>
            <label className="mt-5 block">
              <span className="field-label">Sprawozdanie pracownika</span>
              <select
                className="field"
                value={assessment.firstReport}
                onChange={(event) => {
                  const value = event.target.value;
                  if (value === "yes" || value === "no") update({ firstReport: value });
                }}
              >
                <option value="yes">Złożone w terminie</option>
                <option value="no">Nie / po terminie</option>
              </select>
            </label>
            <Note className="mt-6">
              W demie status egzaminu „Nie dotyczy” wybiera użytkownik; nie weryfikujemy tutaj
              przesłanek zwolnienia.
            </Note>
          </Card>
        </div>
      ) : null}
      <FlowFooter
        onBack={step ? () => update({ firstStep: step - 1 }) : undefined}
        onNext={() => (step === 3 ? router.push("/") : update({ firstStep: step + 1 }))}
        label={step === 3 ? "Wróć do pulpitu" : "Dalej"}
      />
    </div>
  );
}
