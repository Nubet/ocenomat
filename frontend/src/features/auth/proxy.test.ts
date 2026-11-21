import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import type { CookieMethodsServer } from "@supabase/ssr";

const { createClient } = vi.hoisted(() => ({
  createClient:
    vi.fn<
      (url: string, key: string, options: { cookies: Required<CookieMethodsServer> }) => unknown
    >(),
}));
vi.mock("server-only", () => ({}));
vi.mock("@supabase/ssr", () => ({ createServerClient: createClient }));

import { proxy } from "@/proxy";
import { authConfig } from "./config";

describe("session refresh proxy", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  it("copies refreshed cookies and cache headers to request and response", async () => {
    vi.stubEnv("KOMPAS_SUPABASE_URL", "https://auth.example.org");
    vi.stubEnv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test");
    createClient.mockImplementation((_url, _key, options) => ({
      auth: {
        getClaims: async () => {
          options.cookies.setAll(
            [
              {
                name: "sb-test-auth-token",
                value: "refreshed-test-value",
                options: { httpOnly: true, sameSite: "lax" },
              },
            ],
            { "Cache-Control": "no-store", Pragma: "no-cache", Expires: "0" },
          );
          return { data: { claims: { sub: "test" } }, error: null };
        },
      },
    }));
    const request = new NextRequest("http://localhost/");
    const response = await proxy(request);
    expect(request.cookies.get("sb-test-auth-token")?.value).toBe("refreshed-test-value");
    expect(response.cookies.get("sb-test-auth-token")?.value).toBe("refreshed-test-value");
    expect(response.cookies.get("sb-test-auth-token")?.httpOnly).toBe(true);
    expect(response.headers.get("cache-control")).toBe("private, no-store");
    expect(response.headers.get("pragma")).toBe("no-cache");
  });

  it("leaves auth disabled when unconfigured without creating a demo session", async () => {
    vi.stubEnv("KOMPAS_SUPABASE_URL", "");
    const response = await proxy(new NextRequest("http://localhost/login"));
    expect(response.cookies.getAll()).toEqual([]);
    expect(response.headers.get("cache-control")).toBe("private, no-store");
    expect(createClient).not.toHaveBeenCalled();
  });

  it("rejects a secret key in the publishable-key setting", () => {
    vi.stubEnv("KOMPAS_SUPABASE_URL", "https://auth.example.org");
    vi.stubEnv("SUPABASE_PUBLISHABLE_KEY", "sb_secret_test");
    expect(authConfig).toThrow("Invalid Supabase");
  });
});
