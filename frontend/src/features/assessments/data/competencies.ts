import type { Competency, CriterionId, Score } from "../model/types";

export const levels: readonly { score: Score; label: string }[] = [
  { score: 1, label: "Znacznie poniżej oczekiwań" },
  { score: 3, label: "Poniżej oczekiwań" },
  { score: 5, label: "Na poziomie oczekiwań" },
  { score: 7, label: "Powyżej oczekiwań" },
  { score: 9, label: "Znacznie powyżej oczekiwań" },
];

export const criterionNames: Record<CriterionId, string> = {
  wiedza: "Wykorzystywanie wiedzy i doskonalenie zawodowe",
  rzetelnosc: "Rzetelność",
  organizacja: "Organizacja pracy i orientacja na osiąganie celów",
  wspolpraca: "Współpraca",
  komunikacja: "Komunikacja",
  zarzadzanie: "Zarządzanie ludźmi",
  decyzje: "Podejmowanie decyzji i odpowiedzialność",
  analityczne: "Myślenie analityczne",
  kreatywnosc: "Kreatywność",
  negocjowanie: "Negocjowanie",
  orientacja: "Orientacja na klienta/interesanta",
  kryzys: "Radzenie sobie w sytuacjach kryzysowych",
  wystapienia: "Wystąpienia publiczne",
  strategiczne: "Zarządzanie strategiczne",
};

const baseCompetencies: Competency[] = [
  {
    id: "wiedza",
    name: criterionNames.wiedza,
    indicators: [
      {
        question: "Jak pracownik wykorzystuje posiadaną wiedzę w codziennych zadaniach?",
        descriptions: [
          "Nie stosuje potrzebnej wiedzy mimo wsparcia.",
          "Potrzebuje częstej pomocy przy typowych zadaniach.",
          "Samodzielnie wykorzystuje wiedzę w standardowych sytuacjach.",
          "Sprawnie dobiera rozwiązania także w trudniejszych sprawach.",
          "Tworzy rozwiązania i dzieli się wiedzą z całym zespołem.",
        ],
      },
      {
        question: "Jak podchodzi do nowych zagadnień i zmian?",
        descriptions: [
          "Nie podejmuje prób uzupełniania wiedzy.",
          "Uczy się dopiero po wyraźnym wskazaniu.",
          "Systematycznie uzupełnia potrzebne informacje.",
          "Samodzielnie poszukuje i wdraża nowe rozwiązania.",
          "Wyprzedza potrzeby i rozwija praktyki całego zespołu.",
        ],
      },
    ],
  },
  {
    id: "rzetelnosc",
    name: criterionNames.rzetelnosc,
    indicators: [
      {
        question: "Jak pracownik dba o jakość i poprawność przygotowanych materiałów?",
        descriptions: [
          "Często oddaje pracę z poważnymi błędami.",
          "Wymaga częstych poprawek i dodatkowej kontroli.",
          "Sprawdza swoją pracę i dostarcza poprawne materiały.",
          "Wychwytuje ryzyka i zapobiega błędom zawczasu.",
          "Ustanawia dobre praktyki jakości dla innych.",
        ],
      },
      {
        question: "Jak wywiązuje się z uzgodnionych zobowiązań?",
        descriptions: [
          "Regularnie nie realizuje uzgodnionych zadań.",
          "Dotrzymuje ustaleń tylko przy stałym nadzorze.",
          "Realizuje zadania zgodnie z ustaleniami i informuje o ryzykach.",
          "Aktywnie przewiduje przeszkody i proponuje rozwiązania.",
          "Konsekwentnie zwiększa niezawodność pracy zespołu.",
        ],
      },
    ],
  },
  {
    id: "organizacja",
    name: criterionNames.organizacja,
    indicators: [
      {
        question: "Jak pracownik ustala priorytety i planuje działania?",
        descriptions: [
          "Nie planuje pracy w sposób umożliwiający realizację zadań.",
          "Ma trudności z priorytetami bez wsparcia.",
          "Planuje pracę i reaguje na typowe zmiany.",
          "Sprawnie dostosowuje plan do pilnych potrzeb.",
          "Pomaga zespołowi usprawniać procesy i priorytety.",
        ],
      },
      {
        question: "Jak zarządza terminami?",
        descriptions: [
          "Często nie dotrzymuje terminów.",
          "Potrzebuje przypominania o zobowiązaniach.",
          "Samodzielnie pilnuje terminów i zgłasza zagrożenia.",
          "Skutecznie koordynuje zależności między zadaniami.",
          "Wyprzedzająco usprawnia planowanie w całym obszarze.",
        ],
      },
    ],
  },
  {
    id: "wspolpraca",
    name: criterionNames.wspolpraca,
    indicators: [
      {
        question: "Jak pracownik współdziała z innymi osobami?",
        descriptions: [
          "Utrudnia wspólną realizację zadań.",
          "Współpracuje tylko po wyraźnej prośbie.",
          "Wymienia informacje i terminowo realizuje ustalenia.",
          "Aktywnie pomaga innym osiągać wspólne cele.",
          "Buduje trwałą współpracę także między zespołami.",
        ],
      },
      {
        question: "Jak reaguje na odmienne opinie?",
        descriptions: [
          "Odrzuca argumenty bez wysłuchania.",
          "Z trudem akceptuje inne perspektywy.",
          "Słucha i uwzględnia konstruktywne uwagi.",
          "Łączy odmienne perspektywy w lepsze rozwiązania.",
          "Pomaga rozwiązywać złożone konflikty i budować zgodę.",
        ],
      },
    ],
  },
  {
    id: "komunikacja",
    name: criterionNames.komunikacja,
    indicators: [
      {
        question: "Jak pracownik przekazuje informacje?",
        descriptions: [
          "Komunikaty są często niezrozumiałe lub niepełne.",
          "Wymaga częstego doprecyzowywania przekazu.",
          "Przekazuje informacje jasno i adekwatnie do odbiorcy.",
          "Upraszcza złożone informacje i zapobiega nieporozumieniom.",
          "Podnosi standard komunikacji w całym zespole.",
        ],
      },
      {
        question: "Jak pracownik reaguje na pytania i wątpliwości?",
        descriptions: [
          "Pomija pytania lub odpowiada nieadekwatnie.",
          "Odpowiedzi często wymagają wyjaśnienia.",
          "Odpowiada rzeczowo i we właściwym czasie.",
          "Dopasowuje wyjaśnienia i sprawdza zrozumienie.",
          "Ułatwia rozwiązywanie trudnych spraw komunikacyjnych.",
        ],
      },
    ],
  },
];

