import "server-only";

import { cache } from "react";
import { apiRequest } from "@/lib/api/server";
import type { Monitoring } from "./types";

export const getMonitoring = cache(async (scope: "personal" | "hr"): Promise<Monitoring> => {
  const response = await apiRequest(`/api/v1/monitoring/${scope}`);
  if (!response.ok) throw new Error("Nie udało się pobrać monitoringu ocen.");
  return response.json();
});
