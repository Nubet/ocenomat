import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import type { AssessmentRecord } from "./types";
import type { components } from "@/lib/api/schema";

vi.mock("./actions", () => ({ saveArrangements: vi.fn<() => Promise<never>>() }));
vi.mock("./activity-actions", () => ({ saveActivity: vi.fn<() => Promise<never>>() }));
import { ArrangementForm } from "./arrangement-form";

const assessment: AssessmentRecord = {
  id: "test",
  employee_id: "employee",
  assessor_id: "manager",
  catalog_version_id: "catalog",
  kind: "periodic",
  form: "C",
  status: "draft",
  revision: 2,
  created_at: "2026-01-01T12:00:00Z",
  employee_snapshot: {
    id: "employee",
    name: "Test Anna",
    position: "Radca",
    position_kind: "OTHER",
    department: "Test",
  },
  required_criterion_ids: ["required"],
  criteria: [{ criterion_id: "extra", required: false, justification: "Zapisane uzasadnienie" }],
  date_talk: "2026-01-10",
  date_assessment: "2027-01-10",
  duties_discussed: false,
  expectations_discussed: false,
  arrangements_shared: false,
  observations: [],
  conversation: null,
};
const catalog: components["schemas"]["CatalogResponse"] = {
  id: "catalog",
  version: "test-version",
  source_name: "test",
  source_sha256: "test",
  criteria: [
    { id: "required", name: "Obowiązkowe z katalogu", indicators: [] },
    { id: "extra", name: "Dodatkowe z katalogu", indicators: [] },
  ],
};

describe("persisted arrangement screens", () => {
  it("loads selection and justification from the saved assessment and pinned catalog", () => {
    const html = renderToStaticMarkup(
      <ArrangementForm assessment={assessment} catalog={catalog} requestedStep="criteria" />,
    );
    expect(html).toContain("Zapisane uzasadnienie");
    expect(html).toContain("Obowiązkowe z katalogu");
    expect(html).toContain("Dodatkowe z katalogu");
    expect(html).toContain('name="revision" value="2"');
  });
  it("does not manufacture conversation confirmations and restores saved dates", () => {
    const html = renderToStaticMarkup(
      <ArrangementForm assessment={assessment} catalog={catalog} requestedStep="timing" />,
    );
    expect(html).toContain('value="2026-01-10"');
    expect(html).not.toContain('checked=""');
    expect(html).toContain('disabled=""');
    expect(html).toContain("Potwierdź ustalenia");
  });
  it("locks confirmed arrangements while allowing their review", () => {
    const html = renderToStaticMarkup(
      <ArrangementForm
        assessment={{ ...assessment, status: "criteria_agreed" }}
        catalog={catalog}
        requestedStep="criteria"
      />,
    );
    expect(html).toContain('<fieldset disabled="">');
    expect(html).toContain("Ustalenia zostały potwierdzone");
    expect(html).toContain("Zapisane uzasadnienie");
  });
});
