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
import { askAssistant } from "./actions";
import type { AssistantRequest } from "./types";

const request: AssistantRequest = {
  question: "Pytanie",
  mode: "formal",
  assessment_kind: "unspecified",
  task: "question",
};

beforeEach(() => {
  vi.clearAllMocks();
});

it("sends only explicit context and allows time for both model passes", async () => {
  vi.mocked(apiRequest).mockResolvedValue(
    Response.json({ status: "insufficient_evidence", claims: [], limitations: [] }),
  );
  const result = await askAssistant({
    ...request,
    question: " Test ",
    mode: "formal",
    assessment_kind: "first",
  });
  expect("answer" in result).toBe(true);
  const [path, options] = vi.mocked(apiRequest).mock.calls[0]!;
  expect(path).toBe("/api/v1/ai/assistant");
  expect(JSON.parse(options!.body as string)).toEqual({
    question: "Test",
    mode: "formal",
    assessment_kind: "first",
    assessment_id: null,
    task: "question",
    history: [],
  });
  expect(options!.signal).toBeInstanceOf(AbortSignal);
});

it.each([404, 422, 429, 502, 503, 504])(
  "keeps service failure %i separate from a knowledge refusal",
  async (status) => {
    vi.mocked(apiRequest).mockResolvedValue(new Response("private provider details", { status }));
    const result = await askAssistant(request);
    expect(result).toHaveProperty("error");
    expect(JSON.stringify(result)).not.toContain("private provider details");
  },
);

it("preserves authentication redirects", async () => {
  vi.mocked(apiRequest).mockRejectedValue(new Error("redirect:/login"));
  await expect(askAssistant(request)).rejects.toThrow("redirect:/login");
});

it("rejects invalid questions before transport", async () => {
  expect(await askAssistant({ ...request, question: " " })).toHaveProperty("error");
  expect(await askAssistant({ ...request, question: "a".repeat(1001) })).toHaveProperty("error");
  expect(apiRequest).not.toHaveBeenCalled();
});
