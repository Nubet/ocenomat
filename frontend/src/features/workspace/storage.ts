import {
  criterionIds,
  steps,
  type Assessment,
  type WorkspaceState,
} from "@/features/assessments/model/types";
import { employees } from "@/features/assessments/data/employees";
import { competencies } from "@/features/assessments/data/competencies";
import { requiredCriteria } from "@/features/assessments/model/scoring";

export const storageKey = "kompas-workspace-v1";

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function text(value: unknown): value is string {
  return typeof value === "string" && value.length <= 100_000;
}
function member<T>(value: unknown, choices: readonly T[]): value is T {
  return choices.includes(value as T);
}
function integer(value: unknown, maximum: number) {
  return (
    typeof value === "number" &&
    Number.isInteger(value) &&
    value >= 0 &&
    value <= maximum
  );
}
function confirmations(value: unknown) {
  return (
    Array.isArray(value) &&
    value.length === 3 &&
    value.every((item) => typeof item === "boolean")
  );
}

function isAssessment(value: unknown): value is Assessment {
  if (!record(value)) return false;
  const conversation = value.conversation;
  return (
    member(value.type, ["periodic", "first"]) &&
    member(value.step, steps) &&
    integer(value.setupIndex, 3) &&
    integer(value.firstStep, 3) &&
    integer(value.competencyIndex, 7) &&
    integer(value.indicatorIndex, 2) &&
    Array.isArray(value.extra) &&
    value.extra.length <= 3 &&
    new Set(value.extra).size === value.extra.length &&
    value.extra.every((id) => member(id, criterionIds)) &&
    text(value.dateTalk) &&
    text(value.dateAssessment) &&
    text(value.firstHire) &&
    confirmations(value.agreed) &&
    confirmations(value.formal) &&
    typeof value.conversationDone === "boolean" &&
    record(conversation) &&
    ["agenda", "strengths", "growth"].every((key) => text(conversation[key])) &&
    record(value.notes) &&
    Object.entries(value.notes).every(
      ([key, note]) => /^[a-z]+-\d$/.test(key) && text(note),
    ) &&
    record(value.scores) &&
    Object.entries(value.scores).every(
      ([id, score]) =>
        member(id, criterionIds) && member(score, [1, 3, 5, 7, 9]),
    ) &&
    (value.override === null || member(value.override, [1, 3, 5, 7, 9])) &&
    record(value.answers) &&
    Object.entries(value.answers).every(
      ([id, answers]) =>
        member(id, criterionIds) &&
        record(answers) &&
        Object.entries(answers).every(
          ([index, answer]) =>
            /^\d$/.test(index) &&
            Number(index) <
              (competencies.find((item) => item.id === id)?.indicators.length ??
                0) &&
            member(answer, [-1, 0, 1, 2, 3, 4]),
        ),
    ) &&
    text(value.observationDraft) &&
    member(value.observationCriterion, criterionIds) &&
    Array.isArray(value.observations) &&
    value.observations.every(
      (item) =>
        record(item) &&
        text(item.date) &&
        text(item.text) &&
        member(item.criterion, criterionIds),
    ) &&
    Array.isArray(value.firstScores) &&
    value.firstScores.length === 5 &&
    value.firstScores.every((score) => member(score, [3, 5, 7])) &&
    member(value.firstExam, ["yes", "no", "na"]) &&
    member(value.firstReport, ["yes", "no"])
  );
}

export function parseWorkspace(raw: string): WorkspaceState | null {
  try {
    const value: unknown = JSON.parse(raw);
    if (!record(value) || value.version !== 1 || !record(value.state))
      return null;
    const state = value.state;
    if (!member(state.theme, ["light", "dark"]) || !record(state.assessments))
      return null;
    const assessments = state.assessments;
    if (
      !employees.every((employee) => {
        const assessment = assessments[employee.id];
        return (
          isAssessment(assessment) &&
          assessment.extra.every(
            (id) => !requiredCriteria(employee).includes(id),
          )
        );
      })
    )
      return null;
    return state as unknown as WorkspaceState;
  } catch {
    return null;
  }
}

export function serializeWorkspace(state: WorkspaceState) {
  return JSON.stringify({ version: 1, state });
}
