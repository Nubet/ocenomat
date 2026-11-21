import assert from "node:assert/strict";
import { test } from "vitest";
import { employees } from "@/features/assessments/data/employees";
import { assistantReply, assistantSuggestions } from "./responses";

test("all suggested questions have a deterministic answer and source", () => {
  for (const mode of ["formal", "conversation"] as const) {
    for (const step of ["criteria", "first", "period"]) {
      for (const question of assistantSuggestions(mode, step)) {
        const result = assistantReply(question, mode, employees[0]);
        assert.doesNotMatch(result.source, /Brak zweryfikowanej/);
        assert.ok(result.answer.length > 20);
      }
    }
  }
});

test("manager guidance uses B criteria and unknown questions do not invent a source", () => {
  assert.match(
    assistantReply("Jakie kryteria są obowiązkowe?", "formal", employees[3]).answer,
    /Arkusz B.*Zarządzanie ludźmi/,
  );
  assert.match(
    assistantReply("Pogoda jutro?", "formal", employees[0]).source,
    /Brak zweryfikowanej/,
  );
});
