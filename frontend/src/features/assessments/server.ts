import "server-only";

import { cache } from "react";
import { notFound } from "next/navigation";
import { apiRequest } from "@/lib/api/server";
import type { AssessmentRecord } from "./types";
import type { components } from "@/lib/api/schema";

export const getAssessments = cache(async (employeeId?: string): Promise<AssessmentRecord[]> => {
  const query = employeeId ? `?employee_id=${encodeURIComponent(employeeId)}` : "";
  const response = await apiRequest(`/api/v1/assessments${query}`);
  if (!response.ok) throw new Error("Nie można pobrać listy ocen.");
  return response.json() as Promise<AssessmentRecord[]>;
});

export const getAssessment = cache(async (id: string): Promise<AssessmentRecord> => {
  const response = await apiRequest(`/api/v1/assessments/${encodeURIComponent(id)}`);
  if (response.status === 404 || response.status === 422) notFound();
  if (!response.ok) throw new Error("Nie można pobrać oceny.");
  return response.json() as Promise<AssessmentRecord>;
});

export const getAssessmentCatalog = cache(
  async (versionId: string): Promise<components["schemas"]["CatalogResponse"]> => {
    const response = await apiRequest(
      `/api/v1/catalog/criteria?version_id=${encodeURIComponent(versionId)}`,
    );
    if (!response.ok)
      throw new Error("Nie udało się wczytać kryteriów. Spróbuj ponownie za chwilę.");
    return response.json();
  },
);
