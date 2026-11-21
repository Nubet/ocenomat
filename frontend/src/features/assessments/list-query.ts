import { assessmentStatusLabels, type AssessmentRecord } from "./types";

export type AssessmentListParams = Record<string, string | string[] | undefined>;
export const assessmentGroups = { all: "Wszystkie", active: "Aktywne", completed: "Zakończone" };
export const assessmentSorts = {
  newest: "Od najnowszej",
  oldest: "Od najstarszej",
  name: "Pracownik: A–Z",
};

function normalize(value: string) {
  return value.toLocaleLowerCase("pl").normalize("NFD").replace(/\p{M}/gu, "").replaceAll("ł", "l");
}

export function getAssessmentListPage(
  assessments: AssessmentRecord[],
  params: AssessmentListParams,
) {
  const q = typeof params.q === "string" ? params.q.trim().slice(0, 100) : "";
  const group =
    typeof params.group === "string" && Object.hasOwn(assessmentGroups, params.group)
      ? params.group
      : "all";
  const requestedStatus =
    typeof params.status === "string" && Object.hasOwn(assessmentStatusLabels, params.status)
      ? params.status
      : "";
  const status =
    group === "all" ||
    (group === "completed" ? requestedStatus === "completed" : requestedStatus !== "completed")
      ? requestedStatus
      : "";
  const kind = params.kind === "periodic" || params.kind === "first" ? params.kind : "";
  const sort =
    typeof params.sort === "string" && Object.hasOwn(assessmentSorts, params.sort)
      ? params.sort
      : "newest";
  const size = typeof params.page_size === "string" ? Number(params.page_size) : 10;
  const pageSize = [10, 20, 50].includes(size) ? size : 10;
  const requestedPage = typeof params.page === "string" ? Number(params.page) : 1;
  const tokens = normalize(q).split(/\s+/).filter(Boolean);
  const matches = assessments
    .filter((assessment) => {
      const text = normalize(
        `${assessment.employee_snapshot.name} ${assessment.employee_snapshot.position}`,
      );
      return (
        (group === "all" ||
          (group === "completed"
            ? assessment.status === "completed"
            : assessment.status !== "completed")) &&
        (!status || assessment.status === status) &&
        (!kind || assessment.kind === kind) &&
        tokens.every((token) => text.includes(token))
      );
    })
    .sort((a, b) => {
      const dateOrder = Date.parse(a.created_at) - Date.parse(b.created_at);
      const nameOrder = a.employee_snapshot.name.localeCompare(b.employee_snapshot.name, "pl");
      return (
        (sort === "name" ? nameOrder || -dateOrder : sort === "oldest" ? dateOrder : -dateOrder) ||
        a.id.localeCompare(b.id)
      );
    });
  const totalPages = Math.max(1, Math.ceil(matches.length / pageSize));
  const page =
    Number.isSafeInteger(requestedPage) && requestedPage > 0
      ? Math.min(requestedPage, totalPages)
      : 1;
  return {
    query: { q, group, status, kind, sort, page_size: String(pageSize), page: String(page) },
    items: matches.slice((page - 1) * pageSize, page * pageSize),
    total: matches.length,
    page,
    pageSize,
    totalPages,
  };
}

export function assessmentListHref(
  query: Record<string, string>,
  overrides: Record<string, string> = {},
) {
  return `/assessments?${new URLSearchParams({ ...query, ...overrides })}`;
}
