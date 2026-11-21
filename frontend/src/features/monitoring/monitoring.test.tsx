import { renderToStaticMarkup } from "react-dom/server";
import { expect, it, vi } from "vitest";
import { Dashboard } from "@/features/dashboard/dashboard";
import { Deadlines } from "@/features/deadlines/deadlines";
import { HrOverview } from "@/features/hr/hr-overview";
import type { Monitoring } from "./types";

vi.mock("@/features/hr/actions", () => ({ sendReminder: vi.fn<() => Promise<string | null>>() }));

const data: Monitoring = {
  as_of: "2026-11-21",
  attention_window_days: 14,
  total: 1,
  in_progress: 0,
  completed: 0,
  needs_attention: 1,
  processes: [
    {
      id: "saved-process",
      employee_id: "saved-employee",
      employee_name: "Osoba z API",
      position: "Stanowisko z API",
      department: "Komórka z API",
      assessor_name: "Prowadzący z API",
      kind: "first",
      form: "P",
      status: "draft",
      date_assessment: null,
      needs_attention: true,
      can_remind: true,
    },
  ],
  deadlines: [
    {
      assessment_id: "saved-process",
      employee_name: "Osoba z API",
      kind: "introduction",
      due_on: "2026-11-20",
      overdue: true,
      due_soon: false,
    },
  ],
  reminders: [
    {
      id: "saved-reminder",
      assessment_id: "saved-process",
      sender_id: "hr",
      recipient_id: "manager",
      created_at: "2026-11-21T10:00:00Z",
      channel: "in_app",
      status: "delivered",
    },
  ],
};

it("shows saved processes, counts, deadlines and delivered reminders on the dashboard", () => {
  const html = renderToStaticMarkup(
    <Dashboard monitoring={data} displayName="Test" canCreate={false} isHr={true} />,
  );
  expect(html).toContain("Twoje procesy · 1");
  expect(html).toContain("Osoba z API");
  expect(html).toContain('href="/assessments/saved-process"');
  expect(html).toContain("Przypomnienia od HR");
  expect(html).toContain("Rozmowa wstępna");
  expect(html).not.toContain("Jan Kowalski");
});

it("renders overdue saved deadlines instead of static planned examples", () => {
  const html = renderToStaticMarkup(<Deadlines monitoring={data} />);
  expect(html).toContain("Po terminie");
  expect(html).toContain("20.11.2026");
  expect(html).toContain("Osoba z API");
  expect(html).toContain('href="/assessments/saved-process"');
  expect(html).not.toContain("Maria Wiśniewska");
});

it("renders HR process metadata without a link to private assessment content", () => {
  const html = renderToStaticMarkup(<HrOverview monitoring={data} />);
  expect(html).toContain("Prowadzący z API");
  expect(html).toContain("Komórka z API");
  expect(html).toContain("Pierwsza ocena");
  expect(html).not.toContain('href="/assessments/saved-process"');
});

it("renders truthful empty states for a user without processes", () => {
  const empty = {
    ...data,
    processes: [],
    reminders: [],
    deadlines: [],
    total: 0,
    in_progress: 0,
    completed: 0,
    needs_attention: 0,
  };
  const dashboard = renderToStaticMarkup(
    <Dashboard monitoring={empty} displayName="Test" canCreate={false} isHr={false} />,
  );
  expect(dashboard).toContain("Nie prowadzisz jeszcze żadnej oceny");
  expect(dashboard).not.toContain("Osoba z API");
  expect(renderToStaticMarkup(<Deadlines monitoring={empty} />)).toContain(
    "Brak zapisanych terminów aktywnych ocen",
  );
  expect(renderToStaticMarkup(<HrOverview monitoring={empty} />)).toContain(
    "Brak procesów w wybranym widoku",
  );
});
