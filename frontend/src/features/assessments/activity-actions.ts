"use server";

import { revalidatePath } from "next/cache";
import { unstable_rethrow } from "next/navigation";
import { requireUser } from "@/features/auth/session";
import { apiRequest } from "@/lib/api/server";
import { assessmentHref, type AssessmentActionState, type AssessmentRecord } from "./types";

const uuidPattern = /^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$/i;

export async function saveActivity(
  assessmentId: string,
  previous: AssessmentActionState,
  form: FormData,
): Promise<AssessmentActionState> {
  if (previous.conflict) return previous;
  const user = await requireUser();
  if (!user.roles.includes("MANAGER"))
    return {
      error:
        "Obserwacje i rozmowę zapisuje przełożony prowadzący ocenę. Poproś administratora o sprawdzenie roli i przypisania.",
      conflict: false,
    };

  const operation = form.get("operation");
  const rawRevision = form.get("revision");
  if (
    !uuidPattern.test(assessmentId) ||
    typeof rawRevision !== "string" ||
    !/^[1-9]\d*$/.test(rawRevision) ||
    !Number.isSafeInteger(Number(rawRevision))
  )
    return {
      error: "Nie możemy rozpoznać tego zapisu. Otwórz ocenę ponownie z listy ocen.",
      conflict: false,
    };

  const revision = Number(rawRevision);
  let suffix: string;
  let method: string;
  let body: Record<string, unknown>;
  switch (operation) {
    case "observation":
      suffix = "/observations";
      method = "POST";
      body = {
        revision,
        criterion_id: form.get("criterion_id"),
        text: form.get("text"),
        occurred_on: form.get("observation_date"),
      };
      break;
    case "conversation":
      suffix = "/conversation";
      method = "PUT";
      body = {
        revision,
        agenda: form.get("agenda"),
        strengths: form.get("strengths"),
        growth: form.get("growth"),
        occurred_on: form.get("conversation_date") || null,
      };
      break;
    case "start_period":
    case "confirm_conversation":
      suffix = "/transitions";
      method = "POST";
      body = { revision, action: operation };
      break;
    default:
      return {
        error: "Wybierz zapis obserwacji, notatek lub potwierdzenie czynności.",
        conflict: false,
      };
  }

  let assessment: AssessmentRecord;
  try {
    const response = await apiRequest(`/api/v1/assessments/${assessmentId}${suffix}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const messages: Record<number, string> = {
        403: "Nie możesz zapisać tej oceny. Poproś administratora o sprawdzenie roli i przypisania pracownika.",
        404: "Nie masz już dostępu do tej oceny. Zachowaj swoje notatki i poproś administratora o sprawdzenie przypisania pracownika.",
        409: "Ocena zmieniła się w innej karcie lub ten etap jest już zamknięty. Twoje wpisy pozostają w formularzu. Otwórz zapisaną wersję w nowej karcie i porównaj dane.",
        422:
          operation === "observation"
            ? "Wpisz konkretną obserwację (do 10 000 znaków), wybierz kryterium tej oceny i datę od rozmowy rozpoczynającej do dzisiaj."
            : "Każda notatka może mieć do 10 000 znaków. Data odbytej rozmowy musi przypadać między rozmową rozpoczynającą a dzisiaj. Przed potwierdzeniem zapisz jej datę.",
      };
      return {
        error:
          messages[response.status] ??
          "Nie udało się zapisać danych. Twoje wpisy pozostały w formularzu — spróbuj ponownie za chwilę.",
        conflict: response.status === 409,
      };
    }
    assessment = (await response.json()) as AssessmentRecord;
  } catch (error) {
    unstable_rethrow(error);
    return {
      error:
        "Nie udało się potwierdzić zapisu. Twoje wpisy pozostały w formularzu. Spróbuj ponownie; jeśli zapis się powiódł, otrzymasz informację o nowszej wersji.",
      conflict: false,
    };
  }
  revalidatePath(assessmentHref(assessmentId));
  revalidatePath("/assessments");
  revalidatePath(`/employees/${assessment.employee_id}`);
  const messages = {
    observation: "Obserwacja zapisana. Możesz dodać kolejny przykład.",
    conversation: "Notatki z rozmowy zapisane. Potwierdź rozmowę dopiero po jej odbyciu.",
    start_period: "Okres obserwacji rozpoczęty. Możesz zbierać przykłady i przygotować rozmowę.",
    confirm_conversation: "Rozmowa potwierdzona. Obserwacje i notatki są teraz tylko do odczytu.",
  };
  return { error: "", conflict: false, assessment, message: messages[operation] };
}
