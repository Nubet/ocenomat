import { beforeEach, expect, it, vi } from "vitest";
import type { EmployeePage } from "./types";

vi.mock("./server", () => ({ getEmployeePage: vi.fn<() => Promise<EmployeePage>>() }));
vi.mock("next/navigation", () => ({ unstable_rethrow: vi.fn<(error: unknown) => void>() }));
import { getEmployeePage } from "./server";
import { searchEmployees } from "./search-action";

beforeEach(() => vi.clearAllMocks());

it("fetches a bounded authorized page for global search", async () => {
  vi.mocked(getEmployeePage).mockResolvedValue({
    items: [],
    total: 13,
    page: 1,
    page_size: 8,
    total_pages: 2,
  });
  expect(await searchEmployees(" radca ")).toEqual({ items: [], total: 13 });
  expect(getEmployeePage).toHaveBeenCalledWith({ q: "radca", page_size: 8 });
});

it("rejects oversized queries and distinguishes transport failure from no matches", async () => {
  expect((await searchEmployees("a".repeat(101))).error).toBeTruthy();
  expect(getEmployeePage).not.toHaveBeenCalled();
  vi.mocked(getEmployeePage).mockRejectedValue(new Error("offline"));
  expect((await searchEmployees("Anna")).error).toContain("Nie udało się");
});
