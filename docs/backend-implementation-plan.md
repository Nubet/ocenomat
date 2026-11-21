# Kompas Kompetencji — plan wdrożenia backendu

Status: plan wykonawczy, przed rozpoczęciem etapu 1. Ostatnia analiza: 2026-11-21.

Ten dokument jest źródłem decyzji dla kolejnych sesji implementacyjnych. Bieżące
zadanie i wyniki wykonania znajdują się w [backend-progress.md](backend-progress.md).
Plan nie oznacza, że opisane funkcje są już zaimplementowane.

## 1. Cel i priorytety

Istniejący frontend Next.js jest działającym demonstratorem interfejsu. Zachowujemy
jego wygląd i zachowanie tam, gdzie nie stoi to w sprzeczności z rzeczywistym
procesem. Zastępujemy dane demonstracyjne małymi, kompletnymi fragmentami: UI → API
→ reguły → baza → testy. Nie przepisujemy wszystkich ekranów na raz.

Priorytet demonstracji: zalogowany przełożony przeprowadza i wznawia ocenę
okresową C dla fikcyjnego radcy, wybiera zachowania i sam zatwierdza oceny;
backend oblicza wynik, powstaje dokument, a asystent odpowiada na podstawie źródeł.
Kolejne cele to formularz B, pierwsza ocena i rzeczywisty monitoring HR.

Nie dodajemy Redis, RabbitMQ, Celery, mikroserwisów ani osobnej bazy wektorowej.
Nie implementujemy integracji EZD/QNT. Rzeczywiste wdrożenie do urzędu wymaga
osobnej weryfikacji prawnej, bezpieczeństwa, podpisów i procedur organizacyjnych.

## 2. Materiały i stan wyjściowy

### Źródła dostarczone z zadaniem

Ścieżki poniżej są względem katalogu głównego repozytorium. Katalog materiałów
może być lokalnie nieśledzony; nie należy zakładać jego obecności po sklonowaniu
ani dodawać go do commita bez sprawdzenia uprawnień i intencji właściciela.

| Materiał | Zastosowanie |
| --- | --- |
| `docs/hacknation-materials/MC BDG - Pełna treść zadania konkursowego.pdf` | Zakres, rola człowieka, wymagania asystenta i demonstracji |
| `docs/hacknation-materials/Model_kompetencji.xlsx` | 14 kompetencji, 49 wskaźników, pięć poziomów; źródło katalogu, nie fikstury UI |
| `docs/hacknation-materials/Ocena okresowa w służbie cywilnej/Rozporządzenie o ocenach okresowych z 2016 r. (3).pdf` | Okresowa: § 3–6, § 10–12, załączniki z kryteriami i arkuszami |
| `docs/hacknation-materials/Pierwsza ocena w służbie cywilnej/Rozporządzenie o pierwszej ocenie z 2015 r. (1).pdf` | Pierwsza ocena: § 2–10, formularz i sprawozdanie |
| `docs/hacknation-materials/Ocena okresowa w służbie cywilnej/Arkusz oceny B (2).docx` i `Arkusz oceny C (2).docx` | Wzory dokumentów okresowych |
| `docs/hacknation-materials/Pierwsza ocena w służbie cywilnej/Arkusz pierwszej oceny (2).docx` | Wzór dokumentu pierwszej oceny |
| `docs/hacknation-materials/Kompetencje wspierające analizę OSP + przykładowe OSP/OSP_word/` | Trzy przykładowe OSP, w tym `OSP DSI WWI 5 radca.docx` dla pierwszego scenariusza C |
| Poradniki KPRM w katalogach ocen | Interpretacja i przygotowanie bazy wiedzy; zachować źródło i wersję |

Powyższe PDF-y są historycznymi materiałami konkursowymi. Przed deklarowaniem
aktualnej zgodności należy sprawdzić ich obowiązywanie i aktualny tekst ustawy o
służbie cywilnej. Ustawy nie zidentyfikowano jako osobnego pliku w materiałach;
kwalifikacja i terminy zależne od niej wymagają uzupełnienia zweryfikowanego źródła.
Nie rozstrzygać tych niepewności domysłem ani odpowiedzią LLM.

### Inwentaryzacja demonstratora

| Miejsce | Stan teraz | Docelowa integracja |
| --- | --- | --- |
| `frontend/src/features/assessments/model/types.ts` | `EmployeeId` to cztery nazwy, `Assessment` miesza dane i kursory UI | UUID oceny i pracownika; osobne dane biznesowe oraz stan ekranu |
| `frontend/src/features/assessments/model/defaults.ts` | Stałe daty, fikcyjne notatki, domyślne wyniki 5, egzamin i sprawozdanie `yes` | Nowy proces ma wartości nieustalone; żadnych fikcyjnych potwierdzeń |
| `frontend/src/features/workspace/{workspace-provider,storage}.ts*` | Jeden lokalny proces na pracownika, zastępowanie procesu, localStorage `kompas-workspace-v1` | Autoryzowany zapis serwerowy i historia; nie importować automatycznie danych demo |
| `frontend/src/features/assessments/model/{scoring,navigation}.ts` | Wynik liczony w UI; `?step=` tylko częściowo chroni przebieg | Wynik i przejścia zatwierdza backend; ekran nie zmienia statusu |
| `frontend/src/features/assessments/data/{employees,competencies}.ts` | Fikstury, uproszczone wskaźniki i dwa/trzy wskaźniki na kompetencję | Pracownicy z API, katalog pełny i wersjonowany |
| `frontend/src/features/assessments/components/summary.tsx` | Przyciski automatycznego wypełniania ocen demo | Usunąć z prawdziwego procesu; oceniający zatwierdza każdą ocenę |
| `frontend/src/features/assessments/components/assessment-document.tsx` | Nieoficjalny podgląd i `window.print()` | Dokument z właściwego wzoru; potwierdzenie czynności nie jest podpisem |
| `frontend/src/components/layout/sidebar.tsx` i `features/search/` | Użytkownik Anna i lista wszystkich osób są fikcyjne | `/me`, uprawniona wyszukiwarka i widoczność HR |
| `frontend/src/features/{dashboard,deadlines,employees,hr}/` | Część liczb, terminów i statusów jest stała | Projekcje API ograniczone uprawnieniami |
| `frontend/src/features/assistant/` | Synchroniczne odpowiedzi, statyczne źródła, domyślny kontekst Jana | Jawny autoryzowany kontekst, odpowiedź API, cytaty i błędy |

Makieta jest wzorcem UI, a nie autorytetem prawnym, modelem autoryzacji ani
kontraktem API. `employee.manager` oznacza charakter stanowiska ocenianego, a nie
rolę zalogowanego użytkownika. Kliknięcie zakładki nie jest zdarzeniem formalnym.

## 3. Decyzje architektoniczne

Zapisane decyzje obowiązują w kolejnych zadaniach. Zmieniając decyzję, aktualizuj
jej treść, datę, powód i wpływ na już ukończoną pracę; nie zakładaj, że plan
uprawnia do niszczenia danych lub pomijania niezgodności ze źródłami.

