import { expect, it } from "vitest";
import { assessmentListHref, getAssessmentListPage } from "./list-query";
import type { AssessmentRecord } from "./types";

const assessments: AssessmentRecord[] = Array.from({ length: 23 }, (_, index) => ({
  id: String(index),
  employee_id: "employee",
  assessor_id: "manager",
  catalog_version_id: "catalog",
  job_description_id: null,
  kind: index < 12 ? "periodic" : "first",
  form: index < 12 ? "C" : "P",
  status: index < 12 ? "draft" : "completed",
  revision: 1,
  created_at: `2026-11-${String(index + 1).padStart(2, "0")}T12:00:00Z`,
  employee_snapshot: {
    id: "employee",
    name: "Łukasz Żółkiewski",
    position: "Radca",
    position_kind: "OTHER",
    department: "Biuro",
  },
  criteria: [],
  date_talk: null,
  date_assessment: null,
  duties_discussed: false,
  expectations_discussed: false,
  arrangements_shared: false,
  observations: [],
  ratings: [],
  summary: null,
  result: { outcome: "incomplete", mean: null },
  conversation: null,
}));

it("combines employee search, group, stage and kind before pagination", () => {
  const result = getAssessmentListPage(assessments, {
    q: "radca lukasz",
    group: "active",
    status: "draft",
    kind: "periodic",
    page: "2",
  });
  expect(result.total).toBe(12);
  expect(result.items.map((item) => item.id)).toEqual(["1", "0"]);
  const url = new URL(assessmentListHref(result.query, { page: "1" }), "http://localhost");
  expect(url.searchParams.get("q")).toBe("radca lukasz");
  expect(url.searchParams.get("status")).toBe("draft");
  expect(url.searchParams.get("group")).toBe("active");
});

it("normalizes invalid parameters and incompatible stages and clamps the page", () => {
  const result = getAssessmentListPage(assessments, {
    group: "completed",
    status: "draft",
    page: "999",
    sort: "oldest",
  });
  expect(result.query.status).toBe("");
  expect(result.page).toBe(2);
  expect(result.items[0].id).toBe("22");
  expect(getAssessmentListPage(assessments, { q: "nieobecny" }).totalPages).toBe(1);
  expect(
    getAssessmentListPage(assessments, { status: "toString", page: "Infinity", page_size: "-1" })
      .items,
  ).toHaveLength(10);
  expect(assessments[0].id).toBe("0");
});
