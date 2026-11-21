import assert from "node:assert/strict";
import { test } from "node:test";
import { createWorkspace } from "@/features/assessments/model/defaults";
import { parseWorkspace, serializeWorkspace } from "./storage";

test("versioned storage round-trips the complete demo state", () => {
  const state = createWorkspace();
  assert.deepEqual(parseWorkspace(serializeWorkspace(state)), state);
});

test("malformed JSON, unknown versions, missing people and wrong types are rejected", () => {
  for (const raw of ["null", "[]", "{", "{}", '{"version":2,"state":{}}'])
    assert.equal(parseWorkspace(raw), null);
  const state = createWorkspace();
  assert.equal(
    parseWorkspace(
      JSON.stringify({ version: 1, state: { ...state, theme: "surprise" } }),
    ),
    null,
  );
  assert.equal(
    parseWorkspace(
      JSON.stringify({ version: 1, state: { ...state, assessments: {} } }),
    ),
    null,
  );
});

test("invalid scores, optional criteria, indicators and confirmations are rejected", () => {
  const patches = [
    { scores: { wiedza: 11 } },
    { answers: { wiedza: { 0: 9 } } },
    { answers: { wiedza: { 8: 1 } } },
    { extra: ["analityczne", "analityczne"] },
    { extra: ["komunikacja"] },
    { extra: ["missing"] },
    { agreed: [] },
    { firstScores: [5, 5, 5, 5, 9] },
    { conversation: null },
    {
      observations: [
        { text: "Test", date: "2026-01-01", criterion: "unknown" },
      ],
    },
    { competencyIndex: 100 },
  ];
  for (const patch of patches) {
    const state = createWorkspace();
    Object.assign(state.assessments.jan, patch);
    assert.equal(
      parseWorkspace(serializeWorkspace(state)),
      null,
      JSON.stringify(patch),
    );
  }
});

test("user notes remain text and are never interpreted as HTML", () => {
  const state = createWorkspace();
  state.assessments.jan.notes["wiedza-0"] = '<script>alert("example")</script>';
  assert.equal(
    parseWorkspace(serializeWorkspace(state))?.assessments.jan.notes[
      "wiedza-0"
    ],
    state.assessments.jan.notes["wiedza-0"],
  );
});
