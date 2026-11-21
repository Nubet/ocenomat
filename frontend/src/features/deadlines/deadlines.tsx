import Link from "next/link";
import { Card, PageHeading } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { assessmentHref } from "@/features/assessments/types";
import { deadlineLabels, monitoringDate, type Monitoring } from "@/features/monitoring/types";

export function Deadlines({ monitoring }: { monitoring: Monitoring }) {
  return (
    <>
      <PageHeading
        eyebrow="Planowanie"
        title="Terminy"
        description="Zapisane terminy Twoich niezakończonych ocen, w tym zaległości."
      />
      <div className="grid gap-4 lg:grid-cols-[1fr_18.75rem]">
        <Card className="p-6 sm:p-8">
          <h2 className="mb-7 text-sm font-semibold">Zaplanowane działania</h2>
          <div className="ml-3 space-y-9 border-l pl-7">
            {monitoring.deadlines.map((deadline) => (
              <div key={`${deadline.assessment_id}:${deadline.kind}`} className="relative">
                <span
                  aria-hidden="true"
                  className="absolute top-1 -left-9 size-4 rounded-full border-3 border-primary bg-surface"
                />
                <div className="flex items-start justify-between gap-3 max-compact:flex-wrap">
                  <div>
                    <p className="text-caption font-semibold text-primary">
                      {monitoringDate(deadline.due_on)}
                    </p>
                    <h3 className="mt-2 text-[0.8125rem] font-semibold">
                      <Link href={assessmentHref(deadline.assessment_id)}>
                        {deadlineLabels[deadline.kind]}
                      </Link>
                    </h3>
                    <p className="mt-1 text-label text-muted-foreground">
                      {deadline.employee_name}
                    </p>
                  </div>
                  <Badge tone={deadline.overdue || deadline.due_soon ? "warning" : "primary"}>
                    {deadline.overdue
                      ? "Po terminie"
                      : deadline.due_soon
                        ? "Bliski termin"
                        : "Zaplanowano"}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
          {monitoring.deadlines.length === 0 ? (
            <p className="text-body text-muted-foreground">
              Brak zapisanych terminów aktywnych ocen.
            </p>
          ) : null}
        </Card>
        <Card className="h-fit p-6">
          <h2 className="mb-3 text-body font-semibold">Spokojna organizacja</h2>
          <p className="text-label leading-6 text-muted-foreground">
            Stan na {monitoringDate(monitoring.as_of)}. Bliski termin oznacza najbliższe{" "}
            {monitoring.attention_window_days} dni. Przypomnienia wysłane przez HR znajdziesz na
            pulpicie.
          </p>
        </Card>
      </div>
    </>
  );
}
