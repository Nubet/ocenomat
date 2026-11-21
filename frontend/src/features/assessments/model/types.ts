export const criterionIds = [
  "wiedza",
  "rzetelnosc",
  "organizacja",
  "wspolpraca",
  "komunikacja",
  "zarzadzanie",
  "decyzje",
  "analityczne",
  "kreatywnosc",
  "negocjowanie",
  "orientacja",
  "kryzys",
  "wystapienia",
  "strategiczne",
] as const;
export type CriterionId = (typeof criterionIds)[number];
export type Score = 1 | 3 | 5 | 7 | 9;
export type FirstScore = 3 | 5 | 7;
export type Answer = -1 | 0 | 1 | 2 | 3 | 4;
export type EmployeeId = "jan" | "maria" | "alicja" | "piotr";
export type FormType = "B" | "C";
export type ConversationTab = "agenda" | "strengths" | "growth";
export const steps = [
  "setup",
  "analysis",
  "criteria",
  "timing",
  "saved",
  "period",
  "conversation",
  "rating",
  "recommendation",
  "summary",
  "document",
  "finished",
  "first",
] as const;
export type AssessmentStep = (typeof steps)[number];

export interface Employee {
  id: EmployeeId;
  name: string;
  role: string;
  department: string;
  initials: string;
  avatar: "primary" | "peach" | "green" | "purple";
  manager: boolean;
  osp: string;
}

export interface Competency {
  id: CriterionId;
  name: string;
  indicators: { question: string; descriptions: readonly string[] }[];
}

export interface Assessment {
  type: "periodic" | "first";
  step: AssessmentStep;
  setupIndex: number;
  extra: CriterionId[];
  dateTalk: string;
  dateAssessment: string;
  agreed: boolean[];
  formal: boolean[];
  observations: { date: string; text: string; criterion: CriterionId }[];
  observationDraft: string;
  observationCriterion: CriterionId;
  conversation: Record<ConversationTab, string>;
  conversationDone: boolean;
  competencyIndex: number;
  indicatorIndex: number;
  answers: Partial<Record<CriterionId, Record<number, Answer>>>;
  notes: Record<string, string>;
  scores: Partial<Record<CriterionId, Score>>;
  override: Score | null;
  firstStep: number;
  firstScores: FirstScore[];
  firstHire: string;
  firstExam: "yes" | "no" | "na";
  firstReport: "yes" | "no";
}

export interface WorkspaceState {
  theme: "light" | "dark";
  // shortcut: one active assessment per employee; use assessment IDs when retaining process history.
  assessments: Record<EmployeeId, Assessment>;
}