| ID | Decyzja |
| --- | --- |
| DEC-001 | Modularny monolit FastAPI, Python 3.13, `uv`, Pydantic Settings, Ruff, pytest. Wersje zależności i obrazów utrwalamy w lockfile i konkretnych tagach. |
| DEC-002 | PostgreSQL jest źródłem prawdy dla danych biznesowych; SQLAlchemy 2, psycopg 3, synchroniczna sesja na żądanie, Alembic. Transakcja obejmuje zmianę i wymagane zdarzenie. Testy integracyjne używają PostgreSQL. |
| DEC-003 | Supabase Cloud służy do uwierzytelniania. FastAPI weryfikuje access token i pobiera użytkownika, role oraz przypisania z własnej bazy; token nie nadaje biznesowych uprawnień. |
| DEC-004 | Next.js App Router i istniejący wygląd pozostają. Integracja kolejnych ekranów przez mały klient `fetch` i typy wygenerowane z OpenAPI. Brak automatycznego fallbacku z danych prawdziwych na demo. |
| DEC-005 | UUID identyfikują oceny i zasoby; wiele ocen jednego pracownika, zachowana historia. Przy obsłudze duplikatów nie usuwać poprzednich procesów. |
| DEC-006 | Status domenowy, zdarzenia i potwierdzenia są oddzielone od nawigacji UI. Backend sprawdza uprawnienia i warunki przejść. Zamknięta ocena nie jest edytowalna. |
| DEC-007 | Wersja rewizji chroni zapisy przed nadpisaniem: klient wysyła wersję, serwer atomowo sprawdza i inkrementuje, konflikt zwraca `409`. Nie gubić niezapisanego tekstu w UI. |
| DEC-008 | Wynik formalny liczy wyłącznie backend. Sugestia behawioralna jest obliczeniem pomocniczym, jej wersja jest zachowana, a ostateczną ocenę zatwierdza przełożony. |
| DEC-009 | Kryteria i wskaźniki pochodzą z materiałów, mają stabilne ID i wersję. Ocena wiąże się z wersją katalogu oraz migawką formularza i stanowiska. |
| DEC-010 | RustFS jest prywatnym magazynem S3, metadane i uprawnienia znajdują się w PostgreSQL. Dostęp do obiektu przechodzi przez uprawniony backend. |
| DEC-011 | OpenRouter podczas hackathonu wyłącznie przez wymienialny `LLMProvider`. Kontrolowany RAG w PostgreSQL korzysta ze zweryfikowanych fragmentów oryginalnych PDF/DOCX/XLSX; Markdown jest pomocniczy i wymaga porównania z oryginałem. Cytowania wskazują autentyczne dokumenty i lokalizacje. Wierność ekstrakcji i aktualność prawna są osobnymi statusami. Brak podstaw skutkuje ograniczeniem/odmową odpowiedzi; AI nie podejmuje decyzji formalnych. Prywatne dokumenty podlegają autoryzacji i nie trafiają do wspólnego indeksu. |
| DEC-012 | Lokalnie jedna organizacja i komórki organizacyjne. Role `MANAGER`, `HR`, `ADMIN` nie zastępują przypisania dostępu. A jest jawnie nieobsługiwany w pierwszym zakresie. |
| DEC-013 | Logowanie e-mail/hasło przez Supabase, konta tworzone przez administratora; bez publicznej rejestracji. Bootstrap pierwszego administratora jest jawną operacją operatora, nie endpointem publicznym. |
| DEC-014 | Potwierdzenie przez aplikację opisuje zarejestrowaną czynność i autora; nie jest podpisem elektronicznym ani dowodem podpisania przez inną osobę. |
| DEC-015 | Jedno uruchomienie Compose dla developmentu; konfiguracja VPS jako osobny wariant. Bez prawdziwych sekretów w repozytorium, obrazach, logach i progresie. |

Struktura jest wskazówką, nie obowiązkiem tworzenia pustych plików:

```text
frontend/                    istniejący Next.js
backend/
  app/
    main.py
    core/                    config, database, security
    modules/                 users, employees, assessments, documents, ai
    integrations/            storage, llm — dopiero gdy potrzebne
  alembic/                   migracje
  tests/                     pytest
  pyproject.toml
  uv.lock
  Dockerfile
infra/
  compose.yaml
  compose.dev.yaml
  Caddyfile                  dopiero w etapie wdrożenia
.env.example
```

W obrębie istniejących modułów używaj tylko potrzebnych `models.py`, `schemas.py`,
`service.py`, `router.py` i czystych funkcji domenowych. Brak uniwersalnych
repozytoriów, kolejek i warstw tworzonych na przyszłość.

Uszczegółowienie DEC-009 (2026-11-21, P3-01): pełna wersja katalogu jest
niezmiennym snapshotem JSONB w `catalog_versions`, z SHA-256 pliku źródłowego.
Kryteria i wskaźniki mają UUIDv5 od znormalizowanej nazwy/opisu, niezależne od
pozycji w arkuszu. Zachowujemy wszystkie oryginalne opisy i polskie znaki.
Odczyt całego katalogu nie wymaga osobnych tabel wskaźników; relacyjne powiązania
odpowiedzi w P4 muszą walidować ID wobec przypiętego snapshotu wersji.

Uszczegółowienie DEC-003/004 (2026-11-21, P2-02): logowanie e-mail/hasło używa
Server Actions i serwerowego klienta `@supabase/ssr`, bez klienta Auth w przeglądarce.
Sesja jest w ciasteczkach HttpOnly/SameSite=Lax (Secure w produkcji), proxy
odświeża token i przenosi ciasteczka oraz nagłówki bez cache. Next.js sprawdza
claims i przesyła access token serwer-serwer do FastAPI; API niezależnie sprawdza
podpis i konto. Żaden token nie jest przekazywany do komponentu klienckiego.

Uszczegółowienie DEC-006/007 (2026-11-21, P4-02): kryteria i terminy są zapisywane
oddzielnie w `draft`. Jawne polecenie `agree_criteria` sprawdza komplet i zmienia
status na `criteria_agreed`; odtąd ustalenia są tylko do odczytu. Korekta po tym
potwierdzeniu wymaga osobnej decyzji i nie jest obecnie obsługiwana. Każdy zapis
blokuje ocenę i aktualne przypisanie, sprawdza rewizję, inkrementuje ją i zapisuje
zdarzenie z autorem oraz czasem UTC w tej samej transakcji. Potwierdzenie zapisuje
także datę rozmowy jako datę czynności. Kontrolujemy kolejność dat i nie pozwalamy
potwierdzać przyszłej rozmowy jako wykonanej (dzień w Europe/Warsaw); nie obliczamy
terminów ustawowych ani wyjątków bez zweryfikowanych źródeł.

Uszczegółowienie DEC-006/007 (2026-11-21, P4-03): jawne `start_period` zmienia
`criteria_agreed` na `in_progress`. W tym stanie można dodawać datowane obserwacje
do wybranych kryteriów oraz zapisywać szkic rozmowy (agenda, mocne strony,
obszary rozwoju i opcjonalna data odbytej rozmowy). Obserwacje są dopisywane,
nie zastępują wcześniejszych wpisów. Data czynności nie może poprzedzać rozmowy
rozpoczynającej ani być w przyszłości. Nie wymuszamy zakończenia zaplanowanego
okresu bez zweryfikowanych zasad terminów. `confirm_conversation` wymaga zapisanej
daty odbytej rozmowy i zmienia stan na `evaluation`; obserwacje i rozmowa są odtąd
tylko do odczytu. Obserwacje i teksty przygotowawcze są opcjonalne. Autor i czas
zapisu pochodzą z serwera; potwierdzenie nie jest podpisem ani doręczeniem.

