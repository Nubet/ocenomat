"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Icon } from "@/components/ui/icon";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import { assessmentHref } from "../data/employees";
import type { EmployeeId } from "../model/types";

export function NewAssessmentButton({
  employeeId = "jan",
  compact = false,
}: {
  employeeId?: EmployeeId;
  compact?: boolean;
}) {
  const { state, startAssessment } = useWorkspace();
  const router = useRouter();
  const [confirm, setConfirm] = useState(false);
  function start() {
    startAssessment(employeeId);
    setConfirm(false);
    router.push(assessmentHref(employeeId, "setup"));
  }
  return (
    <>
      <Button
        variant={compact ? "ghost" : "primary"}
        onClick={() => {
          if (state.assessments[employeeId].step !== "setup") setConfirm(true);
          else start();
        }}
      >
        <Icon name="plus" size={16} />
        Nowa ocena
      </Button>
      {confirm ? (
        <Dialog title="Rozpocząć nową ocenę?" onClose={() => setConfirm(false)}>
          <div className="p-6">
            <p className="text-body leading-6 text-muted-foreground">
              Nowa ocena zastąpi bieżący proces tej osoby zapisany w tej
              przeglądarce. Dotychczasowe notatki i oceny zostaną usunięte.
            </p>
            <div className="mt-6 flex flex-wrap justify-end gap-2">
              <Button
                onClick={() => {
                  setConfirm(false);
                  router.push(assessmentHref(employeeId));
                }}
              >
                Wróć do bieżącej oceny
              </Button>
              <Button variant="primary" onClick={start}>
                Rozpocznij nową ocenę
              </Button>
            </div>
          </div>
        </Dialog>
      ) : null}
    </>
  );
}
