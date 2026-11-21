import { activeCompetencies, periodicResult } from "./scoring";
import { steps, type Assessment, type AssessmentStep, type Employee } from "./types";

export function resolveAssessmentStep(
  employee: Employee,
  assessment: Assessment,
  requested?: string | null,
): AssessmentStep {
  const step = steps.find((step) => step === requested) ?? assessment.step;
  if (["rating", "recommendation"].includes(step) && !assessment.conversationDone)
    return "conversation";
  if (step === "recommendation") {
    const list = activeCompetencies(employee, assessment.extra);
    const competency = list[assessment.competencyIndex] ?? list[0];
    if (
      competency.indicators.some(
        (_, index) => assessment.answers[competency.id]?.[index] === undefined,
      )
    )
      return "rating";
  }
  if (
    step === "finished" &&
    (!periodicResult(employee, assessment).complete || !assessment.formal.every(Boolean))
  )
    return "document";
  return step;
}
