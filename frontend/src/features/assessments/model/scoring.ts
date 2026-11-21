import { competencies, levels } from "../data/competencies";
import type { Answer, Assessment, CriterionId, Employee, FirstScore, Score } from "./types";

export function formType(employee: Employee) {
  return employee.manager ? "B" : "C";
}

export function requiredCriteria(employee: Employee): CriterionId[] {
  return employee.manager
    ? ["zarzadzanie", "decyzje", "organizacja", "wspolpraca", "komunikacja"]
    : ["wiedza", "rzetelnosc", "organizacja", "wspolpraca", "komunikacja"];
}

export function activeCompetencies(employee: Employee, extra: CriterionId[]) {
  const ids = new Set([...requiredCriteria(employee), ...extra]);
  return [...ids].map((id) => competencies.find((competency) => competency.id === id)!);
}

export function suggestedCriteria(employee: Employee): CriterionId[] {
  if (employee.manager) return ["negocjowanie", "analityczne", "wystapienia"];
  if (employee.id === "maria") return ["analityczne", "kreatywnosc", "decyzje"];
  return ["analityczne", "kryzys", "decyzje"];
}

export function suggestScore(answers: Record<number, Answer> = {}): Score | null {
  const scores = Object.values(answers)
    .filter((value) => value >= 0)
    .map((value) => levels[value].score);
  if (!scores.length) return null;
  const mean = scores.reduce((sum, score) => sum + score, 0) / scores.length;
  return levels.reduce((best, level) =>
    Math.abs(level.score - mean) < Math.abs(best.score - mean) ? level : best,
  ).score;
}

export function periodicResult(
  employee: Employee,
  assessment: Pick<Assessment, "extra" | "scores">,
) {
  const list = activeCompetencies(employee, assessment.extra);
  const values = list.map(({ id }) => assessment.scores[id]);
  const scores = values.filter((value): value is Score => value !== undefined);
  const complete = scores.length === list.length;
  const mean = scores.length
    ? scores.reduce<number>((sum, score) => sum + score, 0) / scores.length
    : null;
  const hasOne = scores.includes(1);
  const level =
    mean === null ? "—" : levels[Math.min(4, Math.max(0, Math.ceil(mean / 2) - 1))].label;
  return {
    list,
    scores,
    complete,
    mean,
    hasOne,
    positive: complete && mean !== null && mean > 4 && !hasOne,
    level,
  };
}

export function firstResult(scores: FirstScore[], report: "yes" | "no", exam: "yes" | "no" | "na") {
  const complete = scores.length === 5;
  const mean = complete ? scores.reduce<number>((sum, score) => sum + score, 0) / 5 : null;
  const threes = scores.filter((score) => score === 3).length;
  return {
    mean,
    threes,
    positive:
      complete && mean !== null && mean >= 5 && threes <= 1 && report === "yes" && exam !== "no",
  };
}

export function nextUnrated(employee: Employee, assessment: Assessment, current: number) {
  const list = activeCompetencies(employee, assessment.extra);
  const after = list.findIndex(
    (item, index) => index > current && assessment.scores[item.id] === undefined,
  );
  return after >= 0 ? after : list.findIndex((item) => assessment.scores[item.id] === undefined);
}

export function isDate(value: string) {
  return (
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    Number.isFinite(Date.parse(value)) &&
    new Date(value).toISOString().slice(0, 10) === value
  );
}

export function timingError(
  assessment: Pick<Assessment, "dateTalk" | "dateAssessment" | "agreed">,
) {
  if (!isDate(assessment.dateTalk) || !isDate(assessment.dateAssessment))
    return "Uzupełnij obie poprawne daty.";
  if (assessment.dateAssessment < assessment.dateTalk)
    return "Termin oceny nie może poprzedzać rozmowy.";
  if (assessment.agreed.length !== 3 || !assessment.agreed.every(Boolean))
    return "Potwierdź wszystkie omówione kwestie.";
  return null;
}

export function formatMean(mean: number | null, digits = 2) {
  return mean === null ? "—" : mean.toFixed(digits).replace(".", ",");
}
