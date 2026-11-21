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
import { getEmployee, getEmployeePage, getEmployees } from "./server";

describe("authorized employees", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv("API_BASE_URL", "http://backend:8000");
    vi.mocked(requireAccessToken).mockResolvedValue("test-token");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          Response.json({ items: [], total: 0, page: 1, page_size: 100, total_pages: 1 }),
        ),
    );
  });

  it("keeps an empty authorized list empty instead of inserting demo records", async () => {
    expect(await getEmployees()).toEqual([]);
    expect(fetch).toHaveBeenCalledWith(
      new URL("http://backend:8000/api/v1/employees?page_size=100&page=1"),
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

  it("passes directory filters to the API and returns only the requested page", async () => {
    const data = { items: [], total: 42, page: 2, page_size: 10, total_pages: 5 };
    vi.mocked(fetch).mockResolvedValue(Response.json(data));
    expect(
      await getEmployeePage({
        q: "Łącka radca",
        page: 2,
        page_size: 10,
        sort: "name_desc",
        position_kind: "OTHER",
      }),
    ).toEqual(data);
    const url = vi.mocked(fetch).mock.calls[0]?.[0] as URL;
    expect(url.searchParams.get("q")).toBe("Łącka radca");
    expect(url.searchParams.get("page")).toBe("2");
    expect(url.searchParams.get("sort")).toBe("name_desc");
    expect(url.searchParams.get("position_kind")).toBe("OTHER");
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("does not truncate assessment choices to the first page", async () => {
    const first = { id: "first" };
    const last = { id: "last" };
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        Response.json({ items: [first], total: 101, page: 1, page_size: 100, total_pages: 2 }),
      )
      .mockResolvedValueOnce(
        Response.json({ items: [last], total: 101, page: 2, page_size: 100, total_pages: 2 }),
      );
    expect(await getEmployees(true)).toEqual([first, last]);
    expect(fetch).toHaveBeenLastCalledWith(
      new URL("http://backend:8000/api/v1/employees?assigned_only=true&page_size=100&page=2"),
      expect.anything(),
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