const additionalQuestions: Partial<Record<CriterionId, string[]>> = {
  zarzadzanie: [
    "Jak deleguje zadania i odpowiedzialność?",
    "Jak udziela informacji zwrotnej podległym pracownikom?",
    "Jak wspiera rozwój osób w zespole?",
  ],
  decyzje: [
    "Jak analizuje warianty i ryzyka decyzji?",
    "Jak bierze odpowiedzialność za podjęte decyzje?",
  ],
  analityczne: [
    "Jak odróżnia informacje istotne od nieistotnych?",
    "Jak dostrzega zależności między informacjami?",
    "Jak formułuje wnioski?",
  ],
  kreatywnosc: ["Jak proponuje nowe rozwiązania?", "Jak podchodzi do zadań niestandardowych?"],
  negocjowanie: [
    "Jak przygotowuje argumentację do negocjacji?",
    "Jak dobiera strategie negocjacyjne?",
  ],
  orientacja: [
    "Jak rozpoznaje potrzeby interesanta?",
    "Jak proponuje rozwiązania odpowiadające potrzebom?",
  ],
  kryzys: ["Jak rozpoznaje sytuacje kryzysowe?", "Jak podejmuje działania rozwiązujące kryzys?"],
  wystapienia: ["Jak nawiązuje kontakt z audytorium?", "Jak zarządza czasem wystąpienia?"],
  strategiczne: ["Jak wyznacza cele strategiczne?", "Jak analizuje ryzyka działań strategicznych?"],
};

export const competencies: Competency[] = [
  ...baseCompetencies,
  ...Object.entries(additionalQuestions).map(([key, questions]) => {
    const id = key as CriterionId;
    return {
      id,
      name: criterionNames[id],
      indicators: questions.map((question) => ({
        question,
        descriptions: [
          `Nie realizuje wymaganych działań związanych z obszarem: ${criterionNames[id].toLowerCase()}.`,
          "Podejmuje działania niesystematycznie i wymaga częstego wsparcia.",
          "Realizuje typowe zadania samodzielnie, zgodnie z oczekiwaniami.",
          "Skutecznie działa również w sytuacjach trudniejszych niż standardowe.",
          "Wyznacza wysokie standardy i pomaga innym rozwijać te działania.",
        ],
      })),
    };
  }),
];

export const firstNames = [
  "Rzetelność",
  "Wykorzystywanie wiedzy i doskonalenie zawodowe",
  "Organizacja pracy i orientacja na osiąganie celów",
  "Komunikacja",
  "Współpraca",
];
