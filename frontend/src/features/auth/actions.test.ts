import { beforeEach, describe, expect, it, vi } from "vitest";

const { client, profile } = vi.hoisted(() => ({
  client: {
    auth: {
      signInWithPassword: vi.fn<(...args: unknown[]) => Promise<object>>(),
      signOut: vi.fn<(...args: unknown[]) => Promise<object>>(),
    },
  },
  profile: vi.fn<(token: string) => Promise<Response>>(),
}));
vi.mock("server-only", () => ({}));
vi.mock("./server", () => ({ createAuthClient: async () => client }));
vi.mock("./session", () => ({ fetchProfile: profile }));
vi.mock("next/navigation", () => ({
  redirect: (path: string) => {
    throw new Error(`redirect:${path}`);
  },
}));

import { signIn, signOut } from "./actions";

function form(email = "test@example.org", password = "test-only-password") {
  const data = new FormData();
  data.set("email", email);
  data.set("password", password);
  return data;
}

describe("authentication actions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv("KOMPAS_SUPABASE_URL", "https://auth.example.org");
    vi.stubEnv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test");
    client.auth.signOut.mockResolvedValue({ error: null });
    client.auth.signInWithPassword.mockResolvedValue({
      data: { session: { access_token: "test-only-token" } },
      error: null,
    });
    profile.mockResolvedValue(new Response(null, { status: 200 }));
  });

  it("validates input before calling the provider", async () => {
    expect((await signIn({ error: "" }, form("invalid", ""))).error).toBeTruthy();
    expect(client.auth.signInWithPassword).not.toHaveBeenCalled();
  });

  it("does not bypass missing configuration", async () => {
    vi.stubEnv("SUPABASE_PUBLISHABLE_KEY", "");
    expect((await signIn({ error: "" }, form())).error).toContain("skonfigurowane");
    expect(client.auth.signInWithPassword).not.toHaveBeenCalled();
  });

  it("accepts the session only after the backend accepts the account", async () => {
    await expect(signIn({ error: "" }, form())).rejects.toThrow("redirect:/");
    expect(profile).toHaveBeenCalledWith("test-only-token");
  });

  it("hides provider error details", async () => {
    client.auth.signInWithPassword.mockResolvedValue({
      data: { session: null },
      error: { message: "private provider detail" },
    });
    const result = await signIn({ error: "" }, form());
    expect(result.error).not.toContain("private");
    expect(profile).not.toHaveBeenCalled();
  });

  it("clears the session when the account is inactive or unknown", async () => {
    profile.mockResolvedValue(new Response(null, { status: 401 }));
    expect((await signIn({ error: "" }, form())).error).toContain("administratorem");
    expect(client.auth.signOut).toHaveBeenCalledWith({ scope: "local" });
  });

  it("shows backend failure without displaying the token", async () => {
    profile.mockRejectedValue(new Error("private test-only-token"));
    const result = await signIn({ error: "" }, form());
    expect(result.error).toContain("niedostępna");
    expect(result.error).not.toContain("test-only-token");
    expect(client.auth.signOut).toHaveBeenCalled();
  });

  it("signs out locally and redirects", async () => {
    await expect(signOut()).rejects.toThrow("redirect:/login");
    expect(client.auth.signOut).toHaveBeenCalledWith({ scope: "local" });
  });
});
