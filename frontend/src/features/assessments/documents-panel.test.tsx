import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import type { AssessmentRecord } from "./types";
import type { AssessmentDocument } from "./document-types";

vi.mock("./document-actions", () => ({ saveDocument: vi.fn<() => Promise<never>>() }));
import { DocumentsPanel } from "./documents-panel";

const assessment: AssessmentRecord = {
  id: "assessment",
  employee_id: "employee",
  assessor_id: "manager",
  catalog_version_id: "catalog",
  job_description_id: null,
  kind: "periodic",
  form: "C",
  status: "draft",
  revision: 1,
  created_at: "2026-01-01T00:00:00Z",
  employee_snapshot: {
    id: "employee",
    name: "Jan",
    department: "Wydział",
    position: "Radca",
    position_kind: "OTHER",
  },
  criteria: [],
  required_criterion_ids: [],
  date_talk: null,
  date_assessment: null,
  duties_discussed: false,
  expectations_discussed: false,
  arrangements_shared: false,
  observations: [],
  conversation: null,
  ratings: [],
  summary: null,
  result: { outcome: "incomplete", mean: null },
};
const document: AssessmentDocument = {
  id: "doc",
  assessment_id: "assessment",
  kind: "periodic_pdf",
  filename: "Arkusz <script>.pdf",
  media_type: "application/pdf",
  size: 1000,
  sha256: "hash",
  author_id: "author",
  created_at: "2026-01-01T00:00:00Z",
  template_version: "v1",
  assessment_revision: 15,
};
function render(record = assessment, files: AssessmentDocument[] = []) {
  return renderToStaticMarkup(
    <DocumentsPanel
      assessment={record}
      initialFiles={files}
      initialDescriptions={[]}
      visible
      showPdf
      onSaved={() => {}}
      onPendingChange={() => {}}
    />,
  );
}
describe("assessment documents", () => {
  it("allows uploading an explicit OSP in draft without generating a formal result", () => {
    const html = render();
    expect(html).toContain("Nowa wersja OSP pracownika");
    expect(html).toContain("10 MiB");
    expect(html).not.toContain("Wygeneruj PDF arkusza C");
  });
  it("collects missing document fields only after completion", () => {
    const html = render({ ...assessment, status: "completed" });
    expect(html).toContain('name="office_name"');
    expect(html).toContain('name="period_end"');
    expect(html).toContain('name="no_promotion_request"');
    expect(html).not.toContain('type="file"');
    expect(html).not.toContain('value="select_osp"');
  });
  it("reuses the generated document and escapes filenames", () => {
    const html = render({ ...assessment, status: "completed" }, [document]);
    expect(html).toContain("/assessments/assessment/documents/doc");
    expect(html).toContain("Arkusz &lt;script&gt;.pdf");
    expect(html).not.toContain('name="office_name"');
    expect(html).toContain("nie jest podpisany ani doręczony");
  });
});
