import type { AssistantMode } from "./types";

export function assistantSuggestions(mode: AssistantMode, context: string) {
  if (mode === "conversation")
    return [
      "Jakie pytania pomogą omówić obowiązki i oczekiwania?",
      "Jak przygotować rozmowę oceniającą na podstawie przepisów?",
    ];
  if (context === "first")
    return ["Jaka jest skala pierwszej oceny?", "Jakie są warunki pozytywnej pierwszej oceny?"];
  return [
    "Ile kryteriów dodatkowych można wybrać?",
    "Jakie kryteria są obowiązkowe dla arkusza C?",
    "Jakie są warunki pozytywnej oceny okresowej?",
  ];
}
