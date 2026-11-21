import assert from "node:assert/strict";
import { test } from "vitest";
import { employees } from "../data/employees";
import { createAssessment, createWorkspace, hasAssessmentProgress } from "./defaults";
import { resolveAssessmentStep } from "./navigation";

test("unknown URLs fall back to the employee's saved step", () => {
  const assessment = createWorkspace().assessments.jan;
  assert.equal(resolveAssessmentStep(employees[0], assessment, "unknown"), "period");
  assert.equal(resolveAssessmentStep(employees[0], assessment), "period");
  assert.equal(resolveAssessmentStep(employees[0], assessment, "criteria"), "criteria");
});

test("scoring URLs require the conversation to be confirmed first", () => {
  const assessment = createAssessment();
  for (const step of ["rating", "recommendation"])
    assert.equal(resolveAssessmentStep(employees[0], assessment, step), "conversation");
  assessment.conversationDone = true;
  assert.equal(resolveAssessmentStep(employees[0], assessment, "rating"), "rating");
});

test("recommendations require every indicator, and accept no-observation answers", () => {
  const assessment = createAssessment();
  assessment.conversationDone = true;
  assert.equal(resolveAssessmentStep(employees[0], assessment, "recommendation"), "rating");
  assessment.answers.wiedza = { 0: -1 };
  assert.equal(resolveAssessmentStep(employees[0], assessment, "recommendation"), "rating");
  assessment.answers.wiedza[1] = -1;
  assert.equal(resolveAssessmentStep(employees[0], assessment, "recommendation"), "recommendation");
});

test("completion requires both all scores and all formal confirmations", () => {
  const assessment = createWorkspace().assessments.alicja;
  assert.equal(resolveAssessmentStep(employees[2], assessment, "finished"), "document");
  assessment.formal = [true, true, true];
  assert.equal(resolveAssessmentStep(employees[2], assessment, "finished"), "finished");
  assessment.extra = ["analityczne"];
  assert.equal(resolveAssessmentStep(employees[2], assessment, "finished"), "document");
});

test("starting over recognizes unfinished setup and drafts as existing progress", () => {
  assert.equal(hasAssessmentProgress(createAssessment()), false);
  assert.equal(hasAssessmentProgress({ ...createAssessment(), setupIndex: 1 }), true);
  assert.equal(
    hasAssessmentProgress({ ...createAssessment(), observationDraft: "Unfinished note" }),
    true,
  );
  assert.equal(hasAssessmentProgress({ ...createAssessment(), dateTalk: "2026-12-01" }), true);
});