Uszczegółowienie DEC-008/009 (2026-11-21, P4-04): w `evaluation` zapisujemy
pełny zestaw odpowiedzi danego kryterium (UUID wskaźnika, poziom 0–4 albo brak
obserwacji, opcjonalna notatka do 4000 znaków). Backend waliduje dokładny zestaw
wobec przypiętego katalogu i utrwala sugestię z wersją polityki, autorem i czasem.
Osobne polecenie zatwierdza jawnie wybraną ocenę 1/3/5/7/9; może ona różnić się
od sugestii, również przy braku obserwacji. Zmiana poziomu lub notatki unieważnia
decyzję tylko tego kryterium. Identyczny zapis nie unieważnia decyzji. Zapis
decyzji nie finalizuje całej oceny. Wszystkie mutacje używają wspólnej blokady,
rewizji i atomowego zdarzenia; nie zapisujemy treści notatek w zdarzeniach.

Uszczegółowienie DEC-006/007/008 (2026-11-21, P4-05): wynik bieżący pochodzi
wyłącznie z zatwierdzonych ocen wszystkich wybranych kryteriów. Odpowiedź zawiera
`outcome` i średnią wyświetlaną do dwóch miejsc; decyzja używa dokładnego ułamka.
Osobny zapis podsumowania przyjmuje uzasadnienie i opcjonalne wnioski rozwojowe
(po 10 000 znaków). Można zapisać niepełny szkic. Jawne `complete` wymaga zapisania
podsumowania, a przy wyniku negatywnym niepustego uzasadnienia. Nie dodajemy wymogu
niepustych wniosków bez ustalonej podstawy. Pod wspólną blokadą sprawdzamy ponownie
ustalenia, rozmowę i komplet decyzji; utrwalamy wynik, sumę/liczbę ocen i osobny
autor/czas zakończenia. Odczyt zamkniętej oceny korzysta z tej migawki wyniku.
Retry `complete` w `completed` akceptuje tylko rewizję źródłową lub wynikową,
bez ponownej mutacji/zdarzenia, nadal z kontrolą aktualnego dostępu. Inne rewizje
zwracają 409. Zamkniętej oceny nie można edytować ani otworzyć do korekty.

Uszczegółowienie DEC-007/010 (2026-11-21, P5-01): prywatne załączniki należą do
konkretnej oceny, z identyczną autoryzacją autorstwa/przypisania. Upload przesyła
surowe bajty (bez multipart), bezpośrednio przez API ze strumieniowym limitem
10 MiB; MIME i rozszerzenie nie zastępują parsera PDF/OOXML. Używamy boto3 oraz
pypdf do rzeczywistej walidacji PDF, bez ekstrakcji tekstu. Metadane i zdarzenie
podnoszą rewizję pod wspólną blokadą; `completed` blokuje nowe pliki. Istniejące
pliki pozostają dostępne po zamknięciu, po aktualnej kontroli dostępu. Odpowiedź
uploadu zawiera nową rewizję; niepewny rezultat klient rozstrzyga przez list/detail,
nie powtarza automatycznie z nową rewizją. Nie ma publicznych/presigned URL-i ani
usuwania/nadpisywania plików. Kompensacja usuwa wyłącznie świeży, niezatwierdzony
obiekt; przy utracie odpowiedzi COMMIT sprawdzamy metadane i zachowujemy plik,
gdy wynik transakcji jest nieustalony. Log z samym kluczem umożliwia ręczną naprawę.
Powiązanie OSP z pracownikiem i ekran dokumentu pozostają w P5-02.

Uszczegółowienie DEC-009/010 (2026-11-21, P5-02): OSP jest niezmiennym źródłem
pracownika w `job_descriptions`, a nie załącznikiem należącym do jednej oceny.
Wersje są numerowane pod blokadą pracownika. Ocena wybiera jawnie wersję w `draft`;
potwierdzenie ustaleń zamyka wybór. Import operatora nie tworzy sztucznej oceny.
Odczyt źródła przez ocenę wymaga jej autorstwa/przypisania i tego samego pracownika.

PDF jest pochodnym artefaktem zakończonej oceny, nie kolejną edycją jej danych.
`assessment_transaction` współdzieli blokadę/autoryzację i commit/rollback z
`edit_assessment`; tylko operacje biznesowe inkrementują rewizję i zapisują event.
Unikalność rewizji i wersji szablonu zapewnia jeden PDF, również przy równoległych
żądaniach. Powtórzenie identycznych danych zwraca metadane istniejącego pliku;
inne dane dla tego artefaktu dają 409. Zachowujemy SHA-256 źródła wzoru, jawne
uzupełnienia i identyfikator OSP w prywatnych metadanych generowania.

Szablon ReportLab `arkusz-c-2016-4845015f-v1` odwzorowuje części I–II dostarczonego
DOCX (SHA-256 `4845015f886a56c8715006a5b803e77c6d628eab9aa4989763214c170ba662f0`).
Imię i nazwisko przedstawiamy razem, bez zgadywania podziału nazwiska. Nazwa urzędu,
komórka/stanowisko oceniającego, data „do”, status pracownika/urzędnika i poprzednia
ocena są jawnymi danymi oceniającego; planowany termin nie staje się datą „do”.
Początek okresu pochodzi z daty rozmowy i przekazania kryteriów w części I.
Zgodnie z przypisem 18 źródła część III pomijamy po jawnej deklaracji nieskładania
wniosku o kolejny stopień; generowanie takiego wniosku pozostaje poza tym zakresem.
Pola podpisów i zapoznania pozostają puste. Font Unicode jest osadzony w PDF;
brak fontu daje 503, nieobsługiwany znak 422, bez cichej utraty tekstu.

## 4. Bezpieczeństwo i autoryzacja

### Sesja i JWT

Next.js używa `@supabase/ssr`; po stronie serwera tożsamość weryfikuje przez
`getClaims()` lub `getUser()`, nie przez bezwarunkowe zaufanie do `getSession()`.
Access token można z sesji przekazać do FastAPI, które weryfikuje go niezależnie.
Projekt Supabase ma używać asymetrycznych kluczy, a FastAPI JWKS z kontrolą
`iss`, `aud`, `exp`, `sub`, dozwolonego algorytmu i rotacji kluczy. Nie akceptować
algorytmu zdefiniowanego wyłącznie przez token. Nieznany/nieaktywny użytkownik
nie dostaje dostępu. Niedostępność weryfikacji nie otwiera dostępu.

Zapisujemy identyfikator `sub` i własne dane użytkownika, nigdy hasła czy tokeny.
Token nie pojawia się w URL, localStorage aplikacji, logach ani błędach. Sesja,
cookies, CSRF i ewentualny serwerowy proxy muszą być dopasowane do rzeczywistego
przepływu żądań i przetestowane. `SUPABASE_SERVICE_ROLE_KEY` nie trafia do Next.js
publicznego ani przeglądarki.

### Polityka dostępu

