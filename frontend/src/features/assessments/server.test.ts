import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("@/lib/api/server", () => ({ apiRequest: vi.fn<() => Promise<Response>>() }));
vi.mock("next/navigation", () => ({
  notFound: () => {
    throw new Error("not-found");
  },
}));

import { apiRequest } from "@/lib/api/server";
import { getAssessment, getAssessments } from "./server";

describe("persistent assessment reads", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not invent history for an empty authorized list", async () => {
    vi.mocked(apiRequest).mockResolvedValue(Response.json([]));
    expect(await getAssessments("employee-id")).toEqual([]);
    expect(apiRequest).toHaveBeenCalledWith("/api/v1/assessments?employee_id=employee-id");
  });

  it.each([404, 422])("makes an inaccessible or invalid UUID not found (%s)", async (status) => {
    vi.mocked(apiRequest).mockResolvedValue(new Response(null, { status }));
    await expect(getAssessment("jan")).rejects.toThrow("not-found");
  });

  it("surfaces an API failure instead of an empty history", async () => {
    vi.mocked(apiRequest).mockResolvedValue(new Response(null, { status: 503 }));
    await expect(getAssessments()).rejects.toThrow("Nie można pobrać listy ocen");
    await expect(getAssessment("id")).rejects.toThrow("Nie można pobrać oceny");
  });
});
