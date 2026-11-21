import assert from "node:assert/strict";
import { test } from "vitest";
import { employees } from "../data/employees";
import { createAssessment, createWorkspace } from "./defaults";
import {
  activeCompetencies,
  firstResult,
  nextUnrated,
  periodicResult,
  requiredCriteria,
  suggestScore,
  timingError,
} from "./scoring";
import type { Assessment } from "./types";

const specialist = employees[0];
const manager = employees[3];

test("B and C select different mandatory criteria without duplicates", () => {
  assert.deepEqual(requiredCriteria(specialist), [
    "wiedza",
    "rzetelnosc",
    "organizacja",
    "wspolpraca",
    "komunikacja",
  ]);
  assert.deepEqual(requiredCriteria(manager), [
    "zarzadzanie",
    "decyzje",
    "organizacja",
    "wspolpraca",
    "komunikacja",
  ]);
  assert.equal(activeCompetencies(manager, ["decyzje", "analityczne"]).length, 6);
});

test("suggestions omit missing observations and choose the lower score on ties", () => {
  assert.equal(suggestScore(), null);
  assert.equal(suggestScore({ 0: -1, 1: -1 }), null);
  assert.equal(suggestScore({ 0: -1, 1: 3 }), 7);
  assert.equal(suggestScore({ 0: 2, 1: 3 }), 5);
  assert.equal(suggestScore({ 0: 0, 1: 4, 2: 4 }), 7);
});

test("periodic result requires every active criterion, mean > 4, and no ones", () => {
  const assessment = createAssessment();
  assessment.scores = {
    wiedza: 9,
    rzetelnosc: 9,
    organizacja: 9,
    wspolpraca: 9,
  };
  assert.equal(periodicResult(specialist, assessment).positive, false);
  assessment.scores.komunikacja = 1;
  const negative = periodicResult(specialist, assessment);
  assert.equal(negative.mean, 7.4);
  assert.equal(negative.hasOne, true);
  assert.equal(negative.positive, false);
  assessment.scores.komunikacja = 3;
  assert.equal(periodicResult(specialist, assessment).positive, true);
  assessment.extra = ["analityczne"];
  assert.equal(periodicResult(specialist, assessment).complete, false);
  assessment.scores.analityczne = 5;
  assert.equal(periodicResult(specialist, assessment).complete, true);
});

test("formal level uses the unrounded mean at every boundary", () => {
  const assessment = createAssessment();
  assessment.scores = {
    wiedza: 3,
    rzetelnosc: 3,
    organizacja: 3,
    wspolpraca: 5,
    komunikacja: 5,
  };
  assert.equal(periodicResult(specialist, assessment).positive, false);
  assessment.scores.rzetelnosc = 5;
  assert.equal(periodicResult(specialist, assessment).mean, 4.2);
  assert.equal(periodicResult(specialist, assessment).positive, true);
  assert.equal(periodicResult(specialist, assessment).level, "Na poziomie oczekiwań");
});

test("approval continues to optional and manager criteria, including earlier omissions", () => {
  const assessment = createAssessment();
  assessment.extra = ["analityczne"];
  assessment.scores = {
    zarzadzanie: 5,
    decyzje: 5,
    organizacja: 5,
    wspolpraca: 5,
    komunikacja: 5,
  };
  assert.equal(nextUnrated(manager, assessment, 4), 5);
  assessment.scores.analityczne = 7;
  assert.equal(nextUnrated(manager, assessment, 5), -1);
  delete assessment.scores.decyzje;
  assert.equal(nextUnrated(manager, assessment, 5), 1);
});

test("first assessment requires all four conditions simultaneously", () => {
  assert.equal(firstResult([5, 5, 5, 5, 5], "yes", "yes").positive, true);
  assert.equal(firstResult([3, 5, 5, 5, 7], "yes", "na").positive, true);
  assert.equal(firstResult([3, 3, 7, 7, 7], "yes", "yes").positive, false);
  assert.equal(firstResult([5, 5, 5, 5, 5], "no", "yes").positive, false);
  assert.equal(firstResult([5, 5, 5, 5, 5], "yes", "no").positive, false);
  assert.equal(firstResult([3, 5, 5, 5, 5], "yes", "yes").positive, false);
  assert.equal(firstResult([7], "yes", "yes").positive, false);
});

test("timing rejects missing, impossible, and reversed dates and incomplete confirmations", () => {
  const assessment = createAssessment();
  assert.match(timingError(assessment)!, /Potwierdź/);
  assessment.agreed = [true, true, true];
  assert.equal(timingError(assessment), null);
  for (const value of ["", "2026-02-30", "not-a-date", "2026-13-01"])
    assert.match(timingError({ ...assessment, dateTalk: value })!, /daty/);
  assert.match(timingError({ ...assessment, dateAssessment: "2025-01-01" })!, /poprzedzać/);
  assert.match(timingError({ ...assessment, agreed: [] })!, /Potwierdź/);
});

test("demo assessments never share mutable data between employees", () => {
  const state = createWorkspace();
  state.assessments.jan.conversation.agenda = "Changed";
  state.assessments.maria.extra.push("analityczne");
  state.assessments.piotr.firstScores[0] = 3;
  assert.notEqual(state.assessments.maria.conversation.agenda, "Changed");
  assert.deepEqual(state.assessments.alicja.extra, []);
  assert.deepEqual(state.assessments.jan.firstScores, [5, 5, 5, 5, 5]);
  const independent: Assessment = createAssessment();
  assert.notEqual(independent.conversation, state.assessments.jan.conversation);
});
