import { beforeEach, describe, expect, it, vi } from "vitest";
import type { WorkspaceUser } from "@/features/auth/session";

vi.mock("@/features/auth/session", () => ({ requireUser: vi.fn<() => Promise<WorkspaceUser>>() }));
vi.mock("@/lib/api/server", () => ({ apiRequest: vi.fn<() => Promise<Response>>() }));
vi.mock("next/cache", () => ({ revalidatePath: vi.fn<(path: string) => void>() }));
vi.mock("next/navigation", () => ({
  redirect: (path: string) => {
    throw new Error(`redirect:${path}`);
  },
  unstable_rethrow: (error: unknown) => {
    if (error instanceof Error && error.message.startsWith("redirect:")) throw error;
  },
}));

import { requireUser } from "@/features/auth/session";
import { apiRequest } from "@/lib/api/server";
import { revalidatePath } from "next/cache";
import { createAssessment } from "./actions";

const employeeId = "00000000-0000-0000-0000-000000000001";
const requestKey = "00000000-0000-0000-0000-000000000002";
const assessmentId = "00000000-0000-0000-0000-000000000003";
function form() {
  const data = new FormData();
  data.set("employee_id", employeeId);
  data.set("idempotency_key", requestKey);
  return data;
}

describe("create persistent assessment action", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(requireUser).mockResolvedValue({
      id: "manager",
      display_name: "Test",
      roles: ["MANAGER"],
    });
    vi.mocked(apiRequest).mockResolvedValue(Response.json({ id: assessmentId }, { status: 201 }));
  });

  it.each([201, 200])(
    "redirects to the same saved UUID after create or replay (%s)",
    async (status) => {
      vi.mocked(apiRequest).mockResolvedValue(Response.json({ id: assessmentId }, { status }));
      const data = form();
      data.set("status", "completed");
      data.set("assessor_id", "untrusted");
      await expect(createAssessment({ error: "" }, data)).rejects.toThrow(
        `redirect:/assessments/${assessmentId}`,
      );
      expect(apiRequest).toHaveBeenCalledWith(
        "/api/v1/assessments",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json", "Idempotency-Key": requestKey },
          body: JSON.stringify({ employee_id: employeeId, kind: "periodic" }),
        }),
      );
      expect(revalidatePath).toHaveBeenCalledWith("/assessments");
      expect(revalidatePath).toHaveBeenCalledWith(`/employees/${employeeId}`);
    },
  );

  it("rejects ADMIN without a manager role before sending a mutation", async () => {
    vi.mocked(requireUser).mockResolvedValue({
      id: "admin",
      display_name: "Test",
      roles: ["ADMIN"],
    });
    expect((await createAssessment({ error: "" }, form())).error).toContain("przełożony");
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it.each(["employee_id", "idempotency_key"])(
    "validates %s at the form boundary",
    async (field) => {
      const data = form();
      data.set(field, "bad-id");
      expect((await createAssessment({ error: "" }, data)).error).toBeTruthy();
      expect(apiRequest).not.toHaveBeenCalled();
    },
  );

  it.each([403, 404, 409, 422, 503, 500])(
    "keeps failed requests on the form without invalidation (%s)",
    async (status) => {
      vi.mocked(apiRequest).mockResolvedValue(new Response(null, { status }));
      const data = form();
      expect((await createAssessment({ error: "" }, data)).error).toBeTruthy();
      expect(data.get("idempotency_key")).toBe(requestKey);
      expect(revalidatePath).not.toHaveBeenCalled();
    },
  );

  it("reuses the request key after an uncertain network result", async () => {
    const data = form();
    vi.mocked(apiRequest).mockRejectedValueOnce(new Error("timeout"));
    expect((await createAssessment({ error: "" }, data)).error).toContain("ten sam klucz");
    await expect(createAssessment({ error: "" }, data)).rejects.toThrow(
      `redirect:/assessments/${assessmentId}`,
    );
    expect(apiRequest).toHaveBeenNthCalledWith(
      1,
      "/api/v1/assessments",
      expect.objectContaining({
        headers: expect.objectContaining({ "Idempotency-Key": requestKey }),
      }),
    );
    expect(apiRequest).toHaveBeenNthCalledWith(
      2,
      "/api/v1/assessments",
      expect.objectContaining({
        headers: expect.objectContaining({ "Idempotency-Key": requestKey }),
      }),
    );
  });

  it("does not swallow the login redirect", async () => {
    vi.mocked(apiRequest).mockRejectedValue(new Error("redirect:/login?error=account"));
    await expect(createAssessment({ error: "" }, form())).rejects.toThrow(
      "redirect:/login?error=account",
    );
  });
});
