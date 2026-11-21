import { beforeEach, describe, expect, it, vi } from "vitest";

const { client } = vi.hoisted(() => ({
  client: {
    auth: {
      getClaims: vi.fn<() => Promise<object>>(),
      getSession: vi.fn<() => Promise<object>>(),
    },
  },
}));
vi.mock("server-only", () => ({}));
vi.mock("./server", () => ({ createAuthClient: async () => client }));
vi.mock("next/navigation", () => ({
  redirect: (path: string) => {
    throw new Error(`redirect:${path}`);
  },
}));

import { requireUser } from "./session";

describe("protected workspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv("KOMPAS_SUPABASE_URL", "https://auth.example.org");
    vi.stubEnv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test");
    vi.stubEnv("API_BASE_URL", "http://backend:8000");
    client.auth.getClaims.mockResolvedValue({
      data: { claims: { sub: "verified-subject" } },
      error: null,
    });
    client.auth.getSession.mockResolvedValue({
      data: { session: { access_token: "test-only-token" } },
    });
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          Response.json({ id: "test", display_name: "Test manager", roles: ["MANAGER"] }),
        ),
    );
  });

  it("rejects an unverified session before reading or forwarding it", async () => {
    client.auth.getClaims.mockResolvedValue({ data: null, error: { message: "bad signature" } });
    await expect(requireUser()).rejects.toThrow("redirect:/login");
    expect(client.auth.getSession).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("forwards the verified session privately to the backend", async () => {
    expect((await requireUser()).display_name).toBe("Test manager");
    expect(fetch).toHaveBeenCalledWith(
      new URL("http://backend:8000/api/v1/me"),
      expect.objectContaining({
        cache: "no-store",
        headers: { Authorization: "Bearer test-only-token" },
        redirect: "error",
      }),
    );
  });

  it("rejects an inactive local account", async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 401 }));
    await expect(requireUser()).rejects.toThrow("redirect:/login?error=account");
  });

  it("does not fall back to demo identity on API failure", async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 503 }));
    await expect(requireUser()).rejects.toThrow("Nie można pobrać profilu");
  });
});
