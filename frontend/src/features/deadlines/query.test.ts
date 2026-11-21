import { expect, it } from "vitest";
import type { Monitoring } from "@/features/monitoring/types";
import { deadlineListHref, getDeadlinePage } from "./query";

const deadlines: Monitoring["deadlines"] = Array.from({ length: 23 }, (_, index) => ({
  assessment_id: String(index),
  employee_name: "Łukasz Żółkiewski",
  kind: "assessment",
  due_on: `2026-11-${String(index + 1).padStart(2, "0")}`,
  overdue: index < 12,
  due_soon: index >= 12 && index < 20,
}));

it("combines status and accent-insensitive search before paginating and preserves filters in links", () => {
  const result = getDeadlinePage(deadlines, {
    status: "overdue",
    q: "zolkiewski lukasz",
    page: "2",
  });
  expect(result.total).toBe(12);
  expect(result.items.map((item) => item.assessment_id)).toEqual(["10", "11"]);
  const url = new URL(deadlineListHref(result.query, { page: "1" }), "http://localhost");
  expect(url.searchParams.get("q")).toBe("zolkiewski lukasz");
  expect(url.searchParams.get("status")).toBe("overdue");
});

it("sorts without changing source data and clamps pages after filtering", () => {
  const result = getDeadlinePage(deadlines, { status: "soon", sort: "date_desc", page: "999" });
  expect(result.page).toBe(1);
  expect(result.items[0].due_on).toBe("2026-11-20");
  expect(deadlines[0].due_on).toBe("2026-11-01");
  expect(getDeadlinePage(deadlines, { q: "nieobecny" }).totalPages).toBe(1);
  expect(
    getDeadlinePage(deadlines, { status: "toString", page: "Infinity", page_size: "-1" }).items,
  ).toHaveLength(10);
});