| Operacja | MANAGER | HR | ADMIN |
| --- | --- | --- | --- |
| Własny profil | Tak | Tak | Tak |
| Lista pracowników | Tylko przypisani | W zakresie organizacji | Dane niezbędne do administracji |
| Treść i edycja oceny | Tylko przypisany oceniający | Monitoring i minimalne pola, bez notatek i ocen cząstkowych | Brak automatycznego dostępu do treści oceny |
| Zatwierdzenie oceny | Tylko przypisany oceniający | Nie | Nie, chyba że ma także odpowiednie przypisanie MANAGER |
| Role i przypisania | Nie | Nie | Tak |

Użytkownik może mieć wiele ról. HR ma oddzielny schemat odpowiedzi dla monitoringu;
nie polegamy na ukrytym przycisku. `ADMIN` może zarządzać przypisaniem bez prawa do
odczytu treści. Każdy endpoint szczegółu sprawdza obiekt i przypisanie, także
obserwacje, dokumenty, wyszukiwanie i kontekst AI. Listy filtruje się w zapytaniu,
przed paginacją i agregacją. Testować brak tokenu, wygasły/podrobiony token,
nieznanego użytkownika, cudzy identyfikator i każdą kombinację rol/zasobów.

## 5. Model domenowy i dane

Nazwy tabel poniżej definiują odpowiedzialności, nie nakaz tworzenia ich przed
pierwszym użyciem. Migracje powstają razem z wymagającym ich vertical slice.

- `users`, `user_roles`, `manager_employee_assignments`: identyfikacja, aktywność,
  wielość ról i przypisania. Przypisanie prowadzącego ocenę zapisuje się w ocenie.
- `employees`, `organizational_units`: osoba, stanowisko, jednostka i typ
  stanowiska; rozróżnienie kierownika urzędu, bezpośredniego kierowania i innych.
- `job_descriptions`, `documents`: powiązanie OSP z metadanymi i prywatnym
  obiektem; wersja OSP użyta w procesie jest jawna.
- `catalog_versions`, `criteria`, `behavior_indicators`, opisy poziomów:
  stabilne identyfikatory, pełne dane XLSX i pochodzenie. Nie używać pozycji w
  tablicy jako identyfikatora biznesowego.
- `assessments`: UUID, pracownik, oceniający, typ, formularz, status, wersja,
  migawka danych potrzebnych do dokumentu, daty utworzenia/zmiany i autorzy.
- `assessment_criteria`, `indicator_observations`, `criterion_ratings`:
  kryteria wymagane/dodatkowe, uzasadnienie wyboru, odpowiedzi i notatki,
  sugestia oraz osobno formalna decyzja i jej autor. Po zmianie danych
  wskaźników oznaczyć zatwierdzenie danego kryterium jako wymagające ponowienia.
- `assessment_events`: istotne czynności, ich typ, czas, autor i identyfikator
  procesu; nie przechowywać niepotrzebnych danych osobowych w logach zdarzeń.
- Pierwsza ocena: pięć osobno identyfikowanych elementów, terminy, sprawozdanie,
  egzamin/zwolnienie i formalny wynik. Współdzielić infrastrukturę, nie wymuszać
  okresowych zasad na tej ścieżce.

Wymuszaj FK, unikalność, poprawne wartości i indeksy dla zapytań uprawnień. Nie
nadawaj wynikom domyślnej wartości pozytywnej. Daty biznesowe przechowuj jako
`date`, zdarzenia jako timezone-aware UTC. Czas wyświetlany użytkownikowi podlega
konwersji; nie używaj zegara przeglądarki jako autorytetu zdarzenia.

Migracje: osobno zmiana schematu i duży backfill; nie edytować migracji użytej w
środowisku współdzielonym. Testować `upgrade`, a downgrade lokalnie tylko gdy jest
bezpieczny; dla produkcji planować migrację naprawczą do przodu. Nie usuwać danych
ani wolumenów podczas zwykłych testów lub uruchamiania.

## 6. Reguły i cykl oceny

### Okresowa B/C

W dostarczonym rozporządzeniu z 2016 r. § 3–4 opisują formularze i wymagane
kryteria, § 5 dopuszcza do trzech dodatkowych, a § 10–11 opisują rozmowę i wynik.
Potwierdzić aktualność źródeł przed użyciem formalnym.

| Formularz | Obowiązkowe kryteria |
| --- | --- |
| C | Wykorzystywanie wiedzy i doskonalenie zawodowe; rzetelność; organizacja pracy i orientacja na osiąganie celów; współpraca; komunikacja |
| B | Zarządzanie ludźmi; podejmowanie decyzji i odpowiedzialność; organizacja pracy i orientacja na osiąganie celów; współpraca; komunikacja |

Arkusz A ma odrębny zakres i sześć obowiązkowych kryteriów; nie wolno traktować go
jako B. W pierwszym milestone API zwraca czytelny błąd nieobsługiwanego A.
Wybór dodatkowych kryteriów jest unikalny, nie może powielać obowiązkowych i ma
uzasadnienie powiązane z obowiązkami z OSP. Decyzję podejmuje oceniający.

Formalne oceny cząstkowe: `1, 3, 5, 7, 9`. Średnia jest arytmetyczna ze
wszystkich aktywnych, zatwierdzonych ocen; porównuj dokładnie, bez wcześniejszego
zaokrąglania. Przed kompletem wynik jest `incomplete`, bez pozytywnej/negatywnej
decyzji. Przy komplecie wynik jest pozytywny, jeżeli średnia > 4 i żadna ocena nie
wynosi 1; inaczej negatywny. Negatywny wymaga uzasadnienia przed finalizacją.
Przechowuj również wnioski rozwojowe oraz informacje niezbędne do arkusza.

Sugestia może początkowo odwzorować demo: poziomy wskaźników 0–4 odpowiadają
1/3/5/7/9, brak obserwacji nie wchodzi do średniej, remis rozstrzyga niższy
poziom, brak odpowiedzi daje brak sugestii. To polityka produktu, nie przepis.
Zapisz jej wersję i przetestuj; człowiek może wybrać inną ocenę. Nie przedstawiaj
zaproponowanego poziomu jako formalnej decyzji.

### Pierwsza ocena

Źródło: dostarczone rozporządzenie z 2015 r., § 2–10; potwierdzić aktualność.
Pięć stałych elementów, oceny `3, 5, 7`, średnia co najmniej 5 i najwyżej jedna
ocena 3. Dodatkowo wymagane sprawozdanie w terminie i zaliczony egzamin, o ile
obowiązuje. `not_applicable` wymaga jawnej podstawy zgodnej ze źródłem. Brak
informacji jest niekompletnością, a nie automatycznym wynikiem. Uzasadnienie
negatywnej oceny jest wymagane. Daty, wyjątki, kwalifikacja i zmiany terminów
wymagają zweryfikowanej ustawy i zapisania podstawy — nie kopiować skrótów demo.

### Statusy i edycja

Minimalne stany okresowe: `draft` → `criteria_agreed` → `in_progress` →
`evaluation` → `completed`. Przejścia są poleceniami API, a nie PATCH-em
dowolnego statusu. Każde przejście wymaga przypisanego oceniającego, bieżącej
rewizji i danych odpowiednich do czynności; każda transakcja zapisuje autora i
czas. `completed` wymaga zatwierdzonych ocen, wyniku, uzasadnienia negatywnego
oraz wymaganych danych i odnotowanych czynności. Zamknięcie w aplikacji nie
oznacza, że dokument jest prawnie podpisany lub doręczony.

