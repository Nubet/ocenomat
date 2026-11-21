"use server";

import { revalidatePath } from "next/cache";
import { requireUser } from "@/features/auth/session";
import { apiRequest } from "@/lib/api/server";

export async function sendReminder(assessmentId: string, key: string): Promise<string | null> {
  const user = await requireUser();
  if (!user.roles.includes("HR")) return "Tylko HR może wysyłać przypomnienia.";
  let response: Response;
  try {
    response = await apiRequest(
      `/api/v1/monitoring/hr/${encodeURIComponent(assessmentId)}/reminders`,
      { method: "POST", headers: { "Idempotency-Key": key } },
    );
  } catch {
    return "Nie potwierdzono dostarczenia. Ponów próbę, aby sprawdzić ten sam zapis.";
  }
  if (response.status === 409)
    return "Proces jest zakończony lub prowadzący nie ma już aktywnego przypisania i uprawnień. Odśwież widok.";
  if (!response.ok) return "Nie potwierdzono dostarczenia przypomnienia. Ponów próbę.";
  revalidatePath("/hr");
  revalidatePath("/");
  return null;
}
