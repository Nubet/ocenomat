import { Card, PageHeading } from "@/components/ui/card";
import { Badge, type BadgeTone } from "@/components/ui/badge";

const deadlines: {
  day: string;
  month: string;
  title: string;
  name: string;
  tone: BadgeTone;
}[] = [
  {
    day: "27",
    month: "LIS 2026",
    title: "Rozmowa oceniająca",
    name: "Maria Wiśniewska",
    tone: "warning",
  },
  {
    day: "04",
    month: "GRU 2026",
    title: "Termin sporządzenia oceny",
    name: "Piotr Nowak",
    tone: "primary",
  },
  {
    day: "18",
    month: "GRU 2026",
    title: "Przegląd postępów",
    name: "Jan Kowalski",
    tone: "neutral",
  },
];

export function Deadlines() {
  return (
    <>
      <PageHeading
        eyebrow="Planowanie"
        title="Terminy"
        description="Najbliższe działania wymagające Twojej uwagi."
      />
      <div className="grid gap-4 lg:grid-cols-[1fr_18.75rem]">
        <Card className="p-6 sm:p-8">
          <h2 className="mb-7 text-sm font-semibold">Nadchodzące wydarzenia</h2>
          <div className="ml-3 space-y-9 border-l pl-7">
            {deadlines.map((deadline) => (
              <div key={deadline.name} className="relative">
                <span
                  aria-hidden="true"
                  className="absolute top-1 -left-9 size-4 rounded-full border-3 border-primary bg-surface"
                />
                <div className="flex items-start justify-between gap-3 max-compact:flex-wrap">
                  <div>
                    <p className="text-caption font-semibold text-primary">
                      {deadline.day} {deadline.month}
                    </p>
                    <h3 className="mt-2 text-[0.8125rem] font-semibold">{deadline.title}</h3>
                    <p className="mt-1 text-label text-muted-foreground">{deadline.name}</p>
                  </div>
                  <Badge tone={deadline.tone}>Zaplanowano</Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
        <Card className="h-fit p-6">
          <h2 className="mb-3 text-body font-semibold">Spokojna organizacja</h2>
          <p className="text-label leading-6 text-muted-foreground">
            Każda ocena ma swój etap, termin i zapisane ustalenia. W docelowej wersji będą tu też
            przypomnienia.
          </p>
        </Card>
      </div>
    </>
  );
}
