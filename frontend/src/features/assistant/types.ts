import type { components } from "@/lib/api/schema";

export type AssistantRequest = components["schemas"]["AssistantRequest"];
export type AssistantAnswer = components["schemas"]["AssistantResponse"];
export type AssistantCitation = components["schemas"]["Citation"];
export type AssistantMode = AssistantRequest["mode"];
export type AssistantActionResult = { answer: AssistantAnswer } | { error: string };

export function assessmentContext(pathname: string): string | undefined {
  return pathname.match(/^\/assessments\/([\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12})(?:\/|$)/i)?.[1];
}
