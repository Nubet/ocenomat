import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import type { AssessmentRecord } from "./types";
import type { AssessmentDocument } from "./document-types";

vi.mock("./document-actions", () => ({ saveDocument: vi.fn<() => Promise<never>>() }));
vi.mock("./first-actions", () => ({ saveFirstAssessment: vi.fn<() => Promise<never>>() }));
import { DocumentsPanel } from "./documents-panel";
import { FirstAssessmentForm } from "./first-form";

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
  it("collects only first-assessment PDF fields and recognizes the saved first PDF", () => {
    const first = {
      ...assessment,
      kind: "first" as const,
      form: "P" as const,
      status: "completed" as const,
    };
    const html = render(first);
    expect(html).toContain('value="first_pdf"');
    expect(html).not.toContain('name="period_end"');
    expect(html).not.toContain('name="no_promotion_request"');
    expect(render(first, [{ ...document, kind: "first_pdf" }])).not.toContain('name="office_name"');
  });
  it("restores first-assessment stages and uses the backend result", () => {
    const first: AssessmentRecord = {
      ...assessment,
      kind: "first",
      form: "P",
      status: "completed",
      result: { outcome: "negative", mean: "5" },
      first: {
        hired_on: "2025-01-01",
        contract_end: "2025-12-31",
        employment_basis: "first_contract",
        eligibility_confirmed: true,
        qualification_basis: "Zweryfikowana kwalifikacja",
        ksap_graduate: false,
        nomination_requested: false,
        intro_confirmed: true,
        arrangements_shared: true,
        report_missing: false,
        report_problems: "Brak problemów",
        report_learning: "Nowa wiedza",
        report_conclusions: "Wnioski",
        exam: "failed",
        exam_basis: "Protokół",
        conversation_notes: "Omówiono zadania",
        conversation_confirmed: true,
        justification: "Niezaliczony egzamin",
        development_conclusions: "Szkolenie",
        unit_head_name: "Kierujący",
        unit_head_position: "Dyrektor",
        unit_head_agreed: true,
        report_tasks: "Zapisane zadanie",
        scores: { reliability: 5, knowledge: 5, organization: 5, communication: 5, cooperation: 5 },
      },
    };
    const html = renderToStaticMarkup(
      <FirstAssessmentForm assessment={first} files={[]} descriptions={[]} />,
    );
    expect(html).toContain("Zapisane zadanie");
    expect(html).toContain("negatywny");
    expect(html).not.toContain('value="complete"');
    expect(html).toContain("disabled");
  });
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