`GET` ani nawigacja po krokach nie zmieniają statusu. Dopuszczalność korekty po
formalnym zamknięciu wymaga osobnej decyzji; początkowo API odrzuca edycję.
Pierwsza ocena ma własny zestaw przejść, ustalany wraz z jej implementacją na
podstawie źródeł; nie udawać, że powyższe stany obejmują wszystkie wyjątki prawne.

## 7. Kontrakt API i frontend

API ma prefiks `/api/v1`, OpenAPI generowane przez FastAPI i jawne schematy
Pydantic. `/health` to liveness procesu, `/api/v1/health` sprawdza rzeczywiste
połączenie PostgreSQL i zwraca niepowodzenie gotowości przy awarii; nie ujawnia
sekretów. Nie twierdzić, że health bazy sprawdza RustFS lub Supabase.

Zasoby wdrażaj w miarę potrzeb, nie wszystkie od razu:

```text
GET    /api/v1/me
GET    /api/v1/employees
GET    /api/v1/employees/{employee_id}
GET    /api/v1/catalog/criteria
GET    /api/v1/assessments
POST   /api/v1/assessments
GET    /api/v1/assessments/{assessment_id}
PATCH  /api/v1/assessments/{assessment_id}
PUT    /api/v1/assessments/{assessment_id}/criteria
POST   /api/v1/assessments/{assessment_id}/observations
PUT    /api/v1/assessments/{assessment_id}/ratings
GET    /api/v1/assessments/{assessment_id}/result
POST   /api/v1/assessments/{assessment_id}/transitions
```

Konkretny schemat każdego endpointu powstaje w odpowiednim zadaniu i obejmuje
rewizję, autoryzację i walidację; OpenAPI jest źródłem dla typów TS. `PATCH`
przyjmuje wyłącznie jawnie dozwolone pola, nigdy role, autora, wynik lub dowolny
status. `401` oznacza brak/nieważną tożsamość, `403` brak uprawnienia, `404`
nieistniejący zasób, `409` konflikt rewizji/stanu, `422` błędne dane, `503`
niedostępną zależność. Nie ujawniać istnienia zasobów osobom nieuprawnionym;
endpointy zasobowe mogą konsekwentnie zwracać `404` zamiast `403`.

### Zasady podłączenia ekranu

1. Zastąp tylko dane potrzebne danemu ekranowi. Zmieniaj `EmployeeId` na UUID i
   trasę na `/assessments/{assessmentId}` wraz ze wszystkimi odnośnikami.
2. Zapisuj celowymi operacjami, nie całym dawnym obiektem `Assessment`. Odśwież
   widok z odpowiedzi serwera i zachowaj niezapisany tekst po błędzie/konflikcie.
3. W trakcie zapisu blokuj podwójne przejście, pokazuj zapis/błąd. Żądanie
   utworzenia musi obsłużyć ponowienie bez przypadkowych duplikatów, np. kluczem
   idempotencji zdefiniowanym w kontrakcie.
4. Przestawionego ekranu nie podłączaj do localStorage demo. Motyw pozostaje
   lokalny; teksty i oceny nie są trwale przechowywane w localStorage.
5. Dashboard, wyszukiwarka, terminy i HR przechodzą na te same autoryzowane dane;
   żadnych statycznych liczników przedstawianych jako rzeczywiste.
6. Sesje/odpowiedzi zawierające dane użytkowników są prywatne i nie trafiają do
   współdzielonego cache Next.js. Brak dostępu, puste listy i awarie są odróżniane.

## 8. Pliki, dokumenty i AI

### RustFS i dokumenty

Jeden prywatny bucket, klucze obiektów generowane przez serwer; nazwa pliku nie
stanowi ścieżki ani uprawnienia. Upload przez FastAPI po autoryzacji, z limitem
rozmiaru i sprawdzeniem typu oraz zawartości dla PDF/DOCX. Nie ufać samemu MIME
klienta. Metadane: UUID, typ, właściciel/powiązanie, oryginalna bezpieczna nazwa,
rozmiar, checksum, klucz obiektu, autor i czas. Nie wystawiać bucketu publicznie.

Zapis obiektu i bazy nie jest jedną transakcją: po nieudanym zapisie metadanych
usuń świeżo zapisany obiekt, a niepowodzenie czyszczenia odnotuj do naprawy.
Testuj oba kierunki błędu. Nie usuwaj obiektu przed trwałym potwierdzeniem
operacji biznesowej. Pobieranie sprawdza prawo do konkretnej oceny/OSP.

PDF tworzony po stronie backendu z rzeczywistego wzoru i danych zatwierdzonych w
procesie. Zachowaj identyfikator wersji szablonu oraz powiązanie z wersją oceny.
Nie nazywaj wygenerowanego pliku podpisanym ani doręczonym. Osobno zapisuj
ewentualny późniejszy dokument podpisany.

### AI i baza wiedzy

`LLMProvider` określa generowanie tekstu oraz ustrukturyzowane odpowiedzi, kiedy
model je obsługuje; `OpenRouterProvider` jest jedyną implementacją w pierwszym
zakresie. Streaming i dodatkowych providerów nie tworzymy na zapas. Adapter
obsługuje timeout, limity i błędy; API nie zwraca surowych sekretów lub promptów.
Na polecenie użytkownika z 2026-11-21 wybieramy płatny model do prezentacji:
priorytet skuteczność, następnie czas, następnie koszt. Domyślnie Sonnet 5.5,
8192 tokenów wyjścia i reasoning medium; bez automatycznej zmiany modelu.
To zmienia wcześniejszy wymóg darmowego modelu; zgodności z ograniczeniem
konkursowym dotyczącym darmowych narzędzi nie deklarujemy bez jego wyjaśnienia.

Original First, Evidence First: manifest wiąże oryginały z pomocniczym Markdown.
Zmiana zakresu na polecenie użytkownika: treść zadania konkursowego, regulamin
i diagram produktu są poza korpusem aplikacji i nie są importowane do RAG.
CLI importuje niezmienne źródła do prywatnego RustFS i lokalizowane fragmenty do
PostgreSQL. Tylko zatwierdzone fragmenty stanowią podstawę odpowiedzi formalnych;
aktualność prawna jest weryfikowana niezależnie od wierności ekstrakcji.
Początkowo PostgreSQL full-text search, bez osobnej bazy wektorowej ani kolejek.
Backend waliduje pochodzenie cytowań, dostęp, zakres oceny i wsparcie twierdzeń;
same poprawne ID cytowań nie potwierdzają prawdziwości odpowiedzi. Brak podstaw
lub sprzeczność źródeł mają jawne statusy, inne niż awaria infrastruktury.
Źródła otwieramy przez autoryzowane API. Analiza OSP używa istniejących wersji
pracownika i katalogu; maksymalnie trzy dodatkowe kryteria z dowodami, bez
automatycznej zmiany oceny. Wynik formalny nadal oblicza silnik reguł.
Nie zapisujemy historii czatu bez zasad retencji ani poufnych promptów w logach.

## 9. Środowisko i jakość

- `docker compose --env-file .env -f infra/compose.yaml -f infra/compose.dev.yaml
  up --build` jest docelowym jednym poleceniem lokalnym po skopiowaniu
  `.env.example` do ignorowanego `.env`. Ścieżki, build contexts i env-file
  sprawdzić rzeczywistym `docker compose config`.
