import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import type { components } from "@/lib/api/schema";
import type { AssessmentRecord } from "./types";

vi.mock("./activity-actions", () => ({ saveActivity: vi.fn<() => Promise<never>>() }));
import { CompletionForm } from "./completion-form";

const catalog: components["schemas"]["CatalogResponse"] = {
  id: "catalog",
  version: "test",
  source_name: "Test",
  source_sha256: "test",
  criteria: [{ id: "criterion", name: "Rzetelność", indicators: [] }],
};
const assessment: AssessmentRecord = {
  id: "assessment",
  employee_id: "employee",
  assessor_id: "manager",
  catalog_version_id: "catalog",
  job_description_id: null,
  kind: "periodic",
  form: "C",
  status: "evaluation",
  revision: 15,
  created_at: "2026-01-01T12:00:00Z",
  employee_snapshot: {
    id: "employee",
    name: "Test Anna",
    position: "Radca",
    position_kind: "OTHER",
    department: "Test",
  },
  criteria: [{ criterion_id: "criterion", required: true, justification: null }],
  required_criterion_ids: ["criterion"],
  date_talk: "2026-01-10",
  date_assessment: "2027-01-10",
  duties_discussed: true,
  expectations_discussed: true,
  arrangements_shared: true,
  observations: [],
  conversation: null,
  ratings: [],
  result: { outcome: "incomplete", mean: null },
  summary: null,
};
const savedSummary: NonNullable<AssessmentRecord["summary"]> = {
  negative_justification: "",
  development_conclusions: "Zapisany plan <script>alert(1)</script>",
  author_id: "private-user-id",
  recorded_at: "2026-11-21T12:00:00Z",
  completed_by: null,
  completed_at: null,
};
function render(record = assessment, evaluationDirty = false, visible = true) {
  return renderToStaticMarkup(
    <CompletionForm
      assessment={record}
      catalog={catalog}
      visible={visible}
      evaluationDirty={evaluationDirty}
      onSaved={() => {}}
      onPendingChange={() => {}}
    />,
  );
}

describe("persistent result and completion", () => {
  it("shows missing decisions without a default outcome or demo autofill", () => {
    const html = render();
    expect(html).toContain("Wynik niekompletny");
    expect(html).toContain("Wymaga zatwierdzenia");
    expect(html).toContain("Sama propozycja oceny nie wystarcza");
    expect(html).toMatch(/value="complete"[^>]*disabled/);
    expect(html).not.toContain("Wypełnij przykładowe");
  });

  it("uses the API result rather than recalculating from displayed ratings", () => {
    const html = render({
      ...assessment,
      result: { outcome: "positive", mean: "4.33" },
      summary: savedSummary,
    });
    expect(html).toContain("Ocena pozytywna");
    expect(html).toContain("4,33");
    expect(html).not.toMatch(/value="complete"[^>]*disabled/);
    expect(html).toContain('name="revision" value="15"');
    expect(html).toContain("&lt;script&gt;");
    expect(html).not.toContain("private-user-id");
  });

  it("requires a saved justification for a negative result", () => {
    const negative: AssessmentRecord = {
      ...assessment,
      result: { outcome: "negative", mean: "7.67" },
      summary: savedSummary,
    };
    expect(render(negative)).toMatch(/value="complete"[^>]*disabled/);
    const html = render({
      ...negative,
      summary: { ...savedSummary, negative_justification: "Uzasadnienie" },
    });
    expect(html).toContain("Ocena negatywna");
    expect(html).toContain("Uzasadnienie");
    expect(html).not.toMatch(/value="complete"[^>]*disabled/);
  });

  it("blocks completion while behavioral drafts are unsaved", () => {
    const html = render(
      { ...assessment, result: { outcome: "positive", mean: "5.00" }, summary: savedSummary },
      true,
    );
    expect(html).toContain("masz niezapisane odpowiedzi lub wybrane oceny");
    expect(html).toMatch(/value="complete"[^>]*disabled/);
  });

  it("keeps a hidden summary mounted and locks completed records", () => {
    const html = render(
      {
        ...assessment,
        status: "completed",
        result: { outcome: "positive", mean: "5.00" },
        summary: {
          ...savedSummary,
          completed_at: "2026-11-21T12:05:00Z",
          completed_by: "private-user-id",
        },
      },
      false,
      false,
    );
    expect(html).toContain('<section hidden=""');
    expect(html).toContain('<fieldset disabled="">');
    expect(html).toContain("Ocena zakończona:");
    expect(html).toContain("Nie oznacza podpisania ani doręczenia");
  });

  it.each(["draft", "criteria_agreed", "in_progress"] as const)(
    "does not expose completion in %s",
    (status) => {
      const html = render({ ...assessment, status });
      expect(html).toContain("po potwierdzeniu rozmowy");
      expect(html).not.toContain('value="complete"');
    },
  );
});
