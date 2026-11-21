import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import type { AssessmentRecord } from "./types";
import type { components } from "@/lib/api/schema";

vi.mock("./activity-actions", () => ({ saveActivity: vi.fn<() => Promise<never>>() }));
import { ActivityForm } from "./activity-form";

const assessment: AssessmentRecord = {
  id: "test",
  employee_id: "employee",
  assessor_id: "manager",
  catalog_version_id: "catalog",
  kind: "periodic",
  form: "C",
  status: "in_progress",
  revision: 7,
  created_at: "2026-01-01T12:00:00Z",
  employee_snapshot: {
    id: "employee",
    name: "Test Anna",
    position: "Radca",
    position_kind: "OTHER",
    department: "Test",
  },
  required_criterion_ids: ["selected"],
  criteria: [{ criterion_id: "selected", required: true, justification: null }],
  date_talk: "2026-01-10",
  date_assessment: "2027-01-10",
  duties_discussed: true,
  expectations_discussed: true,
  arrangements_shared: true,
  observations: [
    {
      id: "entry",
      criterion_id: "selected",
      text: "Konkretny przykład <script>",
      occurred_on: "2026-02-12",
      author_id: "manager",
      recorded_at: "2026-02-13T10:00:00Z",
    },
  ],
  conversation: {
    agenda: "Zapisana agenda",
    strengths: "Zapisane mocne strony",
    growth: "Zapisany rozwój",
    occurred_on: "2026-03-12",
    author_id: "manager",
    recorded_at: "2026-03-12T10:00:00Z",
    confirmed_at: null,
    confirmed_by: null,
  },
};
const catalog: components["schemas"]["CatalogResponse"] = {
  id: "catalog",
  version: "test",
  source_name: "test",
  source_sha256: "test",
  criteria: [
    { id: "selected", name: "Rzetelność z przypiętego katalogu", indicators: [] },
    { id: "not-selected", name: "Niewybrane kryterium", indicators: [] },
  ],
};
function render(record = assessment, step = "period") {
  return renderToStaticMarkup(
    <ActivityForm
      assessment={record}
      catalog={catalog}
      step={step}
      onSaved={() => {}}
      onPendingChange={() => {}}
    />,
  );
}

describe("saved observation and conversation screens", () => {
  it("restores dated entries, escapes note text and lists only selected criteria", () => {
    const html = render();
    expect(html).toContain("Rzetelność z przypiętego katalogu");
    expect(html).not.toContain("Niewybrane kryterium");
    expect(html).toContain("Konkretny przykład &lt;script&gt;");
    expect(html).toContain('dateTime="2026-02-12"');
    expect(html).toContain("Autor: Ty");
    expect(html).toContain('name="revision" value="7"');
  });

  it("restores every conversation tab and the separately recorded activity date", () => {
    const html = render(assessment, "conversation");
    for (const value of [
      "Zapisana agenda",
      "Zapisane mocne strony",
      "Zapisany rozwój",
      'value="2026-03-12"',
    ])
      expect(html).toContain(value);
    expect(html).toMatch(/value="confirm_conversation"[^>]*>Potwierdź/);
    expect(html).not.toMatch(/value="confirm_conversation"[^>]*disabled/);
    expect(html).toContain('role="tablist"');
    expect(html).toContain('aria-controls="conversation-panel-agenda"');
  });

  it("does not invent conversation notes, dates or confirmation", () => {
    const html = render({ ...assessment, observations: [], conversation: null });
    expect(html).toContain("Nie dodano jeszcze obserwacji");
    expect(html).not.toContain("Zapisana agenda");
    expect(html).toMatch(/value="confirm_conversation"[^>]*disabled/);
    expect(html).toMatch(/<input[^>]*name="conversation_date"[^>]*value=""/);
  });

  it.each([
    ["draft", "Najpierw zapisz kryteria"],
    ["criteria_agreed", 'value="start_period"'],
    ["evaluation", "Rozmowa jest potwierdzona"],
    ["completed", "Rozmowa jest potwierdzona"],
  ] as const)("blocks editing in %s", (status, message) => {
    const html = render({ ...assessment, status });
    expect(html).toContain('<fieldset disabled=""');
    expect(html).toContain(message);
  });
});
