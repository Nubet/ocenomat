"use server";

import { unstable_rethrow } from "next/navigation";
import { apiRequest } from "@/lib/api/server";
import type { AssistantActionResult, AssistantAnswer, AssistantRequest } from "./types";
import type { AssessmentRecord } from "@/features/assessments/types";

export async function assistantAssessments() {
  try {
    const response = await apiRequest("/api/v1/assessments");
    if (!response.ok) return { error: "Nie udało się pobrać dostępnych ocen." };
    const assessments = (await response.json()) as AssessmentRecord[];
    return {
      assessments: assessments.map((item) => ({
        id: item.id,
        name: item.employee_snapshot.name,
        kind: item.kind,
        form: item.form,
        status: item.status,
        created_at: item.created_at,
        observations: item.observations.length,
        ratings: item.ratings.filter((rating) => rating.score != null).length,
        notes: Boolean(
          item.conversation?.agenda ||
          item.conversation?.strengths ||
          item.conversation?.growth ||
          item.summary?.development_conclusions ||
          item.first?.conversation_notes ||
          item.first?.report_tasks ||
          item.first?.report_problems ||
          item.first?.report_learning ||
          item.first?.report_conclusions,
        ),
      })),
    };
  } catch (error) {
    unstable_rethrow(error);
    return { error: "Nie udało się pobrać dostępnych ocen." };
  }
}

export async function askAssistant(data: AssistantRequest): Promise<AssistantActionResult> {
  if (
    !data ||
    typeof data.question !== "string" ||
    !data.question.trim() ||
    data.question.length > 1000 ||
    !["formal", "conversation"].includes(data.mode ?? "formal") ||
    !["first", "periodic", "unspecified"].includes(data.assessment_kind ?? "unspecified") ||
    (data.history != null &&
      (!Array.isArray(data.history) ||
        data.history.length > 4 ||
        data.history.some(
          (turn) =>
            typeof turn.question !== "string" ||
            !turn.question.trim() ||
            turn.question.length > 1000 ||
            typeof turn.answer !== "string" ||
            !turn.answer.trim() ||
            turn.answer.length > 4000,
        ))) ||
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
        history: data.mode === "conversation" && data.assessment_id ? (data.history ?? []) : [],
      }),
    });
    if (!response.ok) {
      const messages: Record<number, string> = {
        404: "Nie masz dostępu do tej oceny lub ocena nie istnieje.",
        409: "Ocena zmieniła się podczas przygotowywania odpowiedzi. Spróbuj ponownie.",
        422: "Sprawdź pytanie i zgodność wybranego zakresu z oceną.",
        429: "Dostawca AI ograniczył liczbę zapytań. Spróbuj ponownie później.",
        502: "Dostawca AI zwrócił nieprawidłową odpowiedź. Spróbuj ponownie.",
        503: "Asystent jest chwilowo niedostępny. To błąd usługi, nie brak wiedzy w źródłach.",
        504: "Przekroczono czas oczekiwania na AI. Twoje pytanie pozostało w formularzu.",
      };
      return {
        error: messages[response.status] ?? "Nie udało się uzyskać odpowiedzi. Spróbuj ponownie.",
        accessLost: response.status === 404 && Boolean(data.assessment_id),
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
