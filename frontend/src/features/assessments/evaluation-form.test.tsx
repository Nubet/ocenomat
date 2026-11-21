import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import type { components } from "@/lib/api/schema";
import type { AssessmentRecord } from "./types";

vi.mock("./activity-actions", () => ({ saveActivity: vi.fn<() => Promise<never>>() }));
import { EvaluationForm } from "./evaluation-form";

const criterion: components["schemas"]["Criterion"] = {
  id: "criterion",
  name: "Rzetelność",
  indicators: [
    {
      id: "indicator",
      description: "Pełny opis wskaźnika z przypiętego katalogu",
      levels: [0, 1, 2, 3, 4].map((level) => ({
        level,
        name: `Poziom ${level}`,
        description: `Pełny opis zachowania ${level}`,
      })),
    },
  ],
};
const catalog: components["schemas"]["CatalogResponse"] = {
  id: "catalog",
  version: "v1",
  source_name: "Test",
  source_sha256: "test",
  criteria: [criterion, { id: "unselected", name: "Niewybrane kryterium", indicators: [] }],
};
const assessment: AssessmentRecord = {
  id: "assessment",
  employee_id: "employee",
  assessor_id: "manager",
  catalog_version_id: "catalog",
  kind: "periodic",
  form: "C",
  status: "evaluation",
  revision: 7,
  created_at: "2026-01-01T12:00:00Z",
  employee_snapshot: {
    id: "employee",
    name: "Test Anna",
    position: "Radca",
    position_kind: "OTHER",
    department: "Test",
  },
  criteria: [{ criterion_id: criterion.id, required: true, justification: null }],
  required_criterion_ids: [criterion.id],
  date_talk: "2026-01-10",
  date_assessment: "2027-01-10",
  duties_discussed: true,
  expectations_discussed: true,
  arrangements_shared: true,
  observations: [],
  conversation: null,
  ratings: [],
};
function render(record = assessment, visible = true) {
  return renderToStaticMarkup(
    <EvaluationForm
      assessment={record}
      catalog={catalog}
      visible={visible}
      onSaved={() => {}}
      onPendingChange={() => {}}
    />,
  );
}

describe("persistent behavioral evaluation", () => {
  it("shows every original level description only for selected criteria", () => {
    const html = render();
    expect(html).toContain(criterion.indicators[0].description);
    for (const level of criterion.indicators[0].levels) expect(html).toContain(level.description);
    expect(html).not.toContain("Niewybrane kryterium");
    expect(html).toContain('name="revision" value="7"');
    expect(html).toContain('name="indicator_id" value="indicator"');
    expect(html).toContain("brak propozycji");
    expect(html).toContain("Brak obserwacji");
    expect(html).toMatch(/value="rating"[^>]*disabled/);
    expect(html).not.toMatch(/name="score"[^>]*checked/);
  });

  it("restores answers and suggestion without automatically selecting a formal score", () => {
    const html = render({
      ...assessment,
      ratings: [
        {
          criterion_id: criterion.id,
          answers: [{ indicator_id: "indicator", level: 4, note: "Zapisana notatka" }],
          suggested_score: 9,
          policy_version: "nearest-mean-lower-tie-v1",
          author_id: "manager",
          recorded_at: "2026-11-21T12:00:00Z",
          score: null,
          confirmed_by: null,
          confirmed_at: null,
        },
      ],
    });
    expect(html).toMatch(/name="level:indicator"[^>]*checked=""[^>]*value="4"/);
    expect(html).toContain("Zapisana notatka");
    expect(html).toContain("Proponowana ocena: 9");
    expect(html).not.toMatch(/name="score"[^>]*checked/);
    expect(html).not.toContain("nearest-mean-lower-tie-v1");
    expect(html).not.toContain("backend");
  });

  it("restores a separately confirmed decision and its date", () => {
    const html = render({
      ...assessment,
      ratings: [
        {
          criterion_id: criterion.id,
          answers: [],
          suggested_score: null,
          policy_version: "nearest-mean-lower-tie-v1",
          author_id: "manager",
          recorded_at: "2026-11-21T12:00:00Z",
          score: 3,
          confirmed_by: "technical-user-id",
          confirmed_at: "2026-11-21T12:00:00Z",
        },
      ],
    });
    expect(html).toContain("Zatwierdzono: 3");
    expect(html).toContain("Zatwierdzono 1 z");
    expect(html).toContain("Twoje zatwierdzenie:");
    expect(html).not.toContain("technical-user-id");
  });

  it.each(["draft", "criteria_agreed", "in_progress"] as const)(
    "does not open rating input in %s",
    (status) => {
      const html = render({ ...assessment, status });
      expect(html).toContain("Najpierw potwierdź odbytą rozmowę");
      expect(html).not.toContain('name="score"');
    },
  );

  it("keeps the screen mounted when hidden and makes completed assessments read-only", () => {
    const html = render({ ...assessment, status: "completed" }, false);
    expect(html).toContain('<section hidden=""');
    expect(html).toContain('<fieldset disabled="">');
    expect(html).toContain(criterion.indicators[0].description);
  });
});
