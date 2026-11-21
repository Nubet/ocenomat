import type { Assessment } from "../model/types";
import type { BadgeTone } from "@/components/ui/badge";

export function assessmentStatus(assessment: Assessment): {
  label: string;
  tone: BadgeTone;
} {
  if (assessment.step === "finished")
    return { label: "Przygotowana", tone: "success" };
  if (assessment.step === "document")
    return { label: "Wymaga formalności", tone: "success" };
  if (assessment.type === "first")
    return { label: "Pierwsza ocena", tone: "primary" };
  if (["saved", "period"].includes(assessment.step))
    return { label: "Trwa okres oceny", tone: "primary" };
  if (["analysis", "criteria"].includes(assessment.step))
    return { label: "Ustalenie kryteriów", tone: "warning" };
  if (assessment.step === "timing")
    return { label: "Ustalenia i terminy", tone: "neutral" };
  if (assessment.step === "setup")
    return { label: "Arkusz do potwierdzenia", tone: "neutral" };
  if (assessment.step === "conversation")
    return { label: "Rozmowa oceniająca", tone: "warning" };
  return { label: "Ocena zachowań", tone: "primary" };
}
