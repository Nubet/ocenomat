import { criterionNames } from "@/features/assessments/data/competencies";
import {
  formType,
  requiredCriteria,
} from "@/features/assessments/model/scoring";
import type { Employee } from "@/features/assessments/model/types";

export type AssistantMode = "formal" | "conversation";

export function assistantSuggestions(mode: AssistantMode, context: string) {
  if (mode === "conversation")
    return [
      "Jak przekazać konstruktywną informację zwrotną?",
      "Jak rozmawiać o rozwoju?",
      "Jak wykorzystać obserwacje podczas rozmowy?",
    ];
  if (context === "first")
    return [
      "Jakie są cztery warunki pozytywnej pierwszej oceny?",
      "Jaka jest skala pierwszej oceny?",
      "Kto zatwierdza ocenę?",
    ];
  if (["criteria", "analysis"].includes(context))
    return [
      "Jakie kryteria są obowiązkowe dla arkusza B/C?",
      "Jak dobrać kryteria dodatkowe?",
      "Czym różni się arkusz B od C?",
    ];
  return [
    "Co oznacza ocena 1 punkt?",
    "Kiedy odbywa się rozmowa oceniająca?",
    "Kto zatwierdza ocenę?",
  ];
}

export function assistantReply(
  question: string,
  mode: AssistantMode,
  employee: Employee,
) {
  const query = question.toLocaleLowerCase("pl");
  if (/pierwsz|egzamin|sprawozda/.test(query))
    return {
      answer:
        "Pierwsza ocena korzysta z pięciu elementów i skali 3/5/7. Wynik pozytywny wymaga średniej min. 5, nie więcej niż jednej trójki, terminowego sprawozdania i zaliczonego egzaminu (jeśli dotyczy).",
      source: "Rozporządzenie PRM z 23.07.2015 r. · §§ 2, 9–10",
    };
  if (/obowiązkow|kryteri/.test(query))
    return {
      answer: `Arkusz ${formType(employee)}: wymagane kryteria to ${requiredCriteria(
        employee,
      )
        .map((id) => criterionNames[id])
        .join(
          "; ",
        )}. Można dobrać maksymalnie trzy dodatkowe z oficjalnego katalogu, jeśli uzasadnia to OSP.`,
      source: "Rozporządzenie PRM z 4.04.2016 r. · §§ 2–5",
    };
  if (/arkusz|formularz/.test(query))
    return {
      answer:
        "Arkusz B stosuje się dla stanowisk, na których praca polega na bezpośrednim kierowaniu pracownikami (poza przypadkiem arkusza A); C — dla pozostałych stanowisk.",
      source: "Rozporządzenie PRM z 4.04.2016 r. · §§ 2–5",
    };
  if (/1 punkt|wynik|średni/.test(query))
    return {
      answer:
        "Przy ocenie okresowej średnia powyżej 4 nie wystarcza, jeśli choć jedno kryterium oceniono na 1 punkt. Wtedy wynik jest negatywny.",
      source: "Rozporządzenie PRM z 4.04.2016 r. · § 11",
    };
  if (query.includes("rozmow") && mode === "formal")
    return {
      answer:
        "Rozmowę oceniającą przeprowadza się przed sporządzeniem oceny na piśmie. Omawia się wykonywane zadania, realizację celów i kierunki rozwoju.",
      source: "Rozporządzenie PRM z 4.04.2016 r. · § 10",
    };
  if (/feedback|rozwoju|obserwacj|rozmaw|informację zwrotną/.test(query))
    return {
      answer:
        "Odwołaj się do konkretnej sytuacji, zaobserwowanego zachowania i rezultatu. Poproś pracownika o jego perspektywę, a na końcu uzgodnij możliwy krok rozwojowy.",
      source: "Wskazówka komunikacyjna · bez podstawy prawnej (mock)",
    };
  if (query.includes("zatwierdza"))
    return {
      answer:
        "Ocenę cząstkową ostatecznie ustala przełożony. Podpowiedzi modelu mają charakter pomocniczy i nie zastępują decyzji człowieka.",
      source: "Rozporządzenie PRM z 4.04.2016 r. · §§ 10–12",
    };
  return {
    answer:
      "Nie mam wystarczających danych źródłowych, aby udzielić zweryfikowanej odpowiedzi. W tym demo nie wykonujemy zapytań do modelu AI.",
    source: "Brak zweryfikowanej podstawy dla tego pytania",
  };
}
