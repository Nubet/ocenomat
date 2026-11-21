import { Card } from "@/components/ui/card";
import { Button, ButtonLink } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { useAssessment } from "./assessment-context";

export function Completion() {
  const { go } = useAssessment();
  return (
    <div className="mx-auto max-w-[43.125rem] py-12">
      <Card className="p-10 text-center sm:p-14">
        <span className="mx-auto mb-6 grid size-16 place-items-center rounded-[1.1875rem] bg-success-muted text-success">
          <Icon name="check" size={32} />
        </span>
        <p className="eyebrow mb-3">Proces demonstracyjny</p>
        <h1 className="text-[1.6875rem] font-semibold tracking-heading">
          Ocena przygotowana
        </h1>
        <p className="mx-auto mt-4 max-w-[27.5rem] text-body leading-6 text-muted-foreground">
          Wszystkie czynności w makiecie zostały potwierdzone. Możesz ponownie
          otworzyć podgląd lub wrócić do listy ocen.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Button onClick={() => go("document")}>
            <Icon name="file" size={16} />
            Zobacz dokument
          </Button>
          <ButtonLink href="/" variant="primary">
            Wróć na pulpit
          </ButtonLink>
        </div>
        <p className="mt-8 text-caption text-subtle-foreground">
          To zakończenie prezentacji interfejsu, nie potwierdzenie prawnego
          zakończenia oceny.
        </p>
      </Card>
    </div>
  );
}
