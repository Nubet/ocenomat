import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("@/features/auth/session", () => ({ requireAccessToken: vi.fn<() => Promise<string>>() }));
vi.mock("next/navigation", () => ({
  redirect: (path: string) => {
    throw new Error(`redirect:${path}`);
  },
}));

import { requireAccessToken } from "@/features/auth/session";
import { apiRequest } from "./server";

describe("server API transport", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv("API_BASE_URL", "http://backend:8000");
    vi.mocked(requireAccessToken).mockResolvedValue("verified-token");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json({})));
  });

  it("retains idempotency headers and forces private authenticated requests", async () => {
    await apiRequest("/api/v1/assessments", {
      method: "POST",
      headers: { "Idempotency-Key": "request-key", "Content-Type": "application/json" },
      body: "{}",
    });
    const options = vi.mocked(fetch).mock.calls[0]?.[1];
    const headers = new Headers(options?.headers);
    expect(headers.get("Authorization")).toBe("Bearer verified-token");
    expect(headers.get("Idempotency-Key")).toBe("request-key");
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(options).toEqual(
      expect.objectContaining({ cache: "no-store", redirect: "error", method: "POST", body: "{}" }),
    );
  });

  it("redirects rejected sessions instead of letting callers show stale data", async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 401 }));
    await expect(apiRequest("/api/v1/assessments")).rejects.toThrow(
      "redirect:/login?error=account",
    );
  });

  it("retains a server-supplied timeout signal for AI requests", async () => {
    const signal = AbortSignal.timeout(130000);
    await apiRequest("/api/v1/ai/assistant", { signal });
    expect(vi.mocked(fetch).mock.calls[0]?.[1]?.signal).toBe(signal);
  });
});
