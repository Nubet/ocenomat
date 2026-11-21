import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import { EmployeeList } from "./employee-list";
import { parseEmployeeQuery } from "./query";

it("renders server counts, filters and pagination without client-side slicing", () => {
  const query = parseEmployeeQuery({ q: "radca", page: "2", page_size: "10", sort: "name_desc" });
  const html = renderToStaticMarkup(
    <EmployeeList
      query={query}
      roles={["MANAGER"]}
      result={{
        items: [
          {
            id: "anna",
            name: "Anna Kowalska",
            position: "Radca",
            position_kind: "OTHER",
            department: "Departament Cyfryzacji",
          },
        ],
        page: 2,
        page_size: 10,
        total: 23,
        total_pages: 3,
      }}
    />,
  );
  expect(html).toContain("Anna Kowalska");
  expect(html).toContain("11–20");
  expect(html).toContain("z 23 osób");
  expect(html).toContain("q=radca");
  expect(html).toContain("page=1");
  expect(html).toContain("page=3");
  expect(html).toContain('name="position_kind"');
});

it("offers filter reset instead of access instructions for an empty search", () => {
  const html = renderToStaticMarkup(
    <EmployeeList
      query={parseEmployeeQuery({ q: "brak" })}
      roles={["MANAGER"]}
      result={{ items: [], page: 1, page_size: 20, total: 0, total_pages: 1 }}
    />,
  );
  expect(html).toContain("Nie znaleziono pasujących pracowników");
  expect(html).toContain("Wyczyść filtry");
  expect(html).not.toContain("Poproś administratora");
});
