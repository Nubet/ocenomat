import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import { ConversationForm, type ConversationDraft } from "./conversation-form";
import type { AssessmentRecord } from "./types";

const draft: ConversationDraft = {
  agenda: "Agenda",
  strengths: "Mocne strony",
  growth: "Rozwój",
  occurred_on: "2026-03-12",
};
const assessment: AssessmentRecord = {
  ratings: [],
  summary: null,
  result: { outcome: "incomplete", mean: null },
  id: "assessment",
  employee_id: "employee",
  assessor_id: "manager",
  catalog_version_id: "catalog",
  job_description_id: null,
  kind: "periodic",
  form: "C",
  status: "in_progress",
  revision: 8,
  created_at: "2026-01-01T12:00:00Z",
  employee_snapshot: {
    id: "employee",
    name: "Test Anna",
    position: "Radca",
    position_kind: "OTHER",
    department: "Test",
  },
  criteria: [],
  required_criterion_ids: [],
  observations: [],
  date_talk: "2026-01-10",
  date_assessment: "2027-01-10",
  duties_discussed: true,
  expectations_discussed: true,
  arrangements_shared: true,
  conversation: {
    ...draft,
    author_id: "manager",
    recorded_at: "2026-03-12T10:00:00Z",
    confirmed_at: null,
    confirmed_by: null,
  },
};

it.each([
  {
    label: "unsaved notes",
    value: { ...draft, growth: "Niezapisany tekst" },
    unsentObservation: false,
    conflict: false,
  },
  { label: "unsent observation", value: draft, unsentObservation: true, conflict: false },
  { label: "unresolved conflict", value: draft, unsentObservation: false, conflict: true },
])(
  "prevents confirmation with $label and retains every note",
  ({ value, unsentObservation, conflict }) => {
    const html = renderToStaticMarkup(
      <ConversationForm
        assessment={assessment}
        draft={value}
        onDraftChange={() => {}}
        action={() => {}}
        pending={false}
        conflict={conflict}
        hasUnsentObservation={unsentObservation}
      />,
    );
    expect(html).toMatch(/value="confirm_conversation"[^>]*disabled/);
    for (const key of ["agenda", "strengths", "growth"] as const) {
      expect(html).toContain(`name="${key}"`);
      expect(html).toContain(value[key]);
    }
  },
);