- Serwisy: frontend, backend, PostgreSQL i RustFS. Dane obu usług w oddzielnych
  trwałych wolumenach. Baza ma healthcheck; aplikacja czeka na gotowość. Migracje
  uruchamiane w jawnej, jednokrotnej operacji przed startem API, bez wyścigów
  wielu replik. Decyzję o konkretnym mechanizmie zapisać przy etapie 1.
- W kontenerze backend łączy się z `db`, a Next.js po stronie serwera z nazwą
  serwisu API; adres używany przez przeglądarkę musi być osiągalny z hosta.
  CORS ma jawne lokalne originy i metody; w produkcji użyć właściwej domeny.
- PostgreSQL i konsola RustFS nie są publicznie wystawione w produkcji. RustFS
  single-node korzysta z trwałego wolumenu; wersja obrazu i uprawnienia UID są
  sprawdzone dla wybranego obrazu. Nie zakładać rozszerzenia pojedynczego dysku bez
  migracji danych. Brak produkcyjnych domyślnych haseł.
- `.env.example` zawiera tylko nazwy i niesekretne placeholdery; pliki `.env`,
  locki sesji, dane osobowe, wolumeny i zrzuty bazy są ignorowane. Publiczne i
  serwerowe ustawienia Next.js są rozdzielone.
- `ruff check`, `ruff format --check`, `pytest`; frontend `npm run precommit`.
  Dokładne komendy zapisujemy po utworzeniu projektu. Przed frontendowym commitem
  uruchom `npm run precommit`; React Doctor okresowo, z oceną false positives.
- Testy: jednostkowe domeny, integracyjne PostgreSQL/migracji i API, uprawnienia
  na każdym obiekcie, przypadki błędów i konfliktów oraz E2E krytycznego procesu.
  Żadnych testów na prawdziwych danych pracowników ani z produkcyjnymi sekretami.
- Wcześniejszy zakaz uruchamiania przeglądarki pozostaje w mocy, dopóki użytkownik
  go nie zmieni. Etap E2E jest zaplanowany, lecz oznaczony jako zablokowany tym
  ograniczeniem; nie udawać jego wykonania.

## 10. Fazy i zadania wykonawcze

Każde zadanie aktualizuje `backend-progress.md`. Kryterium ukończenia obejmuje
testy, kontrakt, migracje i integrację UI tam, gdzie są wskazane. Nazwy commitów
są proponowane; rzeczywista treść ma odpowiadać zmianie. Nie oznaczać etapu jako
gotowego, jeśli działa wyłącznie jego część serwerowa.

### Etap 1 — fundament techniczny

**P1-01 — projekt backendu.** Utwórz `backend/`, uv/lockfile, FastAPI, Pydantic
Settings, Ruff, pytest, liveness `/health`, test endpointu i bezpieczną
konfigurację CORS. Nie twórz modułów domenowych na zapas. Gotowe: instalacja z
lockfile, lint, format i testy przechodzą. Commit: `chore(backend): initialize api`.

**P1-02 — PostgreSQL i migracje.** SQLAlchemy/psycopg, sesja per request,
Alembic, konfiguracja URL, `GET /api/v1/health` z realnym `SELECT 1`. Test
połączenia, awarii i uruchomienia migracji na oddzielnej testowej bazie.
Gotowe: poprawna odpowiedź przy dostępnej bazie i niepowodzenie przy awarii.
Commit: `feat(backend): add database readiness`.

**P1-03 — wspólne środowisko.** Dockerfile frontendu i backendu, Compose, wersje
obrazów PostgreSQL/RustFS, trwałe wolumeny, lokalne ustawienia, `.env.example`,
`.dockerignore` i instrukcja. Żaden sekret nie trafia do repo. Gotowe: jedno
polecenie uruchamia cztery usługi; frontend wyświetla istniejący UI, backend
odpowiada, baza i RustFS przeżywają restart; migracje i test połączenia działają.
Zweryfikuj healthcheck RustFS dla wybranej wersji, nie zgaduj endpointu.
Commit: `chore(infra): add local compose environment`.

### Etap 2 — uwierzytelnianie i role

**P2-01 — użytkownicy i JWT.** Migracje użytkowników/rol, jawny bootstrap admina,
weryfikacja Supabase JWKS, `GET /me`. Testuj podpis, algorytm, expiry, issuer,
audience, rotację i nieaktywne konto. Brak skonfigurowanego Supabase blokuje
integrację z realną usługą, nie uzasadnia publicznego trybu bypass. Commit:
`feat(auth): verify identities and load roles`.

**P2-02 — logowanie i sesja.** `@supabase/ssr`, ekran logowania, wylogowanie,
odświeżenie sesji, przekazanie tokenu i prawdziwa tożsamość w sidebarze. Testuj
ochronę stron i błędy sesji; zachowaj istniejący shell. Commit:
`feat(auth): add sign in and session handling`.

**P2-03 — pracownicy i autoryzacja.** Migracja pracowników i przypisań, seed
wyłącznie jawnych fikcyjnych danych, list/detail, filtrowanie po uprawnieniach;
podłącz listę, trasę, wyszukiwarkę i widoczność HR. Testy manager A/B, HR, admin,
nieuprawnione ID, brak danych i wygasła sesja. Commit:
`feat(employees): add authorized employee access`.

### Etap 3 — źródła i reguły domeny

**P3-01 — katalog.** Przetwórz i zweryfikuj XLSX: 14 kompetencji, 49 wskaźników,
pięć poziomów; zapisz pochodzenie, stabilne identyfikatory i wersję. Porównaj
zawartość, nie tylko liczbę, oraz zapewnij powtarzalny import i bezpieczne znaki.
Udostępnij uprawnione API katalogu. Commit: `feat(catalog): add competency model`.

**P3-02 — czyste reguły.** Funkcje Pythona niezależne od FastAPI, bazy i AI:
B/C, maks. 3 dodatkowe, wynik okresowy, sugestie oraz warunki pierwszej oceny.
Niekompletne dane pozostają niekompletne. Testy tabelaryczne progów, oceny 1,
duplikatów, braku dowodów, remisu, zwolnienia z egzaminu i nieprawidłowych danych.
Sprecyzuj daty i wyjątki dopiero po weryfikacji źródeł. Commit:
`feat(assessments): implement scoring rules`.

### Etap 4 — pierwszy kompletny vertical slice C

**P4-01 — utworzenie i wznowienie.** Migracje oceny, przypisanie oceniającego,
migawka pracownika/formularza i katalogu, UUID, rewizja, create/list/detail.
Podłącz istniejący wybór i listę do API, zmień trasy i wszystkie linki. Test
historii, odświeżenia, izolacji użytkowników, A unsupported i idempotencji.
Commit: `feat(assessments): create and resume assessments`.

**P4-02 — kryteria i terminy.** Dobór pięciu kryteriów C i do trzech unikalnych
dodatkowych, uzasadnienie, daty i czynności, kontrola stanu i rewizji. Podłącz
ekrany analizy, kryteriów i terminów. Test limitów, przypisania, błędnych dat,
konfliktu i ponownego odczytu. Commit:
`feat(assessments): persist criteria and dates`.

**P4-03 — obserwacje i rozmowa.** Autoryzowany zapis i odczyt notatek,
obserwacji oraz rozmowy, osobna data czynności i autor; podłącz odpowiednie
ekrany. Test cudzej oceny, błędnych danych, nieudanego zapisu i wznowienia.
Commit: `feat(assessments): persist observations and conversation`.

