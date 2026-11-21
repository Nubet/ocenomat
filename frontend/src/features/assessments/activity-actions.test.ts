import { beforeEach, describe, expect, it, vi } from "vitest";
import type { WorkspaceUser } from "@/features/auth/session";

vi.mock("@/features/auth/session", () => ({ requireUser: vi.fn<() => Promise<WorkspaceUser>>() }));
vi.mock("@/lib/api/server", () => ({
  apiRequest: vi.fn<(path: string, init?: RequestInit) => Promise<Response>>(),
}));
vi.mock("next/cache", () => ({ revalidatePath: vi.fn<(path: string) => void>() }));
vi.mock("next/navigation", () => ({
  unstable_rethrow: (error: unknown) => {
    if (error instanceof Error && error.message.startsWith("redirect:")) throw error;
  },
}));

import { requireUser } from "@/features/auth/session";
import { apiRequest } from "@/lib/api/server";
import { revalidatePath } from "next/cache";
import { saveActivity } from "./activity-actions";

const id = "00000000-0000-0000-0000-000000000001";
const previous = { error: "", conflict: false };
function form(operation = "observation") {
  const data = new FormData();
  for (const [key, value] of Object.entries({
    operation,
    revision: "5",
    criterion_id: id,
    text: "Konkretny przykład",
    observation_date: "2026-02-12",
    agenda: "Agenda",
    strengths: "Mocne strony",
    growth: "Rozwój",
    conversation_date: "2026-03-12",
    negative_justification: "Powody oceny",
    development_conclusions: "Plan rozwoju",
    author_id: "untrusted",
    confirmed_at: "untrusted",
    status: "completed",
  }))
    data.set(key, value);
  return data;
}

