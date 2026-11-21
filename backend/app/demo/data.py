"""Authored fictional cases, not an employee register or legal knowledge source."""

# ruff: noqa: E501

from dataclasses import dataclass


@dataclass(frozen=True)
class Person:
    name: str
    position: str
    task: str
    evidence: str
    development: str


@dataclass(frozen=True)
class Team:
    slug: str
    name: str
    mission: str
    knowledge: str
    additional: tuple[str, ...]
    people: tuple[Person, ...]


TEAMS = (
    Team(
        "cyber",
        "Departament Cyberbezpieczeństwa / Wydział Zarządzania Kryzysowego",
        "Utrzymanie gotowości do reagowania na sytuacje kryzysowe w cyberprzestrzeni "
        "oraz uzgadnianie procedur z właściwymi zespołami CSIRT i administracją.",
        "Zarządzanie kryzysowe, krajowy system cyberbezpieczeństwa, obieg informacji "
        "i dokumentowanie uzgodnień. Bez dostępu do rzeczywistych danych incydentów.",
        ("MYŚLENIE ANALITYCZNE", "RADZENIE SOBIE W SYTUACJACH KRYZYSOWYCH"),
        (
            Person(
                "Michał Sokołowski",
                "Naczelnik wydziału",
                "Planowanie ćwiczeń gotowości i podział odpowiedzialności w wydziale.",
                "Przed ćwiczeniem uzgodnił z ośmioosobowym zespołem role, zastępstwa "
                "i dwa punkty kontrolne. Po ćwiczeniu przypisał właścicieli pięciu zaleceń.",
                "Wprowadzić miesięczny przegląd realizacji zaleceń, zamiast wracać do nich dopiero przed kolejnym ćwiczeniem.",
            ),
            Person(
                "Katarzyna Wysocka",
                "Starszy specjalista",
                "Aktualizacja procedury eskalacji i przygotowanie kart zadań do ćwiczeń.",
                "W porównaniu dwóch wersji procedury wykryła sprzeczne czasy eskalacji. "
                "Przedstawiła tabelę różnic i uzyskała wspólne rozstrzygnięcie przed ćwiczeniem.",
                "Przy kolejnej aktualizacji wcześniej przekazać partnerom krótkie podsumowanie zmian; pełny dokument dotarł zbyt późno na pierwsze spotkanie.",
            ),
            Person(
                "Łukasz Brzeziński",
                "Główny specjalista",
                "Analiza wniosków z ćwiczeń i przygotowanie rekomendacji zmian procedur.",
                "Oddzielił problemy techniczne od niejasnego podziału ról w 18 uwagach "
                "uczestników. Dla trzech zaleceń wskazał miernik sprawdzenia skuteczności.",
                "Ograniczyć prezentację dla kierownictwa do decyzji, ryzyk i rekomendacji; szczegóły techniczne przenieść do załącznika.",
            ),
            Person(
                "Joanna Cieślak",
                "Specjalista",
                "Prowadzenie rejestru uzgodnień i obsługa spotkań roboczych dotyczących gotowości.",
                "Po spotkaniu odtworzyła brakujące potwierdzenia dwóch uzgodnień i zamknęła "
                "rejestr dopiero po sprawdzeniu ich z właścicielami zadań.",
                "Samodzielnie przygotować plan następnego spotkania z rozdzieleniem tematów informacyjnych i wymagających decyzji.",
            ),
            Person(
                "Adam Wilczyński",
                "Starszy specjalista",
                "Uzgadnianie scenariuszy ćwiczeń z partnerami i kontrola gotowości materiałów.",
                "Przy zmianie terminu ćwiczenia przeliczył zależności i zaproponował "
                "wariant ograniczony, który zachował cele bez angażowania całego zespołu.",
                "Dokumentować przesłanki odrzucenia wariantów, aby zastępca mógł odtworzyć tok uzgodnień.",
            ),
            Person(
                "Robert Kubiak",
                "Specjalista",
                "Utrzymywanie kart kontaktowych i zestawienia gotowości do ćwiczeń.",
                "W dwóch kolejnych przeglądach przekazał karty z niepotwierdzonymi danymi "
                "i dopiero po uwagach opiekuna uzupełnił źródła. Trzy uzgodnione terminy "
                "minęły bez zgłoszenia ryzyka. Ponowne sprawdzenie wymagało pracy drugiej osoby.",
                "Przez sześć tygodni stosować checklistę kontroli źródeł i dwa krótkie przeglądy tygodniowo; po tym okresie sprawdzić samodzielność i terminowość.",
            ),
            Person(
                "Natalia Zawadzka",
                "Referent",
                "Porządkowanie dokumentacji ćwiczeń i przygotowanie zestawień terminów.",
                "Przy pierwszym samodzielnym zestawieniu wskazała brak właściciela dwóch "
                "zadań i uzgodniła korektę z opiekunem przed rozesłaniem materiału.",
                "Przećwiczyć samodzielne przygotowanie notatki z uzgodnień i rozróżnianie informacji roboczej od zatwierdzonej.",
            ),
            Person(
                "Filip Ostrowski",
                "Inspektor",
                "Weryfikacja kompletności materiałów do przeglądu gotowości.",
                "Sprawdził 24 karty według uzgodnionej listy; cztery braki opisał tak, "
                "że właściciele uzupełnili je bez dodatkowego spotkania.",
                "Poszerzyć znajomość zależności między dokumentami, nie ograniczać sprawdzenia do obecności wymaganych pól.",
            ),
            Person(
                "Ewa Rutkowska",
                "Główny specjalista",
                "Koordynacja przeglądu zaleceń po ćwiczeniach i ocena ryzyka niewykonania.",
                "Przy zaległym zaleceniu ustaliła rzeczywistą blokadę między dwiema "
                "komórkami i uzgodniła etap pośredni zamiast przesuwać cały termin.",
                "Przekazywać przełożonemu ryzyka przed cotygodniowym przeglądem, z propozycją decyzji i właścicielem działania.",
            ),
            Person(
                "Tomasz Jaworski",
                "Starszy specjalista",
                "Przygotowanie harmonogramu przeglądu procedur i materiałów szkoleniowych.",
                "Uporządkował materiały według odbiorców i wykazał, które instrukcje "
                "wymagają aktualizacji po zmianie procedury eskalacji.",
                "Uzgodnić z odbiorcami sposób sprawdzenia zrozumienia nowych instrukcji.",
            ),
        ),
    ),
    Team(
        "ai",
        "Departament Rozwoju i Bezpieczeństwa Sztucznej Inteligencji / Wydział Wspierania Innowacyjności",
        "Przygotowanie analiz, wyjaśnień i materiałów wspierających bezpieczne "
        "wykorzystanie sztucznej inteligencji oraz spójne rozpatrywanie zagadnień regulacyjnych.",
        "Prawo krajowe i unijne dotyczące AI, analiza źródeł, prowadzenie konsultacji "
        "oraz odróżnianie stanowiska roboczego od zatwierdzonej interpretacji.",
        ("MYŚLENIE ANALITYCZNE", "KREATYWNOŚĆ"),
        (
            Person(
                "Aleksandra Kurek",
                "Naczelnik wydziału",
                "Planowanie prac analitycznych i zapewnianie spójności odpowiedzi wydziału.",
                "Rozdzieliła pilne pytania od zagadnień wymagających analizy prawnej. "
                "Wprowadziła przegląd rozbieżnych stanowisk przed ich przekazaniem do akceptacji.",
                "Delegować prowadzenie przeglądów spraw starszym specjalistom, pozostawiając sobie decyzje o priorytetach.",
            ),
            Person(
                "Monika Borkowska",
                "Radca",
                "Analiza pytań o kwalifikację zastosowań AI i przygotowanie projektów wyjaśnień.",
                "W analizie pilotażu rozdzieliła opis technologii od celu użycia i brakujących "
                "informacji. Zamiast przesądzać kwalifikację, przygotowała pięć pytań do wnioskodawcy.",
                "Na początku opinii wyraźnie oddzielać ustalenia, założenia i kwestie wymagające decyzji; uzgodnić krótszy wzór podsumowania.",
            ),
            Person(
                "Paweł Lis",
                "Główny specjalista",
                "Prowadzenie konsultacji roboczych dotyczących bezpiecznego wykorzystania AI.",
                "Zebrał sprzeczne uwagi z czterech komórek w macierzy problem–propozycja. "
                "Podczas spotkania uzgodnił wspólny opis ryzyk bez ukrywania różnicy stanowisk.",
                "Rezerwować czas na podsumowanie decyzji i wskazanie spraw pozostawionych otwartych.",
            ),
            Person(
                "Karolina Wrona",
                "Starszy specjalista",
                "Przygotowanie porównań dokumentów i projektów odpowiedzi na wystąpienia.",
                "Oznaczyła w projekcie odpowiedzi twierdzenia bez aktualnego źródła "
                "i uzupełniła je przed przekazaniem materiału do akceptacji.",
                "Rozwijać samodzielne formułowanie rekomendacji, a nie tylko zestawianie dostępnych stanowisk.",
            ),
            Person(
                "Grzegorz Mazur",
                "Radca",
                "Przegląd projektów wyjaśnień i identyfikacja zależności między regulacjami.",
                "Dla niejednoznacznego pytania przedstawił dwa warianty odpowiedzi "
                "z przesłankami i skutkami każdego z nich; pozwoliło to zamknąć uzgodnienie na jednym spotkaniu.",
                "Wcześniej sygnalizować wpływ dodatkowych pytań na termin opinii.",
            ),
            Person(
                "Dorota Kalinowska",
                "Specjalista",
                "Prowadzenie rejestru pytań interesariuszy i redakcja materiałów informacyjnych.",
                "Po uwagach odbiorców przeformułowała sześć odpowiedzi na prostszy język, "
                "zachowując zastrzeżenia prawne i ślad do materiału źródłowego.",
                "Przy redakcji kolejnej partii materiałów samodzielnie oznaczyć miejsca, w których uproszczenie może zmienić sens.",
            ),
            Person(
                "Wiktoria Sikora",
                "Referent",
                "Wyszukiwanie materiałów źródłowych i dokumentowanie przebiegu konsultacji.",
                "Przygotowała zestawienie źródeł z datą i statusem dokumentu. "
                "Dwa projekty oznaczyła jako nieobowiązujące zamiast traktować je jak przyjęte przepisy.",
                "Ćwiczyć krótkie opisy przydatności źródła do konkretnego pytania.",
            ),
            Person(
                "Mateusz Czarnecki",
                "Inspektor",
                "Przygotowanie roboczych zestawień uwag i obsługa korespondencji konsultacyjnej.",
                "Po instruktażu prawidłowo połączył powtarzające się uwagi i zachował "
                "rozróżnienie między postulatem zmiany a pytaniem o wyjaśnienie.",
                "Przy kolejnej konsultacji samodzielnie zaproponować kategorie spraw i sprawdzić ich użyteczność z opiekunem.",
            ),
            Person(
                "Agnieszka Gajda",
                "Główny specjalista",
                "Analiza rezultatów pilotaży i opracowanie rekomendacji do materiałów informacyjnych.",
                "W raporcie z pilotażu oddzieliła deklaracje uczestników od pomiarów. "
                "Wskazała, których wniosków nie można uogólnić na inne urzędy.",
                "Uzgodnić kryteria pomiaru przed kolejnym pilotażem, aby ograniczyć późniejsze braki danych.",
            ),
            Person(
                "Bartosz Wójcik",
                "Starszy specjalista",
                "Przygotowanie warsztatów dla administracji o odpowiedzialnym wykorzystaniu AI.",
                "Przetestował scenariusz warsztatu na małej grupie i zamienił wykład "
                "na analizę trzech przypadków po uwagach uczestników.",
                "Dodać sprawdzenie, czy uczestnicy potrafią rozpoznać brak podstaw do odpowiedzi.",
            ),
        ),
    ),
    Team(
        "services",
        "Departament Usług Cyfrowych / Wydział Rozwoju Usług",
        "Przygotowanie zmian usług publicznych na podstawie potrzeb użytkowników, "
        "uzgodnień z właścicielami procesów i wyników odbiorów.",
        "Projektowanie usług publicznych, dostępność cyfrowa, kryteria akceptacji, "
        "analiza zgłoszeń i współpraca z zespołami wdrożeniowymi.",
        ("ORIENTACJA NA KLIENTA/INTERESANTA", "MYŚLENIE ANALITYCZNE"),
        (
            Person(
                "Marcin Domański",
                "Naczelnik wydziału",
                "Koordynowanie portfela zmian usług i uzgadnianie priorytetów odbiorów.",
                "Przy kolizji dwóch wdrożeń uzgodnił wspólne kryterium pilności "
                "i odroczył mniejszą zmianę bez utraty terminu obowiązkowego odbioru.",
                "Wyznaczyć zastępców właścicieli usług i przetestować przekazanie decyzji podczas nieobecności.",
            ),
            Person(
                "Zuzanna Kaczmarek",
                "Główny specjalista",
                "Analiza ścieżek użytkownika i przygotowanie wymagań do zmian formularzy.",
                "Na podstawie 32 zgłoszeń wykazała, że błąd dotyczy opisu wymaganych "
                "załączników, a nie walidatora. Zmianę sprawdziła z obsługą i użytkownikami.",
                "Do każdej rekomendacji dołączyć punkt odniesienia, aby po wdrożeniu zmierzyć zmianę liczby zgłoszeń.",
            ),
            Person(
                "Damian Szymański",
                "Starszy specjalista",
                "Uzgadnianie kryteriów odbioru i prowadzenie rejestru decyzji dla usługi.",
                "Wychwycił sprzeczność między opisem procesu a protokołem odbioru. "
                "Przed testami uzgodnił jedno kryterium z właścicielem merytorycznym.",
                "Odróżniać w rejestrze decyzję od propozycji wykonawcy i domykać potwierdzenie właściciela.",
            ),
            Person(
                "Marta Jasińska",
                "Specjalista",
                "Redakcja komunikatów usługi i porządkowanie zgłoszeń użytkowników.",
                "Zastąpiła niezrozumiały komunikat o błędzie instrukcją naprawy. "
                "Po konsultacji zachowała informację o sposobie kontaktu i ograniczeniach usługi.",
                "Sprawdzać komunikaty również w scenariuszu błędnego załącznika i przerwania procesu.",
            ),
            Person(
                "Krzysztof Malinowski",
                "Główny specjalista",
                "Planowanie odbiorów zmian i monitorowanie zależności między usługami.",
                "Przed odbiorem zidentyfikował zależność od zewnętrznego słownika "
                "i uzgodnił test na nieaktualnej wartości zamiast poprzestać na scenariuszu poprawnym.",
                "W harmonogramie uwzględniać czas na ponowny odbiór po poprawkach.",
            ),
            Person(
                "Ilona Sobczak",
                "Starszy specjalista",
                "Analiza uwag dostępności i przygotowanie zadań naprawczych.",
                "Po przeglądzie formularza opisała problemy jako odtwarzalne kroki "
                "z oczekiwanym rezultatem. Wykonawca odtworzył pięć z sześciu zgłoszeń bez doprecyzowania.",
                "Do zgłoszeń niejednoznacznych dodawać warunki początkowe i wersję testowanego formularza.",
            ),
            Person(
                "Julia Walczak",
                "Referent",
                "Rejestracja uwag do usług i przygotowanie materiałów do spotkań odbiorowych.",
                "Przy porządkowaniu zgłoszeń wykryła dwa duplikaty i zachowała "
                "obie perspektywy użytkowników w opisie jednego problemu.",
                "Samodzielnie przygotować zestawienie spraw do decyzji, zamiast przedstawiać wyłącznie liczbę zgłoszeń.",
            ),
            Person(
                "Oskar Michalak",
                "Inspektor",
                "Weryfikacja dokumentacji odbiorowej i sprawdzanie kompletności odpowiedzi.",
                "Przed spotkaniem wskazał trzy kryteria bez wyniku testu i uzyskał "
                "uzupełnienie protokołu. Nie oznaczył brakujących testów jako zakończonych.",
                "Rozwijać umiejętność oceny jakości dowodu testowego, nie tylko sprawdzania jego obecności.",
            ),
            Person(
                "Renata Król",
                "Radca",
                "Uzgadnianie zmian organizacyjnych niezbędnych do uruchomienia usług.",
                "Przy zmianie obsługi spraw ustaliła właścicieli dwóch wyjątków "
                "procesowych, które wcześniej przechodziły między komórkami bez rozstrzygnięcia.",
                "Ustalić wspólny termin na uwagi do kolejnej wersji procesu i wcześniej eskalować brak odpowiedzi.",
            ),
            Person(
                "Sebastian Urban",
                "Specjalista",
                "Przygotowanie instrukcji dla obsługi nowej wersji usługi.",
                "Po rozmowie z punktem wsparcia uzupełnił instrukcję o trzy najczęstsze "
                "sytuacje wyjątkowe i sposób zgłoszenia nierozwiązanej sprawy.",
                "Sprawdzić instrukcję na osobie, która nie uczestniczyła w projekcie.",
            ),
        ),
    ),
    Team(
        "data",
        "Departament Zarządzania Danymi / Wydział Jakości i Udostępniania Danych",
        "Podnoszenie jakości i użyteczności danych udostępnianych przez administrację "
        "oraz uzgadnianie zasad ich opisu i aktualizacji.",
        "Metadane, jakość danych, otwarte dane, kontrola źródeł i minimalizacja "
        "danych osobowych w materiałach analitycznych.",
        ("MYŚLENIE ANALITYCZNE", "WSPÓŁPRACA"),
        (
            Person(
                "Beata Włodarczyk",
                "Naczelnik wydziału",
                "Planowanie przeglądów jakości i współpracy z dostawcami danych.",
                "Podzieliła przegląd 40 zbiorów według ryzyka i uzgodniła właścicieli "
                "korekt. Zespół zakończył najpilniejsze przeglądy bez równoległego otwierania wszystkich spraw.",
                "Uzgodnić sposób mierzenia skuteczności korekt, nie ograniczać raportu do liczby zamkniętych zgłoszeń.",
            ),
            Person(
                "Szymon Pawlak",
                "Główny specjalista",
                "Analiza jakości zbiorów i opracowanie reguł kontroli spójności.",
                "Wykrył, że skok wskaźnika wynika ze zmiany definicji, a nie zjawiska. "
                "Dodał opis przerwy porównywalności i uzgodnił korektę metadanych z dostawcą.",
                "W komunikacie dla odbiorcy nietechnicznego pokazywać skutek nieporównywalności przed opisem reguły kontroli.",
            ),
            Person(
                "Magdalena Grabowska",
                "Starszy specjalista",
                "Uzgadnianie opisów zbiorów i harmonogramów aktualizacji.",
                "Przy trzech nieaktualizowanych zbiorach ustaliła przyczynę i właściciela. "
                "Dla jednego zaproponowała zmianę częstotliwości zamiast pozornego potwierdzenia aktualności.",
                "Zapisywać w rejestrze także termin ponownego sprawdzenia uzgodnionej poprawki.",
            ),
            Person(
                "Artur Wesołowski",
                "Specjalista",
                "Przygotowanie zestawień kompletności metadanych i kontrola opisów pól.",
                "Po przeglądzie 15 opisów odnalazł różne znaczenia tej samej nazwy pola. "
                "Przed publikacją uzgodnił słownik pojęć z właścicielem danych.",
                "Poszerzyć kontrolę o jednostki miary i zakres czasowy danych.",
            ),
            Person(
                "Elżbieta Chmielewska",
                "Radca",
                "Opiniowanie zakresu udostępniania danych i warunków ich wykorzystania.",
                "W opinii rozdzieliła dane możliwe do udostępnienia od pól wymagających "
                "dalszej analizy. Zaproponowała ograniczony zakres, zamiast wstrzymywać cały zbiór.",
                "Dokumentować założenia opinii tak, aby późniejsza zmiana zakresu danych uruchamiała ponowny przegląd.",
            ),
            Person(
                "Wojciech Baran",
                "Starszy specjalista",
                "Wsparcie dostawców przy korektach jakości i analizie zgłoszeń odbiorców.",
                "Przeprowadził dostawcę przez odtworzenie błędu kodowania i przygotował "
                "krótką instrukcję sprawdzenia pliku przed następną publikacją.",
                "Po udzieleniu wsparcia sprawdzać samodzielne wykonanie kontroli przez dostawcę.",
            ),
            Person(
                "Lena Marciniak",
                "Referent",
                "Kontrola kompletności zgłoszeń zbiorów i porządkowanie dokumentacji.",
                "W pierwszej partii zgłoszeń wskazała brak zakresu czasowego i opisu "
                "aktualizacji. Pytania do dostawcy zebrała w jednym piśmie zamiast wysyłać je osobno.",
                "Uczyć się odróżniania braku formalnego od problemu z jakością treści.",
            ),
            Person(
                "Igor Błaszczyk",
                "Inspektor",
                "Sprawdzanie zgodności plików z opisem i prowadzenie rejestru korekt.",
                "Porównał liczbę rekordów z opisem i wykrył pominięcie jednego okresu. "
                "Zgłosił rozbieżność przed zamknięciem kontroli.",
                "Rozszerzyć testy o wartości puste i duplikaty identyfikatorów.",
            ),
            Person(
                "Paulina Dudek",
                "Główny specjalista",
                "Przygotowanie analiz wykorzystania zbiorów i priorytetów ich poprawy.",
                "Porównała zgłoszenia odbiorców z częstotliwością aktualizacji i wskazała "
                "trzy zbiory, w których korekta opisu była pilniejsza od rozbudowy zakresu.",
                "Przedstawiać ograniczenia analizy także na slajdzie podsumowującym, nie tylko w aneksie.",
            ),
            Person(
                "Marek Przybylski",
                "Specjalista",
                "Opracowanie instrukcji opisu zbiorów dla nowych dostawców.",
                "Po sprawdzeniu instrukcji z dwoma dostawcami uzupełnił ją o przykłady "
                "błędnych i poprawnych metadanych.",
                "Sprawdzić, czy instrukcja ogranicza liczbę pytań przy kolejnych zgłoszeniach.",
            ),
        ),
    ),
    Team(
        "international",
        "Departament Współpracy Międzynarodowej / Wydział Koordynacji Aktywności Międzynarodowych",
        "Zapewnienie przygotowania aktywności międzynarodowych kierownictwa "
        "i spójnych materiałów do spotkań dotyczących polityki cyfrowej.",
        "Koordynacja wizyt, przygotowanie materiałów tezowo-informacyjnych, "
        "obieg akceptacji, planowanie wydatków i roboczy język angielski.",
        ("WSPÓŁPRACA", "NEGOCJOWANIE"),
        (
            Person(
                "Andrzej Dąbrowski",
                "Naczelnik wydziału",
                "Planowanie aktywności międzynarodowych i koordynacja przygotowań zespołu.",
                "Przy zmianie programu wizyty w ciągu dwóch dni przeorganizował zadania "
                "i wskazał jednego właściciela każdej akceptacji. Nie przeniósł presji na wszystkie osoby jednakowo.",
                "Zwiększyć wymienność w zespole, powierzając prowadzenie mniejszych wydarzeń dwóm kolejnym osobom.",
            ),
            Person(
                "Anna Leszczyńska",
                "Radca",
                "Przygotowanie tez i materiałów do spotkań bilateralnych o polityce cyfrowej.",
                "W materiale do spotkania rozdzieliła wspólne interesy, rozbieżności "
                "i propozycje dalszych prac. Po uwagach skróciła dokument do dwóch stron decyzji.",
                "Wcześniej uzgadniać granice stanowiska z komórkami merytorycznymi.",
            ),
            Person(
                "Jakub Nowicki",
                "Starszy specjalista",
                "Koordynacja programu wizyt i uzgadnianie materiałów z komórkami urzędu.",
                "Przygotował harmonogram akceptacji z rezerwą na tłumaczenie i wskazał "
                "konsekwencje spóźnionego wkładu przed upływem terminu.",
                "Po spotkaniu zamykać rejestr zadań wraz z potwierdzeniem właścicieli dalszych działań.",
            ),
            Person(
                "Iwona Pietrzak",
                "Specjalista",
                "Obsługa korespondencji roboczej i aktualizacja kalendarza spotkań.",
                "Po zmianie godziny spotkania sprawdziła potwierdzenia wszystkich "
                "uczestników i odnalazła kolizję z połączeniem zdalnym przed rozesłaniem programu.",
                "Samodzielnie przygotować wariant awaryjny programu dla krótkiej wizyty.",
            ),
            Person(
                "Rafał Sawicki",
                "Główny specjalista",
                "Planowanie wydarzeń międzynarodowych i uzgadnianie zakresu współpracy.",
                "W uzgodnieniu wydarzenia oddzielił elementy konieczne od opcjonalnych "
                "i zaproponował wariant mieszczący się w limicie organizacyjnym.",
                "Po trudnych uzgodnieniach zapisywać również ustępstwa i warunki powrotu do rozmów.",
            ),
            Person(
                "Sylwia Majewska",
                "Starszy specjalista",
                "Monitorowanie rozliczeń wydarzeń i przygotowanie zestawień wydatków.",
                "Przed zamknięciem zestawienia znalazła brak powiązania trzech kosztów "
                "z wydarzeniem i uzyskała uzupełnienie dokumentacji od właścicieli.",
                "Wprowadzić kontrolę kompletności na etapie przygotowań, nie dopiero przy rozliczeniu.",
            ),
            Person(
                "Kinga Stępień",
                "Referent",
                "Przygotowanie pakietów materiałów i rejestrowanie uzgodnień organizacyjnych.",
                "W pakiecie na spotkanie wykryła nieaktualną wersję programu i potwierdziła "
                "właściwą z koordynatorem przed dystrybucją.",
                "Wzmocnić samodzielność przy krótkiej korespondencji po angielsku.",
            ),
            Person(
                "Hubert Kozłowski",
                "Inspektor",
                "Aktualizacja list uczestników i dokumentowanie zmian programu wizyt.",
                "Prowadził jedną listę zmian z datą i źródłem potwierdzenia. Dzięki temu "
                "zespół odtworzył decyzję o zmianie kolejności spotkań bez dodatkowych telefonów.",
                "Przy zmianie programu od razu wskazywać jej wpływ na transport i materiały.",
            ),
            Person(
                "Danuta Sadowska",
                "Radca",
                "Przegląd wkładów merytorycznych i przygotowanie wspólnych podsumowań spotkań.",
                "Ujednoliciła trzy niespójne wkłady, zachowując widoczne zastrzeżenia "
                "komórek. Sporne zagadnienie przekazała do decyzji zamiast redakcyjnie je ukryć.",
                "Uzgodnić krótszą ścieżkę akceptacji dla drobnych zmian redakcyjnych.",
            ),
            Person(
                "Norbert Zieliński",
                "Specjalista",
                "Przygotowanie informacji logistycznych do wizyt roboczych.",
                "Sprawdził pakiet informacji z osobą niezaangażowaną w przygotowania "
                "i uzupełnił brakującą instrukcję dołączenia do spotkania.",
                "Planować sprawdzenie materiałów z większym wyprzedzeniem.",
            ),
        ),
    ),
    Team(
        "hr",
        "Biuro Dyrektora Generalnego / Wydział Rozwoju Zawodowego",
        "Organizacja procesów rozwoju zawodowego i wsparcie przełożonych "
        "w prowadzeniu udokumentowanych, terminowych ocen pracowniczych.",
        "Procesy kadrowe służby cywilnej, organizacja szkoleń, ochrona informacji "
        "pracowniczych i przygotowanie zagregowanej informacji zarządczej.",
        ("ORIENTACJA NA KLIENTA/INTERESANTA", "WSPÓŁPRACA"),
        (
            Person(
                "Teresa Kwiatkowska",
                "Naczelnik wydziału",
                "Planowanie wsparcia przełożonych i koordynacja działań rozwojowych.",
                "Przed spiętrzeniem terminów ocen rozdzieliła konsultacje od kontroli "
                "kompletności i uruchomiła dyżury według rzeczywistego zapotrzebowania komórek.",
                "Weryfikować po kwartale, czy wsparcie zmniejsza liczbę powracających błędów.",
            ),
            Person(
                "Jacek Lewandowski",
                "Główny specjalista",
                "Przygotowanie materiałów dla przełożonych i analiza potrzeb rozwojowych.",
                "W analizie potrzeb oddzielił postulaty szkoleniowe od problemów organizacji "
                "pracy. Zaproponował mentoring tam, gdzie pojedyncze szkolenie nie rozwiązałoby problemu.",
                "Uzgadniać sposób sprawdzenia rezultatu działań rozwojowych z przełożonym przed ich uruchomieniem.",
            ),
            Person(
                "Alicja Malec",
                "Starszy specjalista",
                "Konsultacje procesu ocen i przygotowanie zestawień terminów dla komórek.",
                "Wyjaśniła przełożonemu różnicę między brakującą dokumentacją a brakiem "
                "wykonania czynności. W zestawieniu pozostawiła nierozstrzygnięte pozycje do potwierdzenia.",
                "Przed konsultacją zbierać konkretne pytania, aby nie poświęcać całego spotkania na odtwarzanie stanu sprawy.",
            ),
            Person(
                "Patrycja Wróbel",
                "Specjalista",
                "Organizacja warsztatów o rozmowie oceniającej i zbieranie informacji zwrotnej.",
                "Po pierwszym warsztacie zebrała przykłady trudnych rozmów i zmieniła "
                "ćwiczenia w drugiej grupie, nie ujawniając danych osób opisanych przez uczestników.",
                "Dodać sprawdzenie zastosowania umiejętności po kilku tygodniach, poza samą ankietą satysfakcji.",
            ),
            Person(
                "Mariusz Adamczyk",
                "Radca",
                "Przegląd materiałów procesowych i wyjaśnianie wątpliwości formalnych.",
                "W materiale informacyjnym oznaczył przepis, zalecenie organizacyjne "
                "i przykład. Wycofał z obiegu wersję, która mieszała te trzy kategorie.",
                "Przygotowywać krótką odpowiedź dla przełożonego przed rozbudowanym uzasadnieniem.",
            ),
            Person(
                "Bożena Piotrowska",
                "Starszy specjalista",
                "Koordynacja planów szkoleń i monitorowanie realizacji uzgodnień rozwojowych.",
                "Przy ograniczeniu budżetu porównała potrzeby i wskazała działania "
                "wewnętrzne, które można rozpocząć bez oczekiwania na zakup szkolenia.",
                "Przy zmianie planu zapisywać, kto potwierdził nowy termin i sposób realizacji.",
            ),
            Person(
                "Emilia Szymańska",
                "Referent",
                "Porządkowanie zgłoszeń szkoleniowych i przygotowanie komunikacji do uczestników.",
                "Przed wysłaniem list sprawdziła uprawnienia odbiorców i rozdzieliła "
                "informacje organizacyjne od indywidualnych uzasadnień potrzeb.",
                "Rozwijać samodzielne ustalanie priorytetów przy jednoczesnych zgłoszeniach z kilku komórek.",
            ),
            Person(
                "Daniel Wierzbicki",
                "Inspektor",
                "Kontrola kompletności dokumentacji rozwojowej i rejestracja uzgodnień.",
                "Wykrył brak terminu sprawdzenia rezultatu w czterech planach i zebrał "
                "uzupełnienia bez przesyłania całych dokumentów do nieuprawnionych odbiorców.",
                "Uczyć się formułowania pytań o mierzalny rezultat działania rozwojowego.",
            ),
            Person(
                "Grażyna Szewczyk",
                "Główny specjalista",
                "Przygotowanie zagregowanych informacji o przebiegu procesów rozwojowych.",
                "W raporcie oddzieliła procesy zakończone od wymagających potwierdzenia "
                "i nie przedstawiła brakujących odpowiedzi jako wykonanych czynności.",
                "Wcześniej uzgadniać definicje wskaźników z odbiorcami raportu.",
            ),
            Person(
                "Przemysław Kucharski",
                "Specjalista",
                "Przygotowanie instrukcji dla nowych przełożonych i organizacja konsultacji.",
                "Po konsultacjach uporządkował instrukcję według decyzji przełożonego "
                "zamiast układu dokumentów, dzięki czemu uczestnicy samodzielnie odnajdywali kolejny krok.",
                "Zweryfikować instrukcję na osobach prowadzących pierwszą ocenę po raz pierwszy.",
            ),
        ),
    ),
)
