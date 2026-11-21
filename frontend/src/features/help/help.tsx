import { Card, Note, PageHeading } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import type { WorkspaceUser } from "@/features/auth/session";

const roles = [
  {
    id: "MANAGER",
    title: "Przełożony",
    icon: "file-check",
    description: "Prowadzisz własne oceny przypisanych Ci pracowników.",
    items: [
      "Widzisz profile przypisanych pracowników oraz oceny, które samodzielnie prowadzisz.",
      "Możesz rozpocząć ocenę okresową C, wybrać kryteria, zapisać terminy, zbierać obserwacje i potwierdzić odbytą rozmowę oceniającą.",
      "Nie widzisz ocen prowadzonych przez innego przełożonego, nawet jeśli ten sam pracownik jest również Tobie przypisany.",
    ],
    action: "Przejdź do swoich ocen",
    href: "/assessments",
  },
  {
    id: "HR",
    title: "HR",
    icon: "users",
    description: "Wspierasz organizację procesu ocen w urzędzie.",
    items: [
      "Widzisz podstawowe dane pracowników w organizacji.",
      "Sama rola HR nie pozwala prowadzić ani zatwierdzać ocen. Nie udostępnia też notatek ani ocen cząstkowych przełożonego.",
      "Monitoring postępów i terminów jest w przygotowaniu. Obecny widok HR pokazuje dane demonstracyjne — nie traktuj ich jako aktualnego stanu ocen.",
    ],
    action: "Przejdź do pracowników",
    href: "/employees",
  },
  {
    id: "ADMIN",
    title: "Administrator",
    icon: "shield",
    description: "Odpowiadasz za dostęp do aplikacji i przypisanie osób.",
    items: [
      "Widzisz podstawowe profile pracowników w organizacji.",
      "Sama rola administratora nie daje dostępu do treści ocen ani do panelu HR. Do prowadzenia ocen potrzebujesz również roli przełożonego i przypisania pracownika.",
      "Panel zarządzania kontami, rolami i przypisaniami nie jest jeszcze dostępny. Zmiany wykonuje obecnie osoba obsługująca wdrożenie.",
    ],
    action: "Sprawdź listę pracowników",
    href: "/employees",
  },
] as const;

const questions = [
  [
    "Jak rozpocząć ocenę?",
    "Jeśli jesteś przełożonym, otwórz Oceny → Nowa ocena. Wybierz przypisaną osobę i utwórz ocenę okresową C. Następnie wybierz kryteria, zapisz terminy i odnotuj czynności z rozmowy. Arkusze A/B i pierwsza ocena nie są jeszcze dostępne.",
  ],
  [
    "Nie widzę pracownika lub jego oceny. Co zrobić?",
    "Poproś administratora o sprawdzenie Twojej roli i przypisania pracownika. Jeśli masz już przypisanie, ale nie ma oceny, jako przełożony możesz rozpocząć nową. Ocena prowadzona przez inną osobę nie pojawi się na Twojej liście. HR i administrator nie otrzymują dostępu do jej treści tylko z racji swojej roli.",
  ],
  [
    "Jak wrócić do zapisanej pracy?",
    "Otwórz Oceny i wybierz rozpoczętą ocenę. Własną historię ocen znajdziesz też na profilu pracownika. Używaj przycisków zapisu — niewysłane wpisy nie zapisują się automatycznie. Zapisane dane są w bazie i możesz do nich wrócić po ponownym zalogowaniu.",
  ],
  [
    "Co zrobić, gdy ocena zmieniła się w innej karcie?",
    "Nie zamykaj formularza z własnymi wpisami. Otwórz zapisaną wersję w nowej karcie za pomocą odnośnika w komunikacie, porównaj dane i przenieś potrzebne zmiany. Aplikacja nie nadpisze nowszego zapisu automatycznie.",
  ],
  [
    "Co oznacza potwierdzenie ustaleń?",
    "Rejestrujesz, że rozmowa i wskazane czynności się odbyły. Najpierw zapisz kryteria, obie daty i trzy potwierdzenia. Po potwierdzeniu ustaleń kryteria i terminy są na tym etapie tylko do odczytu. To nie jest podpis pracownika ani potwierdzenie doręczenia dokumentu.",
  ],
  [
    "Jak zapisywać obserwacje i rozmowę oceniającą?",
    "Po potwierdzeniu kryteriów i terminów otwórz Obserwacje i wybierz Rozpocznij okres obserwacji. Każdy przykład powiąż z kryterium i datą zdarzenia. W zakładce Rozmowa oceniająca możesz osobno zapisać agendę, mocne strony i obszary rozwoju. Szkic nie wymaga daty. Po rozmowie zapisz jej rzeczywistą datę i dopiero wtedy potwierdź, że się odbyła. To zamknie edycję obserwacji i rozmowy. Ich teksty są opcjonalne; niewysłane wpisy nie zapisują się automatycznie.",
  ],
  [
    "Jak zatwierdzić ocenę kryterium?",
    "Po potwierdzeniu rozmowy otwórz zakładkę Ocena zachowań. Wybierz opisy pasujące do zaobserwowanych zachowań i zapisz odpowiedzi. Jeśli nie masz podstaw do oceny zachowania, zaznacz brak obserwacji. System przedstawi propozycję, ale decyzja należy do Ciebie: wybierz i zatwierdź ocenę każdego kryterium. Po zmianie odpowiedzi lub notatki zatwierdź to kryterium ponownie. Zatwierdzenie kryteriów nie kończy całego procesu oceny.",
  ],
  [
    "Skąd pochodzą kryteria i co jest jeszcze w przygotowaniu?",
    "Kryteria i pełne opisy zachowań pochodzą z wgranego modelu kompetencji. Każda ocena zachowuje swoją wersję katalogu. W zakładce „Wynik i zakończenie” sprawdzisz wynik zatwierdzonych ocen, zapiszesz wnioski rozwojowe i zakończysz proces. Wynik negatywny wymaga uzasadnienia. Po zakończeniu dane są tylko do odczytu; ten zapis nie oznacza podpisania ani doręczenia dokumentu. Dokumenty, analiza OSP i asystent AI są w przygotowaniu. Pulpit, Terminy i widok HR zawierają jeszcze dane demonstracyjne. W sprawie właściwych terminów i procedury skonsultuj się z HR.",
  ],
];

