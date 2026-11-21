import type { components } from "@/lib/api/schema";

export type AssessmentRecord = components["schemas"]["AssessmentResponse"];

export type AssessmentActionState = {
  error: string;
  conflict: boolean;
  assessment?: AssessmentRecord;
  message?: string;
};

export const assessmentStatusLabels: Record<AssessmentRecord["status"], string> = {
  draft: "Szkic",
  criteria_agreed: "Uzgodnione kryteria",
  in_progress: "W toku",
  evaluation: "Ocena zachowań",
  completed: "Zakończona",
};

export function assessmentHref(id: string) {
  return `/assessments/${encodeURIComponent(id)}`;
}
