"use client";

import { createContext, useContext } from "react";
import type { Assessment, AssessmentStep, Employee } from "../model/types";

export interface AssessmentContextValue {
  employee: Employee;
  assessment: Assessment;
  step: AssessmentStep;
  update: (
    patch: Partial<Assessment> | ((assessment: Assessment) => Assessment),
  ) => void;
  go: (step: AssessmentStep) => void;
  notify: (message: string) => void;
}

export const AssessmentContext = createContext<AssessmentContextValue | null>(
  null,
);

export function useAssessment() {
  const context = useContext(AssessmentContext);
  if (!context) throw new Error("AssessmentContext is required.");
  return context;
}
