import { deadlineLabels, type Monitoring } from "@/features/monitoring/types";

export const deadlineStatuses = {
  all: "Wszystkie",
  overdue: "Po terminie",
  soon: "Bliski termin",
  planned: "Zaplanowane",
};

type Deadline = Monitoring["deadlines"][number];
export type DeadlineParams = Record<string, string | string[] | undefined>;

export function deadlineStatus(deadline: Deadline) {
  return deadline.overdue ? "overdue" : deadline.due_soon ? "soon" : "planned";
}

function normalize(value: string) {
  return value.toLocaleLowerCase("pl").normalize("NFD").replace(/\p{M}/gu, "").replaceAll("ł", "l");
}

export function getDeadlinePage(deadlines: Deadline[], params: DeadlineParams) {
  const q = typeof params.q === "string" ? params.q.trim().slice(0, 100) : "";
  const status =
    typeof params.status === "string" && Object.hasOwn(deadlineStatuses, params.status)
      ? (params.status as keyof typeof deadlineStatuses)
      : "all";
  const sort = params.sort === "date_desc" ? "date_desc" : "date_asc";
  const size = typeof params.page_size === "string" ? Number(params.page_size) : 10;
  const pageSize = [10, 20, 50].includes(size) ? size : 10;
  const requestedPage = typeof params.page === "string" ? Number(params.page) : 1;
  const tokens = normalize(q).split(/\s+/).filter(Boolean);
  const matches = deadlines
    .filter((deadline) => {
      const text = normalize(`${deadline.employee_name} ${deadlineLabels[deadline.kind]}`);
      return (
        (status === "all" || deadlineStatus(deadline) === status) &&
        tokens.every((token) => text.includes(token))
      );
    })
    .sort((a, b) => {
      const dateOrder = a.due_on.localeCompare(b.due_on) * (sort === "date_desc" ? -1 : 1);
      return (
        dateOrder ||
        a.employee_name.localeCompare(b.employee_name, "pl") ||
        a.assessment_id.localeCompare(b.assessment_id) ||
        a.kind.localeCompare(b.kind)
      );
    });
  const totalPages = Math.max(1, Math.ceil(matches.length / pageSize));
  const page =
    Number.isSafeInteger(requestedPage) && requestedPage > 0
      ? Math.min(requestedPage, totalPages)
      : 1;
  const query = { q, status, sort, page_size: String(pageSize), page: String(page) };

  return {
    query,
    items: matches.slice((page - 1) * pageSize, page * pageSize),
    total: matches.length,
    page,
    pageSize,
    totalPages,
  };
}

export function deadlineListHref(
  query: Record<string, string>,
  overrides: Record<string, string> = {},
) {
  return `/deadlines?${new URLSearchParams({ ...query, ...overrides })}`;
}
