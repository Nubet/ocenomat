import { beforeEach, expect, it, vi } from "vitest";
import type { WorkspaceUser } from "@/features/auth/session";

vi.mock("@/features/auth/session", () => ({ requireUser: vi.fn<() => Promise<WorkspaceUser>>() }));
vi.mock("@/lib/api/server", () => ({
  apiRequest: vi.fn<(path: string, init?: RequestInit) => Promise<Response>>(),
}));
vi.mock("next/cache", () => ({ revalidatePath: vi.fn<(path: string) => void>() }));

import { requireUser } from "@/features/auth/session";
import { apiRequest } from "@/lib/api/server";
import { revalidatePath } from "next/cache";
import { sendReminder } from "./actions";

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(requireUser).mockResolvedValue({ id: "hr", display_name: "HR", roles: ["HR"] });
});

it.each([200, 201])(
  "confirms persisted delivery or replay (%s) using the same key",
  async (status) => {
    vi.mocked(apiRequest).mockResolvedValue(Response.json({ status: "delivered" }, { status }));
    expect(await sendReminder("process", "request-key")).toBeNull();
    expect(apiRequest).toHaveBeenCalledWith("/api/v1/monitoring/hr/process/reminders", {
      method: "POST",
      headers: { "Idempotency-Key": "request-key" },
    });
    expect(revalidatePath).toHaveBeenCalledWith("/hr");
    expect(revalidatePath).toHaveBeenCalledWith("/");
  },
);

it("rejects non-HR before mutation", async () => {
  vi.mocked(requireUser).mockResolvedValue({
    id: "admin",
    display_name: "Admin",
    roles: ["ADMIN", "MANAGER"],
  });
  expect(await sendReminder("process", "request-key")).toContain("Tylko HR");
  expect(apiRequest).not.toHaveBeenCalled();
});

it.each([403, 404, 409, 422, 503])(
  "does not report delivery for a rejected or failed save (%s)",
  async (status) => {
    vi.mocked(apiRequest).mockResolvedValue(new Response(null, { status }));
    expect(await sendReminder("process", "request-key")).not.toBeNull();
    expect(revalidatePath).not.toHaveBeenCalled();
  },
);

it("preserves uncertainty after a transport failure", async () => {
  vi.mocked(apiRequest).mockRejectedValue(new Error("network"));
  expect(await sendReminder("process", "request-key")).toContain("Nie potwierdzono");
  expect(revalidatePath).not.toHaveBeenCalled();
});
