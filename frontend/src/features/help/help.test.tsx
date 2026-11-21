import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Help } from "./help";
import { AssessmentEmptyState } from "@/features/assessments/assessment-list";

describe("role-aware guidance", () => {
  it("explains every role and only offers the manager action to a manager", () => {
    const html = renderToStaticMarkup(<Help userRoles={["HR"]} />);
    expect(html).toContain("Przełożony");
    expect(html).toContain("Administrator");
    expect(html).toContain("Panel zarządzania kontami");
    expect(html).toContain("Przejdź do pracowników");
    expect(html).not.toContain("Przejdź do swoich ocen");
    expect(html).not.toContain("Zresetuj demo");
    expect(html).not.toContain("Bez backendu");
  });

  it("offers multiple relevant actions to an account with multiple roles", () => {
    const html = renderToStaticMarkup(<Help userRoles={["MANAGER", "HR", "ADMIN"]} />);
    expect(html).toContain("Przejdź do swoich ocen");
    expect(html).toContain("Przejdź do pracowników");
    expect(html).toContain("Sprawdź listę pracowników");
  });

  it("offers creation only when an assigned manager can create", () => {
    const allowed = renderToStaticMarkup(<AssessmentEmptyState roles={["MANAGER"]} canCreate />);
    expect(allowed).toContain('href="/assessments/new"');
    const unassigned = renderToStaticMarkup(
      <AssessmentEmptyState roles={["MANAGER"]} canCreate={false} />,
    );
    expect(unassigned).not.toContain('href="/assessments/new"');
    expect(unassigned).toContain("Poproś administratora");
    expect(unassigned).toContain("adres logowania");
  });

  it.each(["HR", "ADMIN"] as const)("does not suggest creating assessments to %s", (role) => {
    const html = renderToStaticMarkup(<AssessmentEmptyState roles={[role]} canCreate={false} />);
    expect(html).not.toContain('href="/assessments/new"');
    expect(html).toContain('href="/employees"');
    expect(html).toContain('href="/help"');
  });
});