**P4-04 — wskaźniki i decyzja.** Pełne wskaźniki z katalogu, zapisy odpowiedzi,
sugestia wersjonowana, ręczne zatwierdzenie oceny. Edycja odpowiedzi wymaga
ponownego zatwierdzenia; testuj brak obserwacji, zmianę i dostęp. Podłącz
`behavioral-rating.tsx` i `recommendation.tsx`. Commit:
`feat(assessments): persist behavioral ratings`.

**P4-05 — wynik i zakończenie.** Wynik wyłącznie z API, uzasadnienie negatywne,
wnioski rozwoju, jawna finalizacja, brak edycji po zamknięciu, widoczne braki i
konflikty. Usuń autofill demo z prawdziwej ścieżki. Test granic, wszystkich
przesłanek, ponownego odczytu i idempotentnego przejścia. Commit:
`feat(assessments): finalize periodic assessments`.

### Etap 5 — pliki i dokumentacja

**P5-01 — storage.** Prywatny RustFS, `ObjectStorage`/boto3, bucket,
autoryzowany upload/download, metadane i kompensacja błędów. Testy limitu,
typów, nieuprawnionego odczytu, awarii obu usług i trwałości. Commit:
`feat(documents): store private assessment files`.

**P5-02 — OSP i PDF C.** Powiąż przykładowy OSP z pracownikiem; generuj PDF na
podstawie wzoru C i zweryfikowanych danych, w tym polskich znaków, właściwych
części i wymaganych pól. Podłącz pobranie, przetestuj dane/wariant negatywny i
uprawnienia. Wizualne porównanie PDF oznacz jako niewykonane, jeśli nie można go
przeprowadzić. Commit: `feat(documents): generate periodic assessment pdf`.

### Etap 6 — profesjonalny asystent AI, zweryfikowana baza wiedzy, RAG i analiza OSP

Specyfikacją wykonawczą jest dostarczony przez użytkownika
[phase6-plan.md](hacknation-materials/phase6-plan.md), sekcje 6.0–6.9 i P6-01–P6-07.
Poniższy rejestr zastępuje wcześniejszy skrót trzech zadań. Plik specyfikacji oraz
oryginały pozostają materiałami użytkownika; nie dodawać całego katalogu do Git.
Kolejność jest obowiązkowa, jedno zadanie naraz, z testami i małymi Conventional
Commitami po udanych, spójnych częściach. Nie zaczynać od chatu bez źródeł.

**P6-01 — wymienialny provider LLM.** `LLMProvider`, pojedynczy adapter OpenRouter,
Pydantic Settings, tekst i odpowiedzi strukturalne walidowane lokalnie, timeout,
limity tokenów i kontrolowane błędy. Sprawdzić faktyczne możliwości konkretnego
modelu; bez automatycznego fallbacku do innego modelu, bez streamingu/tool calling
na zapas. Zmiana decyzji 2026-11-21: użytkownik dopuszcza płatne modele i stawia
skuteczność przed czasem i ceną, co zastępuje wymóg darmowego modelu z phase6-plan.
Domyślnie `anthropic/claude-sonnet-5.5`, reasoning medium, limit wyjścia 8192,
timeout operacji 60 s. Routing według latency z awaryjną zmianą dostawcy tego
samego modelu, z zachowaniem parametrów i polityki danych; bez obniżania jakości.
Testy bez sieci: poprawny przepływ i zastąpienie providera, błędny model/brak
klucza, timeout/sieć/limit, błędna struktura, brak wycieku sekretów.
Gotowe: backend używa kontraktu i pełny przepływ przechodzi z atrapą.
Commit: `feat(ai): add configurable llm provider`.

**P6-02 — inwentaryzacja, ekstrakcja i weryfikacja oryginałów.** Manifest stabilnych
ID i jawnych powiązań PDF/DOCX/XLSX → Markdown, SHA-256, typ i wersja źródła.
Ekstrakcja zachowuje kolejność, strony PDF, strukturalne lokalizacje DOCX,
tabele/scalenia/checkboxy/przypisy; XLSX korzysta z importera P3, bez drugiego
katalogu. Zadanie/regulamin konkursu i diagram są poza korpusem; ZIP nie powiela OSP.
Trzystronicowy wykaz kryteriów jest załącznikiem do pełnego rozporządzenia,
nie niezależną podstawą. Oryginały pozostają niezmienne i dostępne po wdrożeniu.
Raport ekstrakcji, różnic Markdown i miejsc do ręcznej kontroli. Normalizacja
nie usuwa cyfr, negacji, progów ani numeracji. Bez poprawiania przepisów LLM.
Minimalne migracje źródeł/fragmentów, idempotentny CLI import PostgreSQL/RustFS.
Statusy treści `unverified/needs_review/approved/rejected` niezależne od
`verified_current/historical/unknown`. Zatwierdzenie tylko sprawdzonych fragmentów,
ze szczególną kontrolą terminów, wyjątków, progów, formularzy i przypisów.
Gotowe: cytat można prześledzić z bazy do oryginału, testy ponownego importu OK.
Commit: `feat(knowledge): ingest verified source documents`.

**P6-03 — wyszukiwanie PostgreSQL.** `KnowledgeRetriever` i FTS z faktycznie
dostępnym słownikiem, filtr typu oceny/źródła/statusu, paragrafy i nazwy kryteriów.
Ograniczony kontekst, sąsiednie warunki/wyjątki, deduplikacja załączników,
diagnostyka rankingu. Nie zwracać przypadkowych wyników przy braku dopasowania.
Prywatne treści filtrować uprawnieniami przed pobraniem. Wynik zawiera ID źródła
i fragmentu, treść, autentyczną lokalizację, statusy, score i dostęp do oryginału.
pgvector wyłącznie po osobnej decyzji uzasadnionej pomiarami. Gotowe: typowe
pytania obu ścieżek znajdują właściwe fragmenty, brak wiedzy jest jawny.
Commit: `feat(knowledge): implement source retrieval`.

**P6-04 — asystent formalny i walidacja cytowań.** Autoryzacja kontekstu,
retrieval zatwierdzonych źródeł, kontrola wystarczalności, deterministyczny silnik
dla wyniku/reguł, LLM dla opisu. Model zwraca twierdzenia z ID dostarczonych
fragmentów, nie wymyślone URL-e, strony czy paragrafy. Pydantic i backend
sprawdzają istnienie, przekazanie, zatwierdzenie, dostęp, zakres i lokalizację;
osobno kontrola merytoryczna twierdzeń, warunków, wyjątków i konfliktów.
API: `answered/insufficient_evidence/conflicting_sources`; awaria providera
jest osobnym błędem. Dokumenty są danymi, nie instrukcjami. Brak mutacji oceny.
Gotowe: prawdziwe cytowania, odrzucenie fikcyjnych podstaw i kontrolowana odmowa.
Commit: `feat(ai): implement grounded formal assistant`.

