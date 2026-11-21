"use server";

import { revalidatePath } from "next/cache";
import { unstable_rethrow } from "next/navigation";
import { requireUser } from "@/features/auth/session";
import { apiRequest } from "@/lib/api/server";
import { assessmentHref } from "./types";
import type { DocumentActionState } from "./document-types";

const uuidPattern = /^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$/i;

export async function saveDocument(
  assessmentId: string,
  previous: DocumentActionState,
  form: FormData,
): Promise<DocumentActionState> {
  if (previous.conflict) return previous;
  const user = await requireUser();
  if (!user.roles.includes("MANAGER"))
    return { error: "Dokumenty przygotowuje przełożony prowadzący ocenę.", conflict: false };
  const rawRevision = form.get("revision");
  if (
    !uuidPattern.test(assessmentId) ||
    typeof rawRevision !== "string" ||
    !/^[1-9]\d*$/.test(rawRevision) ||
    !Number.isSafeInteger(Number(rawRevision))
  )
    return { error: "Otwórz ocenę ponownie z listy ocen.", conflict: false };
  const revision = Number(rawRevision);
  const base = `/api/v1/assessments/${assessmentId}`;
  const operation = form.get("operation");
  let path: string;
  let init: RequestInit;
  if (operation === "upload") {
    const file = form.get("file");
    const kind = form.get("kind");
    if (
      !(file instanceof File) ||
      file.size < 1 ||
      file.size > 10 * 1024 * 1024 ||
      (kind !== "osp" && kind !== "attachment")
    )
      return { error: "Wybierz plik PDF lub DOCX o rozmiarze do 10 MiB.", conflict: false };
    path = `/documents?${new URLSearchParams({ revision: String(revision), filename: file.name, kind })}`;
    init = {
      method: "POST",
      headers: { "Content-Type": file.type || "application/octet-stream" },
      body: file,
    };
  } else if (operation === "select_osp") {
    const id = form.get("job_description_id");
    if (typeof id !== "string" || !uuidPattern.test(id))
      return { error: "Wybierz wersję OSP pracownika.", conflict: false };
    path = "/documents/job-descriptions/select";
    init = {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ revision, job_description_id: id }),
    };
  } else if (operation === "pdf") {
    path = "/documents/periodic-pdf";
    init = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        revision,
        office_name: form.get("office_name"),
        assessor_department: form.get("assessor_department"),
        assessor_position: form.get("assessor_position"),
        period_end: form.get("period_end"),
        civil_service_status: form.get("civil_service_status"),
        no_promotion_request: form.get("no_promotion_request") === "on",
        previous_assessment:
          form.get("civil_service_status") === "official" && form.get("previous_exists") === "yes"
            ? {
                outcome: form.get("previous_outcome"),
                level: Number(form.get("previous_level")),
                assessed_on: form.get("previous_date"),
              }
            : null,
      }),
    };
  } else return { error: "Wybierz operację dokumentu.", conflict: false };
  try {
    const response = await apiRequest(base + path, init);
    if (!response.ok) {
      const messages: Record<number, string> = {
        404: "Nie masz dostępu do tej oceny lub wersji OSP. Poproś administratora o sprawdzenie przypisania.",
        409: "Ocena lub dokument zmieniły się. Otwórz zapisaną wersję i sprawdź listę plików przed kolejnym zapisem.",
        413: "Plik przekracza limit 10 MiB.",
        422: "Sprawdź dane dokumentu: wymagane pola, daty i status zatrudnienia. Pliki muszą być poprawnymi PDF/DOCX bez szyfrowania i makr. Używaj znaków obsługiwanych przez dokument, np. polskich liter.",
      };
      return {
        error:
          messages[response.status] ??
          "Nie udało się przygotować dokumentu. Spróbuj ponownie za chwilę.",
        conflict: response.status === 409,
      };
    }
    const results = await Promise.all([
      apiRequest(base),
      apiRequest(base + "/documents"),
      apiRequest(base + "/documents/job-descriptions"),
    ]);
    if (results.some((result) => !result.ok))
      return {
        error:
          "Operacja została wykonana, ale nie udało się odświeżyć listy. Otwórz zapisaną wersję przed kolejnym zapisem.",
        conflict: true,
      };
    const [assessment, files, descriptions] = await Promise.all(
      results.map((result) => result.json()),
    );
    revalidatePath(assessmentHref(assessmentId));
    return {
      error: "",
      conflict: false,
      assessment,
      files,
      descriptions,
      message:
        operation === "pdf"
          ? `Arkusz ${assessment.form} jest gotowy do pobrania. Nie jest podpisany ani doręczony.`
          : "Dokument zapisany. Wersję OSP można zmienić tylko przed potwierdzeniem ustaleń.",
    };
  } catch (error) {
    unstable_rethrow(error);
    return {
      error:
        "Nie udało się potwierdzić operacji. Zachowaj wpisy i otwórz zapisaną wersję, aby sprawdzić listę plików przed ponowieniem.",
      conflict: true,
    };
  }
}
