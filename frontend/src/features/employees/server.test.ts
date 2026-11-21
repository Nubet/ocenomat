import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("@/features/auth/session", () => ({ requireAccessToken: vi.fn<() => Promise<string>>() }));
vi.mock("next/navigation", () => ({
  redirect: (path: string) => {
    throw new Error(`redirect:${path}`);
  },
  notFound: () => {
    throw new Error("not-found");
  },
}));

import { requireAccessToken } from "@/features/auth/session";
import { getEmployee, getEmployees } from "./server";

describe("authorized employees", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv("API_BASE_URL", "http://backend:8000");
    vi.mocked(requireAccessToken).mockResolvedValue("test-token");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json([])));
  });

  it("keeps an empty authorized list empty instead of inserting demo records", async () => {
    expect(await getEmployees()).toEqual([]);
    expect(fetch).toHaveBeenCalledWith(
      new URL("http://backend:8000/api/v1/employees"),
      expect.objectContaining({
        headers: expect.any(Headers),
        cache: "no-store",
        redirect: "error",
      }),
    );
    expect(new Headers(vi.mocked(fetch).mock.calls[0]?.[1]?.headers).get("Authorization")).toBe(
      "Bearer test-token",
    );
  });

  it("does not send a request without a verified session", async () => {
    vi.mocked(requireAccessToken).mockRejectedValue(new Error("redirect:/login"));
    await expect(getEmployees()).rejects.toThrow("redirect:/login");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("redirects to login when the API rejects a session", async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 401 }));
    await expect(getEmployees()).rejects.toThrow("redirect:/login?error=account");
  });

  it.each([404, 422])(
    "does not reveal missing or inaccessible employee details (%s)",
    async (status) => {
      vi.mocked(fetch).mockResolvedValue(new Response(null, { status }));
      await expect(getEmployee("unknown-id")).rejects.toThrow("not-found");
    },
  );

  it.each([403, 500, 503])(
    "shows an error rather than demo records or an empty list (%s)",
    async (status) => {
      vi.mocked(fetch).mockResolvedValue(new Response(null, { status }));
      await expect(getEmployees()).rejects.toThrow("Nie można pobrać danych pracowników");
    },
  );
});