**P6-05 — istniejący drawer Next.js.** Prawdziwe API przez sesyjną komunikację,
jawny tryb formal/conversation, kontekst oceny tylko przy rzeczywistej ocenie.
Backend pobiera dane i sprawdza dostęp, bez domyślnego Jana i bez zaufania do
przesłanych ról. Ładowanie, błędy/timeout, brak podstaw i klikalne oryginały przez
autoryzowany backend; bez publicznego bucketu, ścieżek hosta i dowolnych URL-i.
Nie zapisujemy czatu w localStorage ani bazy historii bez zasad retencji/dostępu.
Zachować wygląd, bez statycznego fallbacku. Gotowe: pytanie → odpowiedź → źródło.
Commit: `feat(ai): connect grounded assistant frontend`.

**P6-06 — analiza OSP.** Istniejący `JobDescription`, autoryzacja przed odczytem
i wysyłką do LLM, ekstrakcja z lokalizacjami celu/zadań/odpowiedzialności itd.
Obowiązkowe kryteria ustala silnik. Maksymalnie trzy dodatkowe, bez duplikatów
i wyjścia poza przypięty katalog, z uzasadnieniem i rzeczywistym fragmentem OSP.
Pydantic i deterministyczna walidacja ID; brak ocen zachowań osoby, brak
automatycznej zmiany kryteriów. Testy trzech dostarczonych OSP: cyberbezpieczeństwo,
regulacje AI, naczelnik współpracy międzynarodowej. Gotowe: poprawne rekomendacje
z dowodami i decyzją użytkownika. Commit: `feat(ai): recommend criteria from job descriptions`.

**P6-07 — ewaluacja i demonstracja.** 30–50 referencyjnych pytań obu ścieżek,
odpowiedzi zweryfikowane z oryginałami, oznaczenie brakującej ustawy i źródeł.
Osobne pomiary retrieval i generowania; terminy/wyjątki, progi/kryteria, odmowa,
konflikty, fikcyjne cytowania, prompt injection, izolacja OSP, błędy dostawcy
i brak wycieków w logach. Protokół ręcznego przeglądu trudnych odpowiedzi.
Cele wewnętrzne, nie wyniki: ≥95% poprawności, ≥95% trafienia źródła w top-5,
100% autentycznych zatwierdzonych cytowań, zero wycieków/błędów obliczeń
i kategorycznych odpowiedzi przy rozpoznanym braku podstaw w zestawie testowym.
Demo na prawdziwym API: pytanie → źródło → odmowa → OSP → rekomendacja → decyzja
przełożonego → wynik silnika. Bez hardcoded odpowiedzi. Gotowe dopiero po pomiarach.
Commit: `test(ai): validate grounded assistant quality`.

Cały etap jest gotowy dopiero po spełnieniu kryteriów P6-01–P6-07. Mniejszy,
zweryfikowany korpus jest lepszy niż pozornie kompletna wiedza. Nie deklarujemy
aktualności prawnej dostarczonych historycznych materiałów bez osobnej weryfikacji.
Braku ustawy nie zastępujemy wiedzą modelu. Nie dodajemy frameworka agentowego,
kolejek, mikroserwisów ani niezależnego systemu przechowywania prywatnych OSP.

### Etap 7 — formularz B, pierwsza ocena i HR

**P7-01 — B.** Zastosuj osobny wymagany zestaw B w tym samym okresowym procesie,
testuj kierownika i dodatkowe kryteria, generuj właściwy formularz B. Nie
obsługuj A jako B. Commit: `feat(assessments): support manager form b`.

**P7-02 — pierwsza ocena.** Zweryfikuj aktualne źródła, kwalifikację i wyjątki;
zaimplementuj osobny workflow, pięć elementów, terminy, sprawozdanie, egzamin,
oceny i wynik, podłącz istniejące ekrany i dokument. Test granic oraz przypadków
zwolnienia, terminu i wymaganych uzasadnień. Commit:
`feat(assessments): add first assessment workflow`.

**P7-03 — monitoring.** Autoryzowane projekcje dashboardu, terminów i HR,
bez statycznych liczb; oddzielne uprawnienia i brak notatek w odpowiedziach HR.
Przypomnienia wymagane w zadaniu konkursowym: w pierwszej wersji zaplanuj jawne
wysłanie przez uprawnionego HR i zapisz rezultat; kanał oraz konfigurację wybrać
po dostępności środowiska, bez udawania wysyłki. Commit:
`feat(hr): add assessment monitoring`.

### Etap 8 — integracja i wdrożenie

**P8-01 — test całości.** E2E: logowanie → C → zapis → reload → oceny → wynik →
PDF → asystent; odmowy dostępu, wygasła sesja, brak pliku i awaria AI. Przy
obowiązującym zakazie przeglądarki oznaczyć test jako blocked i nie deklarować
zakończenia etapu. Commit: `test: cover critical assessment flow`.

**P8-02 — VPS.** Produkcyjny Compose, reverse proxy Caddy/HTTPS, niepubliczne
usługi danych, sekrety środowiska, backup i ćwiczenie odtworzenia PostgreSQL oraz
RustFS, procedura migracji i rollbacku wdrożenia. Faktyczny deployment wymaga
dostępu do VPS/domeny i konfiguracji. Commit: `chore(infra): prepare vps deployment`.

## 11. Definicja ukończenia i workflow AI

Przed zadaniem: przeczytaj ten dokument i `backend-progress.md`, sprawdź `git
status`, kod i istniejące testy, oznacz jedno zadanie `in_progress`. Weryfikuj
aktualną dokumentację bibliotek dla używanych API. Nie usuwaj cudzych zmian.

Podczas pracy: zakres to jedno zadanie, wraz z migracją, API, ekranem i testem,
jeżeli tak zdefiniowano. Zapisuj nowe decyzje z powodem w sekcji 3 i odwołuj się
do źródła reguły. Nigdy nie zamieniaj brakującej usługi na pozornie działające
demo. Blokery zewnętrzne zapisuj jawnie; kontynuuj niezależną pracę tylko wtedy,
gdy nie osłabia to bezpieczeństwa i kryteriów.

Po zadaniu: uruchom właściwe kontrole, zapisz konkretne komendy i wynik w progresie,
zaktualizuj następny krok, przejrzyj `git diff`, `git status` i historię, dodaj
tylko zamierzone pliki, sprawdź staged diff i utwórz krótki angielski Conventional
Commit bez body. W progresie zapisuj identyfikator zadania i nazwę commita;
hash commita zawierającego samą aktualizację progresu nie może być znany przed
jego utworzeniem, dlatego nie jest wymagany w tym samym commicie.

Stan `done` przysługuje dopiero po weryfikacji; brak przeglądarki, danych Supabase,
klucza AI lub VPS jest odnotowany, a zależne kryterium pozostaje niewykonane.
Przed każdą zmianą kodu frontendu zastosuj jego aktualne kontrole. Nie commituj
sekretów, materiałów użytkownika, `.idea/`, `.opencode/`, artefaktów builda ani
pozostałej zawartości nieśledzonego `docs/` przez zbiorcze `git add docs`.

### Dokumentacja techniczna użyta podczas planowania

- [FastAPI: zależności sesji](https://fastapi.tiangolo.com/tutorial/sql-databases/) i [nadpisywanie zależności w testach](https://fastapi.tiangolo.com/advanced/testing-dependencies/).
- [Supabase: klienci SSR](https://supabase.com/docs/guides/auth/server-side/creating-a-client) i [klucze podpisujące JWT](https://supabase.com/docs/guides/auth/signing-keys).
- [RustFS: uruchomienie kontenera](https://github.com/rustfs/rustfs#docker-quick-start-option-2).
