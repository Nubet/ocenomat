"use server";

import { unstable_rethrow } from "next/navigation";
import { apiRequest } from "@/lib/api/server";
import type { components } from "@/lib/api/schema";

type Analysis = components["schemas"]["OspAnalysis"];

export async function analyzeJobDescription(
  assessmentId: string,
): Promise<{ analysis: Analysis } | { error: string }> {
  if (!/^[\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12}$/i.test(assessmentId))
    return { error: "Otwórz zapisaną ocenę z listy ocen." };
  try {
    const response = await apiRequest(
      `/api/v1/ai/assessments/${assessmentId}/job-description-analysis`,
      {
        method: "POST",
        signal: AbortSignal.timeout(130000),
      },
    );
    if (!response.ok)
      return {
        error:
          response.status === 404
            ? "Nie masz dostępu do tej oceny lub wybranego OSP."
            : response.status === 409
              ? "Kontekst oceny zmienił się podczas analizy. Otwórz zapisaną wersję i ponów analizę."
              : response.status === 422
                ? "Nie można bezpiecznie odczytać wybranego OSP. Sprawdź oryginał dokumentu."
                : "Analiza OSP jest chwilowo niedostępna lub przekroczono czas oczekiwania. Spróbuj ponownie później.",
      };
    return { analysis: (await response.json()) as Analysis };
  } catch (error) {
    unstable_rethrow(error);
    return { error: "Nie udało się połączyć z analizą OSP. Spróbuj ponownie później." };
  }
}