export function Help({ userRoles }: { userRoles: WorkspaceUser["roles"] }) {
  return (
    <>
      <PageHeading
        eyebrow="Centrum pomocy"
        title="Jak pracować z OcenoMat?"
        description="Sprawdź, co możesz zrobić na swoim koncie i jak przejść do kolejnego kroku."
      />
      <div className="mb-6 grid gap-4 lg:grid-cols-3">
        {roles.map((role) => (
          <Card
            key={role.id}
            className={`flex flex-col p-6 ${userRoles.includes(role.id) ? "border-primary-border" : ""}`}
          >
            <div className="flex items-start gap-3">
              <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-surface-muted text-primary">
                <Icon name={role.icon} size={20} />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-sm font-semibold">{role.title}</h2>
                  {userRoles.includes(role.id) ? <Badge tone="primary">Twoja rola</Badge> : null}
                </div>
                <p className="mt-2 text-body leading-5 text-muted-foreground">{role.description}</p>
              </div>
            </div>
            <ul className="mt-5 mb-6 space-y-3 border-t pt-4 text-body leading-6 text-muted-foreground">
              {role.items.map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <span
                    aria-hidden="true"
                    className="mt-2.5 size-1.5 shrink-0 rounded-full bg-primary"
                  />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            {userRoles.includes(role.id) ? (
              <ButtonLink href={role.href} className="mt-auto">
                {role.action}
                <Icon name="arrow-up-right" size={15} />
              </ButtonLink>
            ) : null}
          </Card>
        ))}
      </div>
      <Note className="mb-6 flex items-start gap-3">
        <Icon name="info" size={18} className="mt-0.5 shrink-0 text-primary" />
        <p>
          Jedno konto może mieć kilka ról. Do prowadzenia oceny zawsze potrzebujesz roli
          przełożonego i przypisania pracownika. Jeśli brakuje Ci dostępu, podaj administratorowi
          swój adres logowania oraz imię i nazwisko pracownika. Administrator zleci zmianę osobie
          obsługującej wdrożenie.
        </p>
      </Note>
      <Card className="p-6 sm:p-7">
        <h2 className="mb-3 text-sm font-semibold">Najczęstsze pytania</h2>
        {questions.map(([question, answer]) => (
          <details key={question} className="group border-b py-4 last:border-0">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-body font-semibold">
              {question}
              <Icon
                name="chevron-down"
                size={17}
                className="shrink-0 text-subtle-foreground group-open:rotate-180"
              />
            </summary>
            <p className="mt-3 pr-5 text-body leading-6 text-muted-foreground">{answer}</p>
          </details>
        ))}
      </Card>
    </>
  );
}
