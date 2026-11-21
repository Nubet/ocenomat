import { beforeEach, expect, it, vi } from "vitest";
vi.mock("@/lib/api/server", () => ({
  apiRequest: vi.fn<(path: string, init?: RequestInit) => Promise<Response>>(),
}));
vi.mock("next/navigation", () => ({
  unstable_rethrow: (error: unknown) => {
    if (error instanceof Error && error.message.startsWith("redirect:")) throw error;
  },
}));
import { apiRequest } from "@/lib/api/server";
import { analyzeJobDescription } from "./osp-actions";
const id = "00000000-0000-0000-0000-000000000001";
beforeEach(() => {
  vi.clearAllMocks();
});
it("asks the backend to use its selected version, without client-provided OSP content", async () => {
  vi.mocked(apiRequest).mockResolvedValue(Response.json({ status: "insufficient_evidence" }));
  expect(await analyzeJobDescription(id)).toHaveProperty("analysis");
  const [path, options] = vi.mocked(apiRequest).mock.calls[0]!;
  expect(path).toBe(`/api/v1/ai/assessments/${id}/job-description-analysis`);
  expect(options?.method).toBe("POST");
  expect(options?.body).toBeUndefined();
});
it.each([404, 409, 422, 429, 503, 504])(
  "reports analysis error %i without pretending recommendations",
  async (status) => {
    vi.mocked(apiRequest).mockResolvedValue(new Response("secret", { status }));
    expect(await analyzeJobDescription(id)).toHaveProperty("error");
  },
);
it("rejects demo IDs without invoking analysis", async () => {
  expect(await analyzeJobDescription("jan")).toHaveProperty("error");
  expect(apiRequest).not.toHaveBeenCalled();
});