describe("persistent observations and conversation actions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(requireUser).mockResolvedValue({
      id: "manager",
      display_name: "Test",
      roles: ["MANAGER"],
    });
    vi.mocked(apiRequest).mockResolvedValue(
      Response.json({ id, employee_id: "employee", revision: 6 }),
    );
  });

  it.each([
    {
      operation: "observation",
      method: "POST",
      suffix: "/observations",
      body: {
        revision: 5,
        criterion_id: id,
        text: "Konkretny przykład",
        occurred_on: "2026-02-12",
      },
    },
    {
      operation: "conversation",
      method: "PUT",
      suffix: "/conversation",
      body: {
        revision: 5,
        agenda: "Agenda",
        strengths: "Mocne strony",
        growth: "Rozwój",
        occurred_on: "2026-03-12",
      },
    },
    {
      operation: "start_period",
      method: "POST",
      suffix: "/transitions",
      body: { revision: 5, action: "start_period" },
    },
    {
      operation: "confirm_conversation",
      method: "POST",
      suffix: "/transitions",
      body: { revision: 5, action: "confirm_conversation" },
    },
    {
      operation: "summary",
      method: "PUT",
      suffix: "/summary",
      body: {
        revision: 5,
        negative_justification: "Powody oceny",
        development_conclusions: "Plan rozwoju",
      },
    },
    {
      operation: "complete",
      method: "POST",
      suffix: "/transitions",
      body: { revision: 5, action: "complete" },
    },
  ])("sends only the $operation command fields", async ({ operation, method, suffix, body }) => {
    const result = await saveActivity(id, previous, form(operation));
    expect(result.error).toBe("");
    expect(result.assessment?.revision).toBe(6);
    expect(apiRequest).toHaveBeenCalledExactlyOnceWith(
      `/api/v1/assessments/${id}${suffix}`,
      expect.objectContaining({ method, body: JSON.stringify(body) }),
    );
    expect(revalidatePath).toHaveBeenCalledWith(`/assessments/${id}`);
    expect(revalidatePath).toHaveBeenCalledWith("/employees/employee");
  });

  it("saves a conversation draft without manufacturing a completed date", async () => {
    const data = form("conversation");
    data.set("conversation_date", "");
    await saveActivity(id, previous, data);
    expect(
      JSON.parse(vi.mocked(apiRequest).mock.calls[0][1]?.body as string).occurred_on,
    ).toBeNull();
  });

  it.each([403, 404, 409, 422, 500])(
    "preserves submitted text and revision on failure %s",
    async (status) => {
      vi.mocked(apiRequest).mockResolvedValue(new Response(null, { status }));
      const data = form();
      const result = await saveActivity(id, previous, data);
      expect(result.error).toBeTruthy();
      expect(result.conflict).toBe(status === 409);
      expect(result.assessment).toBeUndefined();
      expect(data.get("text")).toBe("Konkretny przykład");
      expect(data.get("revision")).toBe("5");
      expect(revalidatePath).not.toHaveBeenCalled();
      expect(apiRequest).toHaveBeenCalledTimes(1);
    },
  );

  it("does not resend after an unresolved conflict", async () => {
    const conflict = { error: "Konflikt", conflict: true };
    expect(await saveActivity(id, conflict, form())).toEqual(conflict);
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it("retains a draft on timeout and propagates session redirects", async () => {
    vi.mocked(apiRequest).mockRejectedValueOnce(new Error("timeout"));
    expect((await saveActivity(id, previous, form("conversation"))).error).toContain("pozostały");
    expect(revalidatePath).not.toHaveBeenCalled();
    vi.mocked(apiRequest).mockRejectedValueOnce(new Error("redirect:/login"));
    await expect(saveActivity(id, previous, form())).rejects.toThrow("redirect:/login");
  });

  it.each(["HR", "ADMIN"] as const)("rejects %s without the manager role", async (role) => {
    vi.mocked(requireUser).mockResolvedValue({ id: "test", display_name: "Test", roles: [role] });
    expect((await saveActivity(id, previous, form())).error).toContain("przełożony");
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it.each(["0", "-1", "1.5", "9007199254740992"])(
    "rejects invalid revision %s",
    async (revision) => {
      const data = form();
      data.set("revision", revision);
      expect((await saveActivity(id, previous, data)).error).toBeTruthy();
      expect(apiRequest).not.toHaveBeenCalled();
    },
  );

  it("rejects unknown commands and invalid assessment IDs", async () => {
    expect((await saveActivity(id, previous, form("unknown"))).error).toBeTruthy();
    expect((await saveActivity("bad", previous, form())).error).toBeTruthy();
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it("sends answers with null for no observation, without accepting a client suggestion", async () => {
    const data = form("answers");
    data.append("indicator_id", id);
    data.set(`level:${id}`, "");
    data.set(`note:${id}`, "Przykład");
    data.set("suggested_score", "9");
    data.set("policy_version", "untrusted");
    const result = await saveActivity(id, previous, data);
    expect(result.error).toBe("");
    expect(result.message).not.toContain("backend");
    expect(apiRequest).toHaveBeenCalledExactlyOnceWith(
      `/api/v1/assessments/${id}/criteria/${id}/answers`,
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({
          revision: 5,
          answers: [{ indicator_id: id, level: null, note: "Przykład" }],
        }),
      }),
    );
  });

  it("sends an explicit manual decision independently of the suggested score", async () => {
    const data = form("rating");
    data.set("score", "3");
    data.set("suggested_score", "9");
    await saveActivity(id, previous, data);
    expect(apiRequest).toHaveBeenCalledExactlyOnceWith(
      `/api/v1/assessments/${id}/criteria/${id}/rating`,
      expect.objectContaining({ method: "POST", body: JSON.stringify({ revision: 5, score: 3 }) }),
    );
  });

  it.each(["bad", "-1", "5", "null", " "])(
    "does not turn invalid level %s into missing observations",
    async (level) => {
      const data = form("answers");
      data.append("indicator_id", id);
      data.set(`level:${id}`, level);
      data.set(`note:${id}`, "Notatka");
      expect((await saveActivity(id, previous, data)).error).toBeTruthy();
      expect(apiRequest).not.toHaveBeenCalled();
    },
  );

  it.each(["", "2", "bad"])("does not approve missing or invalid score %s", async (score) => {
    const data = form("rating");
    data.set("score", score);
    expect((await saveActivity(id, previous, data)).error).toBeTruthy();
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it.each([409, 422, 500])("preserves answers on evaluation failure %s", async (status) => {
    vi.mocked(apiRequest).mockResolvedValue(new Response(null, { status }));
    const data = form("answers");
    data.append("indicator_id", id);
    data.set(`level:${id}`, "0");
    data.set(`note:${id}`, "Własny tekst");
    const result = await saveActivity(id, previous, data);
    expect(result.conflict).toBe(status === 409);
    expect(result.assessment).toBeUndefined();
    expect(data.get(`note:${id}`)).toBe("Własny tekst");
    expect(revalidatePath).not.toHaveBeenCalled();
  });

  it.each([409, 422, 500])("preserves summary text on completion failure %s", async (status) => {
    vi.mocked(apiRequest).mockResolvedValue(new Response(null, { status }));
    const data = form("complete");
    const result = await saveActivity(id, previous, data);
    expect(result.error).toBeTruthy();
    expect(result.conflict).toBe(status === 409);
    expect(data.get("negative_justification")).toBe("Powody oceny");
    expect(data.get("development_conclusions")).toBe("Plan rozwoju");
    expect(revalidatePath).not.toHaveBeenCalled();
    expect(apiRequest).toHaveBeenCalledTimes(1);
  });
});
