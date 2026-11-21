import type { Assessment, EmployeeId, WorkspaceState } from "./types";

export function createAssessment(): Assessment {
  return {
    type: "periodic",
    step: "setup",
    setupIndex: 0,
    extra: [],
    dateTalk: "2026-11-23",
    dateAssessment: "2027-11-23",
    agreed: [false, false, false],
    formal: [false, false, false],
    observations: [],
    observationDraft: "",
    observationCriterion: "rzetelnosc",
    conversation: {
      agenda:
        "1. Cel i przebieg spotkania\n2. Najważniejsze osiągnięcia\n3. Obszary do rozwoju\n4. Ustalenie dalszych działań",
      strengths: "Docenić samodzielność w analizie danych i dobrą współpracę z innymi komórkami.",
      growth: "Zapytać, jakie zmiany pomogłyby lepiej planować pracę w okresach spiętrzenia zadań.",
    },
    conversationDone: false,
    competencyIndex: 0,
    indicatorIndex: 0,
    answers: {},
    notes: {},
    scores: {},
    override: null,
    firstStep: 0,
    firstScores: [5, 5, 5, 5, 5],
    firstHire: "2026-02-02",
    firstExam: "yes",
    firstReport: "yes",
  };
}

export function hasAssessmentProgress(assessment: Assessment) {
  return JSON.stringify(assessment) !== JSON.stringify(createAssessment());
}

export function createWorkspace(): WorkspaceState {
  const assessments = Object.fromEntries(
    (["jan", "maria", "alicja", "piotr"] as EmployeeId[]).map((id) => [id, createAssessment()]),
  ) as Record<EmployeeId, Assessment>;
  assessments.jan = {
    ...assessments.jan,
    step: "period",
    extra: ["analityczne"],
    dateTalk: "2025-11-23",
    dateAssessment: "2026-11-28",
    agreed: [true, true, true],
    competencyIndex: 1,
    observations: [
      {
        date: "2026-04-18",
        text: "Samodzielne przygotowanie analizy i omówienie ustaleń z zespołem.",
        criterion: "analityczne",
      },
    ],
    scores: { wiedza: 7, organizacja: 5, wspolpraca: 7, komunikacja: 5 },
  };
  assessments.maria = {
    ...assessments.maria,
    step: "criteria",
    dateAssessment: "2026-11-27",
  };
  assessments.piotr = {
    ...assessments.piotr,
    setupIndex: 2,
    dateAssessment: "2026-12-04",
  };
  assessments.alicja = {
    ...assessments.alicja,
    step: "document",
    dateAssessment: "2026-11-14",
    conversationDone: true,
    scores: {
      wiedza: 7,
      rzetelnosc: 5,
      organizacja: 5,
      wspolpraca: 7,
      komunikacja: 5,
    },
  };
  return { theme: "light", assessments };
}
