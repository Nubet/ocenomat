import { expect, it } from "vitest";
import { employeeListHref, parseEmployeeQuery } from "./query";

it("normalizes invalid or repeated URL parameters", () => {
  expect(
    parseEmployeeQuery({
      page: "-1",
      page_size: "10000",
      sort: "toString",
      position_kind: "ADMIN",
      q: ["a", "b"],
    }),
  ).toEqual({
    q: "",
    page: 1,
    page_size: 20,
    sort: "name_asc",
    position_kind: "",
  });
  expect(parseEmployeeQuery({ page: "Infinity" }).page).toBe(1);
});

it("keeps search, sorting and page size when moving between pages", () => {
  const query = parseEmployeeQuery({
    q: "  Łącka radca ",
    position_kind: "OTHER",
    sort: "position_desc",
    page_size: "10",
    page: "2",
  });
  const url = new URL(employeeListHref(query, 3), "http://localhost");
  expect(Object.fromEntries(url.searchParams)).toEqual({
    q: "Łącka radca",
    position_kind: "OTHER",
    sort: "position_desc",
    page_size: "10",
    page: "3",
  });
});
