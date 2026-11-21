"use server";

import { revalidatePath } from "next/cache";
import { redirect, unstable_rethrow } from "next/navigation";
import { requireUser } from "@/features/auth/session";
import { apiRequest } from "@/lib/api/server";
import { assessmentHref, type AssessmentRecord, type AssessmentActionState } from "./types";

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
        403: "Nie możesz rozpocząć tej oceny. Poproś administratora o sprawdzenie roli przełożonego i przypisania pracownika.",
        404: "Przypisanie pracownika mogło się zmienić. Wróć do listy pracowników. Jeśli brakuje tej osoby, poproś administratora o sprawdzenie przypisania.",
        409: "Nie możemy rozpocząć tej oceny z tego formularza. Sprawdź listę ocen — jeśli jej tam nie ma, wybierz Nowa ocena.",
        422: "Możesz rozpocząć ocenę okresową B lub C. Arkusz A dla kierownika urzędu nie jest jeszcze obsługiwany.",
        503: "Nie udało się rozpocząć oceny. Spróbuj ponownie za chwilę. Jeśli problem się powtarza, poproś administratora o sprawdzenie katalogu kompetencji.",
      };
      return {
        error:
          messages[response.status] ??
          "Nie udało się zapisać oceny. Spróbuj ponownie, pozostając w tym formularzu.",
      };
    }
    assessment = (await response.json()) as AssessmentRecord;
  } catch (error) {
    unstable_rethrow(error);
    return {
      error:
        "Nie udało się potwierdzić zapisu. Spróbuj ponownie w tym formularzu — nie utworzymy drugiej kopii tej samej oceny.",
    };
  }
  revalidatePath("/assessments");
  revalidatePath(`/employees/${employeeId}`);
  redirect(assessmentHref(assessment.id));
}

export async function saveArrangements(
  assessmentId: string,
  _previous: AssessmentActionState,
  form: FormData,
): Promise<AssessmentActionState> {
  const user = await requireUser();
  if (!user.roles.includes("MANAGER"))
    return {
      error:
        "Ustalenia zapisuje przełożony prowadzący ocenę. Jeśli to Twoje zadanie, poproś administratora o sprawdzenie roli i przypisania pracownika.",
      conflict: false,
    };
  const operation = form.get("operation");
  const rawRevision = form.get("revision");
  if (
    !uuidPattern.test(assessmentId) ||
    typeof rawRevision !== "string" ||
    !/^[1-9]\d*$/.test(rawRevision) ||
    !Number.isSafeInteger(Number(rawRevision)) ||
    !["criteria", "dates", "agree"].includes(String(operation))
  ) {
    return {
      error: "Nie możemy rozpoznać tego zapisu. Otwórz ocenę ponownie z listy ocen.",
      conflict: false,
    };
  }
  const revision = Number(rawRevision);
  const additional = form.getAll("additional");
  if (
    operation === "criteria" &&
    (additional.length > 3 ||
      additional.some((id) => typeof id !== "string" || !uuidPattern.test(id)))
  ) {
    return {
      error:
        "Wybierz najwyżej trzy dodatkowe kryteria i uzasadnij każde z nich obowiązkami pracownika.",
      conflict: false,
    };
  }
  const body =
    operation === "criteria"
      ? {
          revision,
          additional: additional.map((id) => ({
            criterion_id: id,
            justification: form.get(`reason:${id}`),
          })),
        }
      : operation === "dates"
        ? {
            revision,
            date_talk: form.get("date_talk"),
            date_assessment: form.get("date_assessment"),
            duties_discussed: form.get("duties_discussed") === "on",
            expectations_discussed: form.get("expectations_discussed") === "on",
            arrangements_shared: form.get("arrangements_shared") === "on",
          }
        : { revision, action: "agree_criteria" };
  let assessment: AssessmentRecord;
  try {
    const response = await apiRequest(
      `/api/v1/assessments/${assessmentId}${operation === "criteria" ? "/criteria" : operation === "agree" ? "/transitions" : ""}`,
      {
        method: operation === "criteria" ? "PUT" : operation === "agree" ? "POST" : "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!response.ok) {
      const messages: Record<number, string> = {
        403: "Nie możesz zapisać tej oceny. Poproś administratora o sprawdzenie roli i przypisania pracownika.",
        404: "Nie masz już dostępu do tej oceny. Zachowaj swoje notatki i poproś administratora o sprawdzenie przypisania pracownika.",
        409: "W innej karcie zapisano zmiany lub potwierdzono już ustalenia. Twoje zmiany pozostają w formularzu. Otwórz zapisaną wersję w nowej karcie i porównaj dane przed dalszą pracą.",
        422:
          operation === "criteria"
            ? "Wybierz do trzech różnych kryteriów dodatkowych. Przy każdym wpisz uzasadnienie związane z obowiązkami pracownika (do 4000 znaków)."
            : operation === "dates"
              ? "Sprawdź obie daty: termin oceny nie może poprzedzać rozmowy. Czynności potwierdzaj tylko po rozmowie, która już się odbyła."
              : "Najpierw zapisz kryteria i terminy, a następnie zaznacz wszystkie wykonane czynności z rozmowy.",
      };
      return {
        error:
          messages[response.status] ??
          "Nie udało się zapisać ustaleń. Twoje zmiany pozostały w formularzu — spróbuj ponownie za chwilę.",
        conflict: response.status === 409,
      };
    }
    assessment = (await response.json()) as AssessmentRecord;
  } catch (error) {
    unstable_rethrow(error);
    return {
      error:
        "Nie udało się potwierdzić zapisu. Zachowaliśmy Twoje wpisy. Spróbuj ponownie; jeśli zapis się powiódł, zobaczysz informację o nowszej wersji.",
      conflict: false,
    };
  }
  revalidatePath(assessmentHref(assessmentId));
  revalidatePath("/assessments");
  revalidatePath(`/employees/${assessment.employee_id}`);
  return {
    error: "",
    conflict: false,
    assessment,
    message:
      operation === "criteria"
        ? "Kryteria zapisane. Teraz uzupełnij terminy i czynności z rozmowy."
        : operation === "dates"
          ? "Terminy i czynności zapisane. Jeśli rozmowa jest zakończona, potwierdź ustalenia."
          : "Ustalenia potwierdzone. Znajdziesz je ponownie na liście ocen.",
  };
}
