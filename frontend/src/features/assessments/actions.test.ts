import { beforeEach, describe, expect, it, vi } from "vitest";
import type { WorkspaceUser } from "@/features/auth/session";

vi.mock("@/features/auth/session", () => ({ requireUser: vi.fn<() => Promise<WorkspaceUser>>() }));
vi.mock("@/lib/api/server", () => ({
  apiRequest: vi.fn<(path: string, init?: RequestInit) => Promise<Response>>(),
}));
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
import { createAssessment, saveArrangements } from "./actions";
import { saveFirstAssessment } from "./first-actions";

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
  it("sends explicit first qualification without converting a preparatory-service waiver into an exam exemption", async () => {
    const data = form();
    data.set("kind", "first");
    data.set("hired_on", "2025-01-01");
    data.set("contract_end", "2025-12-31");
    data.set("employment_basis", "first_contract");
    data.set("qualification_basis", "Sprawdzona historia zatrudnienia");
    data.set("eligibility_confirmed", "on");
    data.set("exam", "not_applicable");
    await expect(createAssessment({ error: "" }, data)).rejects.toThrow("redirect:");
    const body = JSON.parse(String(vi.mocked(apiRequest).mock.calls[0]![1]!.body));
    expect(body.kind).toBe("first");
    expect(body.qualification.eligibility_confirmed).toBe(true);
    expect(body.qualification.ksap_graduate).toBe(false);
    expect(body.qualification).not.toHaveProperty("exam");
  });
  it("keeps a stale first-assessment revision on the form without invalidating saved data", async () => {
    vi.mocked(apiRequest).mockResolvedValue(new Response(null, { status: 409 }));
    const command = {
      revision: 2,
      reason: "justified_absence" as const,
      basis: "Pismo",
      circumstance_from: "2025-07-01",
      circumstance_to: "2025-07-10",
      notified_on: "2025-07-11",
      contract_end: "2025-12-31",
      report_from: "2025-09-11",
      report_to: "2025-09-15",
    };
    const result = await saveFirstAssessment(assessmentId, command, true);
    expect(result.conflict).toBe(true);
    expect(apiRequest).toHaveBeenCalledWith(
      `/api/v1/assessments/${assessmentId}/first/deadlines`,
      expect.objectContaining({ method: "POST", body: JSON.stringify(command) }),
    );
    expect(revalidatePath).not.toHaveBeenCalled();
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
    expect((await createAssessment({ error: "" }, data)).error).toContain(
      "nie utworzymy drugiej kopii",
    );
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

describe("save assessment arrangements", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(requireUser).mockResolvedValue({
      id: "manager",
      display_name: "Test",
      roles: ["MANAGER"],
    });
    vi.mocked(apiRequest).mockResolvedValue(
      Response.json({ id: assessmentId, employee_id: employeeId, revision: 2 }),
    );
  });
  function arrangement(operation = "criteria") {
    const data = new FormData();
    data.set("operation", operation);
    data.set("revision", "1");
    data.append("additional", requestKey);
    data.set(`reason:${requestKey}`, "Uzasadnienie z OSP");
    data.set("date_talk", "2026-01-10");
    data.set("date_assessment", "2027-01-10");
    data.set("duties_discussed", "on");
    data.set("status", "completed");
    return data;
  }
  const previous = { error: "", conflict: false };

  it.each([
    {
      operation: "criteria",
      suffix: "/criteria",
      method: "PUT",
      body: {
        revision: 1,
        additional: [{ criterion_id: requestKey, justification: "Uzasadnienie z OSP" }],
      },
    },
    {
      operation: "dates",
      suffix: "",
      method: "PATCH",
      body: {
        revision: 1,
        date_talk: "2026-01-10",
        date_assessment: "2027-01-10",
        duties_discussed: true,
        expectations_discussed: false,
        arrangements_shared: false,
      },
    },
    {
      operation: "agree",
      suffix: "/transitions",
      method: "POST",
      body: { revision: 1, action: "agree_criteria" },
    },
  ])(
    "sends only fields for $operation and refreshes after success",
    async ({ operation, suffix, method, body }) => {
      const result = await saveArrangements(assessmentId, previous, arrangement(operation));
      expect(result.error).toBe("");
      expect(apiRequest).toHaveBeenCalledWith(
        `/api/v1/assessments/${assessmentId}${suffix}`,
        expect.objectContaining({ method, body: JSON.stringify(body) }),
      );
      expect(revalidatePath).toHaveBeenCalledWith(`/assessments/${assessmentId}`);
      expect(revalidatePath).toHaveBeenCalledWith(`/employees/${employeeId}`);
    },
  );

  it("retains text and revision after a conflict without retrying or refreshing", async () => {
    vi.mocked(apiRequest).mockResolvedValue(new Response(null, { status: 409 }));
    const data = arrangement();
    const result = await saveArrangements(assessmentId, previous, data);
    expect(result.conflict).toBe(true);
    expect(result.error).toContain("nowej karcie");
    expect(result.assessment).toBeUndefined();
    expect(data.get(`reason:${requestKey}`)).toBe("Uzasadnienie z OSP");
    expect(data.get("revision")).toBe("1");
    expect(revalidatePath).not.toHaveBeenCalled();
    expect(apiRequest).toHaveBeenCalledTimes(1);
  });

  it.each(["HR", "ADMIN"] as const)("rejects %s without a manager role", async (role) => {
    vi.mocked(requireUser).mockResolvedValue({ id: "test", display_name: "Test", roles: [role] });
    expect((await saveArrangements(assessmentId, previous, arrangement())).error).toContain(
      "przełożony",
    );
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it.each(["0", "-1", "1.5", "NaN", "9007199254740992"])(
    "rejects invalid revision %s",
    async (value) => {
      const data = arrangement();
      data.set("revision", value);
      expect((await saveArrangements(assessmentId, previous, data)).error).toBeTruthy();
      expect(apiRequest).not.toHaveBeenCalled();
    },
  );

  it("does not catch a session redirect", async () => {
    vi.mocked(apiRequest).mockRejectedValue(new Error("redirect:/login"));
    await expect(saveArrangements(assessmentId, previous, arrangement())).rejects.toThrow(
      "redirect:/login",
    );
  });
});
