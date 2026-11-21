"use server";

import { unstable_rethrow } from "next/navigation";
import { apiRequest } from "@/lib/api/server";
import type { AssistantActionResult, AssistantAnswer, AssistantRequest } from "./types";

export async function askAssistant(data: AssistantRequest): Promise<AssistantActionResult> {
  if (
    !data ||
    typeof data.question !== "string" ||
    !data.question.trim() ||
    data.question.length > 1000 ||
    !["formal", "conversation"].includes(data.mode ?? "formal") ||
    !["first", "periodic", "unspecified"].includes(data.assessment_kind ?? "unspecified") ||
    (data.assessment_id != null &&
      !/^[\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12}$/i.test(data.assessment_id))
  )
    return { error: "Wpisz pytanie do 1000 znaków i wybierz właściwy zakres." };
  try {
    const response = await apiRequest("/api/v1/ai/assistant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(130000),
      body: JSON.stringify({
        question: data.question.trim(),
        mode: data.mode ?? "formal",
        assessment_kind: data.assessment_kind ?? "unspecified",
        assessment_id: data.assessment_id ?? null,
        task: data.task === "assessment_result" ? "assessment_result" : "question",
      }),
    });
    if (!response.ok) {
      const messages: Record<number, string> = {
        404: "Nie masz dostępu do tej oceny lub ocena nie istnieje.",
        422: "Sprawdź pytanie i zgodność wybranego zakresu z oceną.",
        429: "Dostawca AI ograniczył liczbę zapytań. Spróbuj ponownie później.",
        502: "Dostawca AI zwrócił nieprawidłową odpowiedź. Spróbuj ponownie.",
        503: "Asystent jest chwilowo niedostępny. To błąd usługi, nie brak wiedzy w źródłach.",
        504: "Przekroczono czas oczekiwania na AI. Twoje pytanie pozostało w formularzu.",
      };
      return {
        error: messages[response.status] ?? "Nie udało się uzyskać odpowiedzi. Spróbuj ponownie.",
      };
    }
    return { answer: (await response.json()) as AssistantAnswer };
  } catch (error) {
    unstable_rethrow(error);
    return {
      error:
        "Nie udało się połączyć z asystentem lub minął czas oczekiwania. Pytanie pozostało w formularzu.",
    };
  }
}
