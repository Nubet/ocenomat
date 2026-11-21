"use server";

import { revalidatePath } from "next/cache";
import { unstable_rethrow } from "next/navigation";
import { requireUser } from "@/features/auth/session";
import { apiRequest } from "@/lib/api/server";
import type { components } from "@/lib/api/schema";
import { assessmentHref, type AssessmentActionState } from "./types";

export async function saveFirstAssessment(
  id: string,
  command: components["schemas"]["FirstUpdate"] | components["schemas"]["FirstDeadlineUpdate"],
  deadlines = false,
): Promise<AssessmentActionState> {
  const user = await requireUser();
  if (!user.roles.includes("MANAGER") || !/^[\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12}$/i.test(id))
    return { error: "Otwórz ocenę prowadzoną przez siebie z listy ocen.", conflict: false };
  try {
    const response = await apiRequest(
      `/api/v1/assessments/${id}/first${deadlines ? "/deadlines" : ""}`,
      {
        method: deadlines ? "POST" : "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(command),
      },
    );
    if (!response.ok)
      return {
        error:
          response.status === 409
            ? "Zapisano nowszą wersję lub zamknięto etap. Otwórz zapisaną ocenę w nowej karcie i porównaj dane."
            : response.status === 422
              ? "Sprawdź kompletność etapu, daty, podstawy zwolnienia oraz uzasadnienie. Potwierdzaj tylko wykonane czynności."
              : "Nie udało się zapisać pierwszej oceny. Sprawdź dostęp i spróbuj ponownie.",
        conflict: response.status === 409,
      };
    const assessment = await response.json();
    revalidatePath(assessmentHref(id));
    revalidatePath("/assessments");
    revalidatePath(`/employees/${assessment.employee_id}`);
    return { error: "", conflict: false, assessment, message: "Pierwsza ocena zapisana." };
  } catch (error) {
    unstable_rethrow(error);
    return {
      error:
        "Nie udało się potwierdzić zapisu. Zachowaj wpisy i sprawdź zapisaną wersję przed ponowieniem.",
      conflict: true,
    };
  }
}
