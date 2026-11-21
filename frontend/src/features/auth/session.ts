import "server-only";

import { cache } from "react";
import { redirect } from "next/navigation";
import type { components } from "@/lib/api/schema";
import { authConfig } from "./config";
import { createAuthClient } from "./server";

export type WorkspaceUser = components["schemas"]["UserResponse"];

export async function fetchProfile(accessToken: string): Promise<Response> {
  const baseUrl = process.env.API_BASE_URL;
  if (!baseUrl) throw new Error("API_BASE_URL is not configured");
  return fetch(new URL("/api/v1/me", baseUrl), {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
    signal: AbortSignal.timeout(8000),
    redirect: "error",
  });
}

export const requireUser = cache(async (): Promise<WorkspaceUser> => {
  if (!authConfig()) redirect("/login");
  const client = await createAuthClient();
  const { data, error } = await client.auth.getClaims();
  if (error || !data?.claims.sub) redirect("/login");
  const { data: sessionData } = await client.auth.getSession();
  if (!sessionData.session) redirect("/login");
  const response = await fetchProfile(sessionData.session.access_token);
  if (response.status === 401 || response.status === 403) redirect("/login?error=account");
  if (!response.ok) throw new Error("Nie można pobrać profilu użytkownika.");
  return response.json() as Promise<WorkspaceUser>;
});
