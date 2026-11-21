"use server";

import { revalidatePath } from "next/cache";
import { redirect, unstable_rethrow } from "next/navigation";
import { requireUser } from "@/features/auth/session";
import { apiRequest } from "@/lib/api/server";
import { assessmentHref, type AssessmentRecord } from "./types";

const uuidPattern = /^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$/i;

export async function createAssessment(_previous: { error: string }, form: FormData) {
  const user = await requireUser();
  if (!user.roles.includes("MANAGER"))
    return { error: "Ocenę może utworzyć tylko przypisany przełożony." };
  const employeeId = form.get("employee_id");
  const key = form.get("idempotency_key");
  if (
    typeof employeeId !== "string" ||
    !uuidPattern.test(employeeId) ||
    typeof key !== "string" ||
    !uuidPattern.test(key)
  ) {
    return { error: "Wybierz pracownika i spróbuj ponownie." };
  }
  let assessment: AssessmentRecord;
  try {
    const response = await apiRequest("/api/v1/assessments", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": key },
      body: JSON.stringify({ employee_id: employeeId, kind: "periodic" }),
    });
    if (!response.ok) {
      const messages: Record<number, string> = {
        403: "Ocenę może utworzyć tylko przypisany przełożony.",
        404: "Pracownik jest niedostępny albo zmieniło się przypisanie. Odśwież listę.",
        409: "To żądanie dotyczyło innej oceny. Wróć do listy i rozpocznij nową konfigurację.",
        422: "Obecnie dostępna jest tylko ocena okresowa C dla pozostałych stanowisk.",
        503: "Nie można teraz utworzyć oceny. Spróbuj ponownie; wymagany jest katalog kompetencji.",
      };
      return {
        error: messages[response.status] ?? "Nie udało się zapisać oceny. Ponów to samo żądanie.",
      };
    }
    assessment = (await response.json()) as AssessmentRecord;
  } catch (error) {
    unstable_rethrow(error);
    return {
      error: "Nie udało się potwierdzić zapisu. Spróbuj ponownie — żądanie zachowa ten sam klucz.",
    };
  }
  revalidatePath("/assessments");
  revalidatePath(`/employees/${employeeId}`);
  redirect(assessmentHref(assessment.id));
}
