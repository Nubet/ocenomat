"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useWorkspace } from "@/features/workspace/workspace-provider";
import { assessmentHref } from "./data/employees";
import { resolveAssessmentStep } from "./model/navigation";
import type { AssessmentStep, Employee } from "./model/types";
import { AssessmentContext } from "./components/assessment-context";
import { Setup } from "./components/setup";
import { Criteria, PositionAnalysis } from "./components/criteria";
import { Timing, TimingSaved } from "./components/timing";
import { ObservationJournal } from "./components/observation-journal";
import { Conversation } from "./components/conversation";
import { BehavioralRating } from "./components/behavioral-rating";
import { Recommendation } from "./components/recommendation";
import { Summary } from "./components/summary";
import { AssessmentDocument } from "./components/assessment-document";
import { Completion } from "./components/completion";
import { FirstAssessment } from "./components/first-assessment";

export function AssessmentFlow({
  employee,
  requestedStep,
}: {
  employee: Employee;
  requestedStep?: AssessmentStep;
}) {
  const { state, ready, updateAssessment, notify } = useWorkspace();
  const router = useRouter();
  const assessment = state.assessments[employee.id];
  const step = resolveAssessmentStep(employee, assessment, requestedStep);

  useEffect(() => {
    if (ready) document.getElementById("main-content")?.focus({ preventScroll: true });
  }, [step, ready]);

  if (!ready)
    return (
      <output className="block py-10 text-body text-muted-foreground">
        Wczytywanie zapisanej oceny…
      </output>
    );

  function go(next: AssessmentStep) {
    updateAssessment(employee.id, { step: next });
    router.push(assessmentHref(employee.id, next));
  }

  const screens = {
    setup: <Setup />,
    analysis: <PositionAnalysis />,
    criteria: <Criteria />,
    timing: <Timing />,
    saved: <TimingSaved />,
    period: <ObservationJournal />,
    conversation: <Conversation />,
    rating: <BehavioralRating />,
    recommendation: <Recommendation />,
    summary: <Summary />,
    document: <AssessmentDocument />,
    finished: <Completion />,
    first: <FirstAssessment />,
  };

  return (
    <AssessmentContext.Provider
      value={{
        employee,
        assessment,
        step,
        go,
        update: (patch) => updateAssessment(employee.id, patch),
        notify,
      }}
    >
      {screens[step]}
    </AssessmentContext.Provider>
  );
}
