import { expect, it } from "vitest";
import { assistantSuggestions } from "./responses";
import { assessmentContext } from "./types";

it("only supplies real assessment UUIDs, with no default employee", () => {
  expect(assessmentContext("/dashboard")).toBeUndefined();
  expect(assessmentContext("/assessments/new")).toBeUndefined();
  expect(assessmentContext("/employees/jan")).toBeUndefined();
  expect(assessmentContext("/assessments/00000000-0000-0000-0000-000000000001/summary")).toBe(
    "00000000-0000-0000-0000-000000000001",
  );
});

it("suggests questions appropriate to the explicitly selected scope", () => {
  expect(
    assistantSuggestions("formal", "first").every((question) => question.includes("pierwszej")),
  ).toBe(true);
  expect(assistantSuggestions("conversation", "periodic").join(" ")).toContain("rozmowę");
});
