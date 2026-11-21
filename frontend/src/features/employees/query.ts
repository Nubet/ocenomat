import type { EmployeeRecord, EmployeeSort } from "./types";

export const employeeSorts: Record<EmployeeSort, string> = {
  name_asc: "Imię i nazwisko: A–Z",
  name_desc: "Imię i nazwisko: Z–A",
  position_asc: "Stanowisko: A–Z",
  position_desc: "Stanowisko: Z–A",
  department_asc: "Komórka: A–Z",
  department_desc: "Komórka: Z–A",
};

export const positionKinds: Record<EmployeeRecord["position_kind"], string> = {
  DIRECT_MANAGER: "Kierujące pracownikami",
  OTHER: "Pozostałe stanowiska",
  OFFICE_HEAD: "Kierownik urzędu",
};

export type EmployeeQuery = {
  q: string;
  position_kind: EmployeeRecord["position_kind"] | "";
  sort: EmployeeSort;
  page: number;
  page_size: number;
};

export function parseEmployeeQuery(
  params: Record<string, string | string[] | undefined>,
): EmployeeQuery {
  const sort = typeof params.sort === "string" ? params.sort : "";
  const kind = typeof params.position_kind === "string" ? params.position_kind : "";
  const page = typeof params.page === "string" ? Number(params.page) : 1;
  const pageSize = typeof params.page_size === "string" ? Number(params.page_size) : 20;
  return {
    q: typeof params.q === "string" ? params.q.trim().slice(0, 100) : "",
    position_kind: Object.hasOwn(positionKinds, kind)
      ? (kind as EmployeeQuery["position_kind"])
      : "",
    sort: Object.hasOwn(employeeSorts, sort) ? (sort as EmployeeSort) : "name_asc",
    page: Number.isSafeInteger(page) && page >= 1 && page <= 1_000_000 ? page : 1,
    page_size: [10, 20, 50].includes(pageSize) ? pageSize : 20,
  };
}

export function employeeListHref(query: EmployeeQuery, page = query.page) {
  const params = new URLSearchParams({
    sort: query.sort,
    page_size: String(query.page_size),
    page: String(page),
  });
  if (query.q) params.set("q", query.q);
  if (query.position_kind) params.set("position_kind", query.position_kind);
  return `/employees?${params}`;
}
