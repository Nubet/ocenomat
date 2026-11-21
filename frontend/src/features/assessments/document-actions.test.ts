import { beforeEach, describe, expect, it, vi } from "vitest";
import type { WorkspaceUser } from "@/features/auth/session";

vi.mock("@/features/auth/session", () => ({ requireUser: vi.fn<() => Promise<WorkspaceUser>>() }));
vi.mock("@/lib/api/server", () => ({
  apiRequest: vi.fn<(path: string, init?: RequestInit) => Promise<Response>>(),
}));
vi.mock("next/cache", () => ({ revalidatePath: vi.fn<(path: string) => void>() }));
vi.mock("next/navigation", () => ({
  unstable_rethrow: (error: unknown) => {
    if (error instanceof Error && error.message === "redirect") throw error;
  },
}));

import { requireUser } from "@/features/auth/session";
import { apiRequest } from "@/lib/api/server";
import { revalidatePath } from "next/cache";
import { saveDocument } from "./document-actions";
import { GET } from "@/app/(workspace)/assessments/[assessmentId]/documents/[documentId]/route";

const id = "00000000-0000-0000-0000-000000000001";
const previous = { error: "", conflict: false };
function form(operation = "pdf") {
  const result = new FormData();
  for (const [key, value] of Object.entries({
    operation,
    revision: "15",
    office_name: "Urząd w Łodzi",
    assessor_department: "Wydział",
    assessor_position: "Naczelnik",
    period_end: "2026-11-21",
    civil_service_status: "employee",
    no_promotion_request: "on",
    author_id: "forged",
    outcome: "positive",
  }))
    result.set(key, value);
  return result;
}

describe("document actions", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(requireUser).mockResolvedValue({
      id: "manager",
      display_name: "Test",
      roles: ["MANAGER"],
    });
    vi.mocked(apiRequest).mockImplementation(async (path) =>
      path.endsWith("/job-descriptions") || path.endsWith("/documents")
        ? Response.json([])
        : Response.json({ id, revision: 15 }),
    );
  });
  it("sends only explicit PDF fields and reloads private metadata", async () => {
    const result = await saveDocument(id, previous, form());
    expect(result.error).toBe("");
    const init = vi.mocked(apiRequest).mock.calls[0][1];
    expect(JSON.parse(init?.body as string)).toEqual({
      revision: 15,
      office_name: "Urząd w Łodzi",
      assessor_department: "Wydział",
      assessor_position: "Naczelnik",
      period_end: "2026-11-21",
      civil_service_status: "employee",
      no_promotion_request: true,
      previous_assessment: null,
    });
    expect(revalidatePath).toHaveBeenCalledWith(`/assessments/${id}`);
    expect(result.files).toEqual([]);
  });
  it("uploads raw bytes and includes the original filename and revision in an encoded query", async () => {
    const data = form("upload");
    data.set("kind", "osp");
    data.set(
      "file",
      new File(["test"], "Zażółć & plik.docx", { type: "application/octet-stream" }),
    );
    const result = await saveDocument(id, previous, data);
    expect(result.error).toBe("");
    const [path, init] = vi.mocked(apiRequest).mock.calls[0];
    expect(new URL(path, "http://api").searchParams.get("filename")).toBe("Zażółć & plik.docx");
    expect(init?.body).toBeInstanceOf(File);
    expect(init?.method).toBe("POST");
  });
  it("rejects an oversized file before contacting the API", async () => {
    const data = form("upload");
    data.set("kind", "osp");
    data.set("file", new File([new Uint8Array(10 * 1024 * 1024 + 1)], "large.pdf"));
    expect((await saveDocument(id, previous, data)).error).toContain("10 MiB");
    expect(apiRequest).not.toHaveBeenCalled();
  });
  it("does not retry a conflict or an uncertain result", async () => {
    vi.mocked(apiRequest).mockResolvedValueOnce(new Response(null, { status: 409 }));
    const result = await saveDocument(id, previous, form());
    expect(result.conflict).toBe(true);
    expect(await saveDocument(id, result, form())).toBe(result);
    expect(apiRequest).toHaveBeenCalledTimes(1);
    expect(revalidatePath).not.toHaveBeenCalled();
  });
  it("keeps uncertain successful uploads blocked until metadata can be reloaded", async () => {
    vi.mocked(apiRequest)
      .mockResolvedValueOnce(Response.json({}))
      .mockResolvedValueOnce(new Response(null, { status: 503 }));
    const result = await saveDocument(id, previous, form());
    expect(result.conflict).toBe(true);
    expect(result.error).toContain("Operacja została wykonana");
  });
  it("requires a manager and a valid revision", async () => {
    const data = form();
    data.set("revision", "1.2");
    expect((await saveDocument(id, previous, data)).error).not.toBe("");
    vi.mocked(requireUser).mockResolvedValue({ id: "hr", display_name: "HR", roles: ["HR"] });
    expect((await saveDocument(id, previous, form())).error).toContain("przełożony");
    expect(apiRequest).not.toHaveBeenCalled();
  });
  it("keeps redirect control flow intact", async () => {
    vi.mocked(apiRequest).mockRejectedValueOnce(new Error("redirect"));
    await expect(saveDocument(id, previous, form())).rejects.toThrow("redirect");
  });
});

describe("private document download route", () => {
  beforeEach(() => vi.resetAllMocks());
  it("streams bytes and forwards only download headers", async () => {
    vi.mocked(apiRequest).mockResolvedValue(
      new Response("%PDF-bytes", {
        headers: {
          "Content-Type": "application/pdf",
          "Content-Disposition": "attachment; filename=test.pdf",
          Authorization: "private",
        },
      }),
    );
    const result = await GET(new Request("http://app/download?osp=1"), {
      params: Promise.resolve({ assessmentId: id, documentId: id }),
    });
    expect(await result.text()).toBe("%PDF-bytes");
    expect(result.headers.get("cache-control")).toBe("private, no-store");
    expect(result.headers.get("authorization")).toBeNull();
    expect(apiRequest).toHaveBeenCalledWith(
      `/api/v1/assessments/${id}/documents/job-descriptions/${id}/download`,
    );
  });
  it.each([404, 503])("does not forward an upstream %s error body", async (status) => {
    vi.mocked(apiRequest).mockResolvedValue(new Response("private storage details", { status }));
    const result = await GET(new Request("http://app/download"), {
      params: Promise.resolve({ assessmentId: id, documentId: id }),
    });
    expect(result.status).toBe(status);
    expect(await result.text()).not.toContain("private storage");
  });
});
