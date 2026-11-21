import "server-only";

import { redirect } from "next/navigation";
import { requireAccessToken } from "@/features/auth/session";

export async function apiRequest(path: string, init: RequestInit = {}): Promise<Response> {
  const token = await requireAccessToken();
  const baseUrl = process.env.API_BASE_URL;
  if (!baseUrl) throw new Error("API_BASE_URL is not configured");
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(new URL(path, baseUrl), {
    ...init,
    headers,
    cache: "no-store",
    signal: init.signal ?? AbortSignal.timeout(8000),
    redirect: "error",
  });
  if (response.status === 401) redirect("/login?error=account");
  return response;
}
