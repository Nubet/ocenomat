# Kompas Kompetencji — postęp backendu

Plan i obowiązujące decyzje: [backend-implementation-plan.md](backend-implementation-plan.md).
Ten plik opisuje faktyczny stan, nie planowane rezultaty. Aktualizacja: 2026-11-21.

## Bieżący stan

- **Etap:** 4 — trwały proces oceny C; P4-03 zakończone.
- **Aktywne zadanie:** brak.
- **Następny krok:** P4-04 — pełne wskaźniki z przypiętego katalogu, zapis odpowiedzi,
  wersjonowana sugestia i ręczne zatwierdzenie każdej oceny cząstkowej.
- **Ostatnia zakończona praca:** P4-03 — datowane obserwacje, szkic rozmowy
  i osobne potwierdzenie jej odbycia; autorzy/czasy, rewizje i integracja UI.
- **Stan aplikacji:** frontend łączy autoryzowane dane API z pozostałymi ekranami demo;
  backend ma `/health`
  i `/api/v1/health`, PostgreSQL, użytkowników/role, pracowników/przypisania
  i wersjonowany katalog. Lista pracowników, profile, wyszukiwarka oraz utworzenie,
   historia i szczegół ocen korzystają z API. Rewizja nowej oceny to 1, status `draft`.
   Dobór kryteriów i terminy są zapisywane w API; osobna czynność potwierdza komplet
    i zmienia status na `criteria_agreed`. Potwierdzone ustalenia są tylko do odczytu.
   `start_period` otwiera zapis obserwacji i rozmowy w `in_progress`; osobne
   potwierdzenie zapisanej daty rozmowy przechodzi do `evaluation` i zamyka edycję
   tego etapu. Odczyt odtwarza wpisy, notatki, daty i autorów bez mutacji.
  Frontend ma ekran logowania, cookie session i chroniony workspace; jego ekrany
  dalszych etapów oceny i monitoringu pozostają do podłączenia w P4/P7. Bez Supabase
  dostępny jest ekran logowania z jawną informacją o braku konfiguracji.
  RustFS działa lokalnie; integracja plików z API jest w P5-01.
  Konfigurację Supabase Auth wpisano lokalnie; publiczny JWKS potwierdza ES256.
  Użytkownik potwierdził logowanie; live HTTP potwierdził JWT, autoryzację API,
  SSR, odświeżenie cookie przez proxy i wylogowanie Server Action.
  OpenRouter i VPS niezintegrowane.
- **Kontrole frontendu:** `npm run precommit` i `npm run build` — OK,
  123 testy Vitest. Backend: 206 testów z rzeczywistym PostgreSQL i źródłowym XLSX.
- **Środowisko lokalne:** Compose korzysta z ignorowanego `.env.compose-check`;
  frontend na życzenie użytkownika przeniesiono na `http://localhost:3000`,
  pozostałe porty testowe jak w P1-03. Oddzielny `kompas-postgres-test` został
  zatrzymany po testach; wznowienie: `docker start kompas-postgres-test`.
- **Frontend commity:** `5b1375c` (`chore(frontend): add react doctor diagnostics`),
  `c37a8e0` (`perf(frontend): stabilize workspace context value`).

## Rejestr zadań

Statusy: `pending` — nie rozpoczęto; `in_progress` — praca trwa; `blocked` —
oczekuje na wskazany warunek; `done` — spełnione kryteria i kontrole. W danej
chwili jedno aktywne zadanie. Nie oznaczaj wyników planowanych jako wykonane.

| ID | Zadanie | Status | Wynik / kontrola / commit |
| --- | --- | --- | --- |
| P1-01 | Projekt FastAPI i health | done | 8 testów; `chore(backend): initialize api` |
| P1-02 | PostgreSQL, Alembic, readiness | done | 14 testów z PostgreSQL; `feat(backend): add database readiness` |
| P1-03 | Compose: frontend, API, PostgreSQL, RustFS | done | Build, HTTP, S3, restart i 19 testów UI; `chore(infra): add local compose environment` |
| P2-01 | Tożsamość, role, weryfikacja JWT | done | Testy JWT i rzeczywiste tokeny Supabase dla ADMIN/MANAGER/HR, `/me` i izolacja API OK. `feat(auth): verify identities and load roles` |
| P2-02 | Logowanie i sesja | done | Logowanie potwierdzone przez użytkownika; live HTTP: SSR cookie, proxy refresh i logout Server Action OK. E2E przeglądarkowe osobno w P8-01. `feat(auth): add sign in and session handling` |
| P2-03 | Pracownicy i przypisania | done | Migracja 0004, API list/detail/search, fikcyjny seed, lista/profile/wyszukiwarka i ochrona HR; 120 testów backendu, 45 UI, build i live HTTP OK. |
| P3-01 | Katalog kompetencji | done | Import i porównanie treści XLSX, 52 testy; `feat(catalog): add competency model` |
| P3-02 | Reguły i testy domenowe | done | 99 testów, dokładne progi i kompletność; `feat(assessments): implement scoring rules` |
| P4-01 | Utworzenie i wznowienie oceny C | done | Migracja 0005, API create/list/detail, snapshoty, współbieżna idempotencja, historia i UI UUID; 144 testy backendu, 68 UI, build i live HTTP OK. |
| P4-02 | Kryteria i terminy | done | Migracja 0006, kryteria/uzasadnienia, daty/czynności, potwierdzenie, zdarzenia i atomowa rewizja; 172 testy backendu, 94 UI, build i live HTTP/SSR OK. |
| P4-03 | Obserwacje i rozmowa | done | Migracja 0007, datowane wpisy i szkic rozmowy, jawne przejścia, autorzy/czasy, rewizje i UI; 206 testów backendu, 123 UI, build i live HTTP/SSR OK. |
| P4-04 | Wskaźniki i decyzje | pending | — |
| P4-05 | Wynik i zakończenie | pending | — |
| P5-01 | Prywatny storage | pending | — |
| P5-02 | OSP i PDF C | pending | — |
| P6-01 | Provider i baza wiedzy | pending | — |
| P6-02 | Asystent | pending | — |
| P6-03 | Analiza OSP | pending | — |
| P7-01 | Arkusz B | pending | — |
| P7-02 | Pierwsza ocena | pending | — |
| P7-03 | Monitoring HR | pending | — |
| P8-01 | Test krytycznej ścieżki E2E | blocked | Poprzednie polecenie zabrania uruchamiania przeglądarki; potrzebna zmiana instrukcji. |
| P8-02 | Konfiguracja i deployment VPS | pending | Faktyczne wdrożenie wymaga dostępu do serwera i domeny. |

## Ograniczenia i zależności zewnętrzne

- Integracja auth wymaga skonfigurowanego projektu Supabase Cloud z kluczami
  asymetrycznymi i rzeczywistych danych konfiguracyjnych; nie zapisuj sekretów tutaj.
- Żywe testy AI wymagają dostępu do OpenRouter i zgodnego z regulaminem darmowego
  modelu. Nie przełączaj się na płatne modele automatycznie.
- Aktualność dostarczonych rozporządzeń i brakująca w materiałach ustawa o służbie
  cywilnej wymagają weryfikacji przed deklarowaniem zgodności formalnej.
- Materiały w `docs/hacknation-materials/`, `.idea/` i `.opencode/` są obecnie
  nieśledzone; nie dodawaj ich przypadkowo do commitów.

## Konta środowiska testowego

Stan na 2026-11-21. Logowanie: `http://localhost:3000/login`.
Projekt Supabase: `hacknation-kompas-kompetencji`, ref `ghhpbotdloibsrfgusog`.
Role zapisane są w lokalnej bazie aplikacji, nie w metadanych Supabase.

| E-mail | Supabase Auth UID | Rola aplikacji |
| --- | --- | --- |
| `konto-admin@hacknation.pl` | `10ee8b21-a7ac-4af4-879d-d54cb9c8fe6c` | `ADMIN` |
| `konto-przelozony@hacknation.pl` | `dfc5c072-34dd-4560-8c4d-46e3defa69a1` | `MANAGER` |
| `konto-hr@hacknation.pl` | `49a8eb76-10cf-40e4-bbc9-c7dbe224e68c` | `HR` |
| `konto-testowe@hacknation.pl` | `a9c982ec-8411-4ea0-8136-48fd89c5ae9b` | Brak lokalnego profilu i dostępu |
| `nubet2137@gmail.com` | `1e8715a0-e028-4df6-bef9-e8d7a57e2728` | Brak lokalnego profilu i dostępu |

- Wszystkie adresy potwierdzone; UID zweryfikowane odczytem Supabase Auth.
- Użytkownik podał wspólne hasło dla powyższych kont. Lokalnie zapisano je jako
  `KOMPAS_TEST_ACCOUNT_PASSWORD` w ignorowanym `.env.compose-check` w katalogu
  głównym repozytorium. To notatka operatora, nie zmienna używana przez aplikację.
  Nie kopiować hasła do dokumentacji śledzonej przez Git ani nie używać do realnych danych.
- Hasło sprawdzono logowaniem kont ADMIN/MANAGER/HR w testach HTTP; nie zmieniano go.
- Przełożonemu przypisano trzech fikcyjnych pracowników: Jana, Marię i Alicję.
  Piotr pozostaje nieprzypisany; HR i ADMIN widzą wszystkich czterech.

## Wykonane zadania

### 2026-11-21 — P4-03, obserwacje i rozmowa

- Migracja `0007`: obserwacje z UUID, datą zdarzenia, tekstem i kryterium wybranym
  w tej ocenie (złożony FK); rozmowa z agendą, mocnymi stronami, obszarami rozwoju
  i opcjonalną datą czynności. Autor/czas zapisu i potwierdzenia pochodzą z serwera.
  Dotychczasowe oceny nie otrzymują fikcyjnych obserwacji, notatek ani potwierdzeń.
- API: `POST /assessments/{id}/observations`, `PUT /assessments/{id}/conversation`
  i polecenia `start_period`, `confirm_conversation` w dotychczasowych `transitions`.
  Cienkie routery delegują transakcje do serwisu; współdzielona blokada oceny
  i przypisania, świeży odczyt ORM, rewizja i zdarzenie zabezpieczają każdy zapis.
- Jawne przejścia: `criteria_agreed` → `in_progress` → `evaluation`. Szkic rozmowy
  bez daty można zapisać; potwierdzenie wymaga zapisanej daty odbytej rozmowy.
  Teksty i obserwacje są opcjonalne. Po potwierdzeniu edycja tego etapu zablokowana.
  Potwierdzenie nie zmienia czasu wcześniejszego zapisu notatek i nie jest podpisem.
- Daty czynności: od rozmowy rozpoczynającej do dzisiaj w `Europe/Warsaw`; tekst
  obserwacji 1–10 000 znaków, notatki 0–10 000. Nie narzucamy upływu planowanego
  okresu ani nowych terminów prawnych bez zweryfikowanej podstawy.
- UI: zakładki Obserwacje/Rozmowa oceniająca w trasie UUID, kryteria z przypiętego
  katalogu, daty i metadane zapisu, trzy zakładki notatek. Osobny komponent rozmowy
  odpowiada za pola i dostępność; Server Action wysyła wyłącznie dozwolone pola.
  Bez symulacji upływu okresu i bez localStorage/demo. Pomoc opisuje nowy przebieg.
- Kontrolowane wpisy pozostają zamontowane przy zmianie zakładek i po błędzie.
  Zapis blokuje nawigację i ponowną wysyłkę; konflikt zachowuje wpisy i daje nową
  kartę z zapisaną wersją. Potwierdzenie blokowane przy niewysłanych zmianach
  rozmowy lub obserwacji. Ponowienie starej rewizji nie dopisuje duplikatu.
- `uv run ruff check .`, `uv run ruff format --check .` i `uv run pytest` z
  `KOMPAS_TEST_DATABASE_URL` oraz `KOMPAS_TEST_CATALOG_XLSX` — OK, 206 testów
  bez skipów. Testy obejmują walidację, wznowienie, cudze ID, drugi przypisany
  przełożony, cofnięcie przypisania, zamknięcie etapu, rollback wpisów i potwierdzenia.
  Rzeczywiste równoległe sesje: dopisanie obserwacji kontra potwierdzenie z rewizją 6
  — jeden sukces i jeden konflikt, bez wpisu po zamknięciu etapu.
- `npm run api:types -- http://127.0.0.1:33081/openapi.json`, `npm run precommit`
  i `npm run build` — OK, 123 testy w 20 plikach. Server Actions: dozwolone pola,
  błąd sieci, sesja, walidacja, 409 bez retry/inwalidacji. UI: zapisane dane,
  niepuste szkice, blokady potwierdzenia, puste daty, tryb odczytu i escaping tekstu.
- `npm run doctor` — wykonano, 29 wskazań doradczych. Nowy formularz rozmowy
  wydzielono, formatter dat współdzielony w module. Pozostałe rozgałęzienia
  formularza obsługują jawne stany/komunikaty; inicjalizacja z props celowo zachowuje
  lokalny szkic, zamiast nadpisywać go po rewalidacji. Brak wyciszania reguł.
- Compose `up --build --detach --wait --wait-timeout 180 backend`, następnie
  `frontend` — OK; migracja `0007` wdrożona bez resetu danych.
- Live HTTP/SSR bez przeglądarki: rzeczywisty MANAGER, utworzenie i ustalenia →
  start → obserwacja/data/autor → retry 409 → szkic bez daty → odmowa potwierdzenia
  422 → zapis daty → potwierdzenie `evaluation`/rewizja 9 → reload i tryb odczytu.
  HR/ADMIN: GET/POST/PUT i trasa SSR cudzej oceny 404. Smoke usunął wyłącznie swój
  rekord filtrowany autorem i losowym kluczem żądania; sesje testowe wylogowano.
- Nie wykonywano przeglądarkowego E2E ani wizualnego sprawdzenia. P8-01 pozostaje
  blocked. P4-04/05 nadal do wdrożenia; następny krok: P4-04.
- Commit: `feat(assessments): persist observations and conversation`.

### 2026-11-21 — pomoc i komunikaty według uprawnień

- Pomoc opisuje osobno przełożonego, HR i administratora, oznacza role bieżącego
  konta i pokazuje odpowiadające im odnośniki. Wyjaśnia własne autorstwo oceny,
  aktualne przypisanie, wiele ról, powrót do zapisu i postępowanie przy konflikcie.
- Usunięto nieaktualne informacje o braku backendu, wyłącznie lokalnym zapisie
  i demonstracyjnych kryteriach oraz reset demo z Pomocy. Funkcje niegotowe
  (monitoring HR, panel ról/przypisań, dokumenty, AI) są opisane zgodnie ze stanem.
- Pusta lista ocen: przełożony z przypisaniem dostaje przycisk Nowa ocena;
  bez przypisania instrukcję kontaktu z administratorem i wskazanie, jakie dane
  podać. HR dostaje przejście do pracowników; administrator instrukcję zlecenia
  zmiany roli/przypisania operatorowi. Nie sugerujemy im prowadzenia ocen bez MANAGER.
- Profil pracownika sprawdza `assigned_only=true`, także dla kont z MANAGER+ADMIN,
  zanim zaproponuje nową ocenę. Szeroki dostęp do profili nie zastępuje przypisania.
- Przy pustej liście pracowników, błędach tworzenia i wyszukiwaniu komunikaty
  podają prosty następny krok. Usunięto techniczny język o API/kluczach żądania
  z tworzenia oceny. Nowa ocena nie jest proponowana dwukrotnie na pustym ekranie.
- `npm run precommit` i `npm run build` — OK, 94 testy w 17 plikach. Testy obejmują
  treści/akcje według ról i brak przycisku dla nieprzypisanego profilu widocznego
  przez dodatkową rolę administratora. Live SSR HTTP: Pomoc i pusta lista HR/ADMIN
  z właściwymi komunikatami i bez przycisku tworzenia — OK.
- Przeglądarkowego E2E nie wykonano zgodnie z wcześniejszym zakazem. Następny
  etap pozostaje P4-03; nie zmieniano uprawnień kont w środowisku.
- Commit: `fix(frontend): explain roles and actionable next steps`.

### 2026-11-21 — P4-02, kryteria i terminy

- Dotychczasowe P2-03/P4-01 zapisano po ponownej kontroli (144 testy backendu,
  68 UI) jako `64b5a18 feat(assessments): persist employee assessment workflows`.
- Migracja `0006`: daty i trzy jawne potwierdzenia domyślnie false, relacyjne
  `assessment_criteria` i `assessment_events`. Istniejące szkice zachowane;
  brak migracji z demo i fikcyjnych dat. Katalog oceny pozostaje niezmieniony.
- PUT kryteriów: pięć obowiązkowych C z reguł backendu i 0–3 dodatkowe UUID
  z przypiętej wersji; bez duplikatów, każde dodatkowe z uzasadnieniem 1–4000 znaków.
- PATCH dat/czynności: obie daty, kolejność, jawne booleany; można zaplanować
  przyszłą rozmowę, ale nie potwierdzić przyszłych czynności jako wykonanych.
  Nie automatyzujemy terminów ustawowych bez zweryfikowanych źródeł.
- POST `transitions` / `agree_criteria`: komplet kryteriów, dat i czynności,
  dopiero wtedy `draft` → `criteria_agreed`. Ustalenia po potwierdzeniu zablokowane.
  Zapis czynności nie jest podpisem ani potwierdzeniem doręczenia.
- Wspólny serwis transakcyjny blokuje ocenę i aktualne przypisanie, odświeża stan
  po blokadzie i sprawdza rewizję. Zmiana + inkrementacja + zdarzenie z autorem
  i czasem UTC są atomowe; potwierdzenie ma też datę rozmowy. Konflikt → 409,
  błędne dane → 422, cudza/brakująca ocena → 404.
- UI kontekstu stanowiska, kryteriów i terminów korzysta z API i przypiętego
  katalogu, bez localStorage i bez udawanej analizy OSP. Przy błędzie wpisy zostają;
  konflikt blokuje kolejne zapisy i daje link do zapisanej wersji w nowej karcie.
  Pola pozostają dostępne do skopiowania. Nawigacja/GET nie zmieniają statusu.
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest` z
  `KOMPAS_TEST_DATABASE_URL` (oddzielny PostgreSQL) i `KOMPAS_TEST_CATALOG_XLSX`
  (źródłowy XLSX) — OK, 172 testy bez skipów. Nowe przypadki: limit, duplikaty,
  przypięty katalog, błędne daty, niepełne czynności, izolacja i cofnięte przypisanie,
  równoległe połączenia z rewizją 1 (jeden zapis, jeden konflikt), rollback zdarzenia.
- `npm run api:types -- http://127.0.0.1:33081/openapi.json`, `npm run precommit`
  i `npm run build` — OK; 94 testy w 17 plikach, także kontrole UI i komunikatów ról.
- Compose `up --build --detach --wait --wait-timeout 180 backend`, następnie
  `frontend` — OK; migracja 0006 wdrożona bez resetu danych. Pierwsza próba SSR
  wykryła stary moduł po hot reload; po przebudowie frontendu test przeszedł.
- Live HTTP bez przeglądarki: rzeczywisty MANAGER, create → kryteria (6) → retry
  starej rewizji 409 → daty/czynności → potwierdzenie (rewizja 4), ponowny odczyt
  i SSR kryteriów/uzasadnienia/dat/stanu — OK. HR/ADMIN: cudza ocena 404.
  Dwa kolejne uruchomienia smoke usunęły wyłącznie własne rekordy według autora
  i losowego klucza żądania; konta i inne oceny nietknięte. Sesje smoke wylogowano.
- Nie uruchamiano przeglądarki. Dalsze obserwacje, rozmowa oceniająca, cząstkowe
  decyzje i wynik pozostają do P4-03–05. Następny krok: P4-03.
- Commit: `feat(assessments): persist criteria and dates`.

### 2026-11-21 — P4-01, trwałe rozpoczęcie i wznowienie C

- Migracja `0005`: osobne UUID ocen, FK do pracownika/oceniającego/katalogu,
  snapshot profilu JSONB, formularz C, `draft`, rewizja 1, autor i czas UTC.
  Nowy proces nie zastępuje poprzedniego; zmiana profilu lub katalogu nie zmienia historii.
- Podział modułu: modele/kontrakt, serwis transakcyjny bez FastAPI i cienki router.
  Reguły w `rules.py` pozostają niezależne. Wspólny transport serwerowy frontendu
  obsługuje token, timeout i brak cache; feature loaders/actions obsługują rezultat.
- `POST /api/v1/assessments` przyjmuje tylko employee UUID i `kind=periodic` oraz
  wymagany `Idempotency-Key` UUID. Pierwszy zapis → 201, replay → 200 z tym samym
  UUID, ten sam klucz z innymi danymi → 409. Blokada transakcyjna PostgreSQL
  i unikalność `(assessor_id, idempotency_key)` chronią także równoległe retry.
- Lista (także po employee UUID) i szczegół sprawdzają MANAGER, własne autorstwo
  i aktualne przypisanie. HR/ADMIN ani drugi przypisany przełożony nie dostają
  automatycznie dostępu do cudzej oceny. GET i `?step=` nie przesuwają statusu.
  A/B i first → 422; brak katalogu → 503. Bez demo fallbacku i pól nadawanych przez klienta.
- `assigned_only=true` w API pracowników zasila wybór także dla kont MANAGER+HR/ADMIN.
  Nie wystarcza szeroka widoczność podstawowych profili do tworzenia oceny.
- UI: `/assessments/new`, cztery kroki w stylu istniejącej konfiguracji; Server
  Action i blokada formularza podczas zapisu, zachowany wybór i klucz po błędzie,
  nowy klucz przy zmianie pracownika. Lista i profile pokazują pełną własną historię.
- Trasa `/assessments/{assessmentId}` zastąpiła slug pracownika. Stare slugi → 404;
  linki z demo pulpitu kierują do prawdziwej listy. Usunięto stały licznik ocen
  i podłączenie demo nawigacji w sidebarze. Tworzenie w UI tylko dla MANAGER.
  Asystent nie udaje kontekstu zapisanej oceny. Legacy komponenty kolejnych kroków
  pozostają wzorcem UI, ale nowa trasa ich nie montuje i nie używa localStorage.
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest` z oddzielnym
  PostgreSQL i źródłowym XLSX — OK, 144 testy bez skipów. Testy obejmują upgrade
  i `alembic check`, historię, snapshoty, izolację i cofnięte przypisanie, walidację,
  retry/409 i rzeczywiste równoległe tworzenie na dwóch połączeniach.
- `npm run api:types -- http://127.0.0.1:33081/openapi.json`, `npm run precommit`
  i `npm run build` — OK; 68 testów, dynamiczne trasy list/new/UUID. Po zmianie
  parametru trasy usunięto wyłącznie stare wygenerowane typy `.next/dev/types`;
  ponowny typegen i build przeszły.
- Compose: build i `up --detach --wait` API z migracją 0005 oraz frontend — OK.
- Live HTTP bez przeglądarki: realna sesja MANAGER, GET formularza i POST Server
  Action → 303 do UUID, ponowiony POST → ten sam UUID, nowy klucz → drugi proces;
  lista i historia w profilu pokazują oba. Dwa odczyty z `?step=rating` nadal dają
  ten sam szkic; odpowiedzi prywatne/no-store. Stary `/assessments/jan` → 404.
  Usunięto wyłącznie dwa rekordy utworzone przez smoke (po autorze i własnych kluczach).
- Końcowe SSR HTTP na ADMIN/HR/MANAGER: lista → 200, przycisk tworzenia na pulpicie
  tylko u MANAGER, bezpośrednie `/assessments/new` → 404 dla ADMIN/HR i 200 dla MANAGER.
- Nie wykonano przeglądarkowego E2E (P8-01 nadal blocked). Kryteria, terminy,
  obserwacje, oceny i przejścia nie są jeszcze edytowane w nowym procesie;
  UI pokazuje ten zakres jawnie. Następny krok: P4-02.

### 2026-11-21 — P2-03 i domknięcie live P2-01/P2-02

- Migracja `0004`: jednostki, pracownicy i przypisania z FK, PK, indeksem
  oraz ograniczeniami nazw i typu stanowiska. Bez zmiany wcześniejszych migracji.
- API list/detail i wyszukiwanie po nazwie; filtrowanie uprawnień w SQL,
  identyczne 404 dla cudzego i brakującego UUID, prywatne odpowiedzi bez cache.
  MANAGER tylko przypisani, HR/ADMIN podstawowe dane organizacji, bez ról pusta lista.
- Jawny seed fikcyjnych pracowników wykonano dwukrotnie w Compose bez duplikatów;
  trzy przypisania do testowego MANAGER, czwarta osoba bez przypisania.
- Frontend: lista i `/employees/{UUID}`, wyszukiwarka z tych samych danych API,
  odróżnione puste/błędne odpowiedzi, bez połączenia nowych profili z localStorage.
  Link HR i bezpośrednia trasa wymagają HR (ADMIN sam nie wystarcza).
- Typy OpenAPI: `npm run api:types -- http://127.0.0.1:33081/openapi.json`.
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest` z testowym
  PostgreSQL i źródłowym XLSX — OK, 120 testów, bez skipów; obejmują upgrade,
  `alembic check`, manager A/B, HR/admin, wygasłe sesje, FK i powtarzalny seed.
- `npm run precommit` — OK, 45 testów (włączono także pliki `.test.tsx`), format,
  lint i TypeScript. `npm run build` — OK; profile pracowników są dynamiczne.
- Compose `up --build --detach --wait`: migracja i usługi API/frontend — OK.
- Live HTTP bez przeglądarki: realne logowanie ADMIN/MANAGER/HR, weryfikacja JWT
  przez `/me`, list/detail i izolacja (4/3/4 osób, cudzy profil → 404), refresh
  i local logout po stronie providera — OK; tokeny wyłącznie w pamięci.
- Live SSR z cookies: lista na wszystkich rolach i brak cache, HR → 200 tylko
  dla HR, pozostałym → 404; anonimowe `/employees` → 307 do logowania.
  W osobnej sesji testowej celowo przeterminowano metadane `expires_at` cookie
  (nie podpisany JWT): proxy odświeżyło sesję i zwróciło nowe cookies. POST formularza
  wylogowania wykonał Server Action → 303 `/login`, usunął cookies; następny GET
  chronionej strony → 307 `/login`. Nie wylogowywano sesji użytkownika.
- Użytkownik osobno potwierdził działające logowanie w UI. P2-01/P2-02 domknięte;
  przeglądarki ani E2E nie uruchamiano (P8-01 nadal blocked). Dashboard, procesy
  ocen i monitoring nadal są demo; nowy profil nie tworzy pozornej oceny.
- Testowy kontener PostgreSQL zatrzymano po kontrolach; środowisko Compose pozostaje uruchomione.
- Następny krok: P4-01.

### 2026-11-21 — pierwsze profile użytkowników

- Odczyt Supabase Auth potwierdził pięć kont i potwierdzone adresy e-mail.
- Istniejącym CLI `app.modules.users.bootstrap` utworzono pierwszego lokalnego
  administratora; kontom przełożonego i HR dodano profile przez istniejące modele
  ORM w jednej transakcji z kontrolą braku wcześniejszych profili.
- Ponowny odczyt po zapisie: trzy aktywne profile, dokładnie role ADMIN, MANAGER, HR.
  Konto testowe i prywatne pozostawiono bez lokalnego profilu i uprawnień.
- Nie zmieniano haseł ani metadanych Supabase. Nie wprowadzano kodu ani migracji.
  Logowanie rzeczywistym hasłem, refresh i logout pozostają do sprawdzenia przez
  użytkownika; przeglądarki nie uruchamiano. P2-01/P2-02 nadal blocked.
- Następny krok: użytkownik loguje się kontem administratora na porcie 3000;
  następne zadanie implementacyjne pozostaje P2-03 (pracownicy i przypisania).

### 2026-11-21 — konfiguracja projektu Supabase Auth

- Uzupełniono ignorowany `.env.compose-check` o URL projektu i publishable key;
  frontend i CORS zmieniono na `http://localhost:3000`. Bez zmiany bazy aplikacji.
- Zatrzymano `next dev` tego projektu zajmujący port 3000 i uruchomiono frontend
  Compose. Po konflikcie portu wymagane było ponowne utworzenie kontenera frontendu.
- Compose `config --quiet`, `up --detach --wait` i ponowne utworzenie frontendu
  — OK; HTTP `/login` na porcie 3000 → 200. Publiczny JWKS projektu → ES256.
- Połączenie zarządzające Supabase aktywne; projekt i usługa Auth `ACTIVE_HEALTHY`.
  Odczyt konfiguracji potwierdził Site URL `http://localhost:3000`, email provider
  i rotację refresh tokenów włączone, anonymous/manual linking wyłączone.
- Wyłączono publiczną rejestrację (`disable_signup=true`) i włączono potwierdzanie
  e-maila (`mailer_autoconfirm=false`); ponowny odczyt potwierdził zapis.
- Odczyt `auth.users` bez sekretów: brak nieusuniętych kont. Następny krok:
  utworzyć uzgodnione konto Auth z potwierdzonym e-mailem i powiązać je z pierwszym
  lokalnym administratorem. Hasło bazy Supabase nie jest do tego potrzebne.
- Logowanie, refresh i logout nadal niezweryfikowane; P2-01/P2-02 pozostają blocked.

### 2026-11-21 — P2-01, obsługa pustego JWKS

- Pusty lub niepoprawny zestaw kluczy providera zwraca 503 zamiast nieobsłużonego
  błędu; nie otwiera dostępu. Dodano przypadek regresyjny pustego JWKS.
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest`
  z testowym PostgreSQL i oryginalnym XLSX — OK, 100 testów, bez skipów.
- Commit: `fix(auth): handle unusable signing key sets`.
- Następny krok pozostaje P2-03. Próby z realnym Supabase nadal niewykonane.

### 2026-11-21 — P2-02 (kod gotowy, integracja live blocked)

- Server Actions logowania/wylogowania, `@supabase/ssr`, cookie HttpOnly, proxy
  odświeżania z nagłówkami bez cache, `getClaims()` i serwerowe przekazanie tokenu
  do FastAPI `/me`; sidebar używa profilu z API. Brak konfiguracji nie otwiera demo.
- Typy wygenerowano z aktualnego OpenAPI przez `openapi-typescript`; instrukcja
  regeneracji i `.env.example` frontendu. Workspace wymuszony dynamicznie.
- `npm run precommit` — OK, format/Oxlint/TypeScript i 33 testy. `npm run build`
  — OK; workspace routes są dynamiczne. Testy obejmują odrzucenie niezweryfikowanej
  sesji, konto nieaktywne, awarię API/providera, wylogowanie i propagację cookie.
- Compose `config --quiet`, `up --build --detach --wait` — OK po nowych zależnościach.
  HTTP bez przeglądarki: `/` → 307 `/login`, `/login` → 200 z informacją o braku
  konfiguracji; obie odpowiedzi bez współdzielonego cache.
- Brak realnej konfiguracji Supabase; nie sprawdzono rzeczywistego logowania,
  odświeżenia i wylogowania ani wyglądu w przeglądarce. P2-02 pozostaje `blocked`.
- Commit: `feat(auth): add sign in and session handling`.
- Następny krok: P2-03. Ekrany biznesowe nadal są demo i nie służą do realnych danych.

### 2026-11-21 — P3-02

- Czyste reguły B/C, unikalne i znane kryteria, do trzech dodatkowych,
  średnia okresowa >4 i brak 1, kompletność, odrębna wersjonowana sugestia,
  punktowe warunki pierwszej oceny i jawna podstawa zwolnienia z egzaminu.
- Średnie jako `Fraction`; brak danych nie daje formalnego wyniku. Ustalanie
  terminów i kwalifikacji prawnej pozostaje do weryfikacji źródeł w P7-02.
- `uv run ruff check .`, `uv run ruff format .`, `uv run pytest` z testowym
  PostgreSQL i źródłowym XLSX — OK, 99 testów. Test źródła potwierdza także,
  że wymagane kryteria B/C odpowiadają rzeczywistym UUID zaimportowanego katalogu.
- Commit: `feat(assessments): implement scoring rules`.
- Następny krok: P2-02; weryfikacja realnego Supabase nadal blocked.

### 2026-11-21 — P3-01

- Migracja `0003`, niezmienne wersje JSONB z SHA-256 i stabilnymi UUID kryteriów
  i wskaźników; importer waliduje arkusze, ilości, kompletność, formuły i znaki.
  Chroniony endpoint katalogu i jawny odczyt wersji historycznej.
- `uv sync`, `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run pytest` z testową bazą i `KOMPAS_TEST_CATALOG_XLSX` — OK, 52 testy.
  Porównano wszystkie nazwy, wskaźniki i opisy poziomów z oryginalnym XLSX.
- Lokalna baza Compose: `uv run alembic upgrade head`, dwukrotne
  `uv run python -m app.modules.catalog.importer
  '../docs/hacknation-materials/Model_kompetencji.xlsx' --version model-2026-11-21`
  z lokalnym `KOMPAS_DATABASE_URL` — OK; bez duplikatów i bez zmiany źródła.
- Materiał XLSX nie został dodany do repo; po klonowaniu operator dostarcza plik.
  Chronione API sprawdzono z podpisanym tokenem testowym, nie realnym Supabase.
- Commit: `feat(catalog): add competency model`.
- Następny krok: P3-02; P2-01 nadal blocked wyłącznie weryfikacją live.

### 2026-11-21 — P2-01 (kod gotowy, integracja live blocked)

- Migracja `0002`: użytkownicy i wielokrotne role z constraintami; `/api/v1/me`
  czyta aktywne konto i role z PostgreSQL, ignorując biznesowe role z JWT.
- JWKS PyJWT: przypięty ES256/RS256, issuer/audience/exp/iat/sub, UUID, cache,
  rotacja i timeout; 401/503 bez szczegółów i bez bypassu. Bootstrap pierwszego
  admina jako CLI, z blokadą transakcyjną i odmową ponownego utworzenia.
- Kontrole w `backend/`: `uv sync`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run pytest` z oddzielną bazą PostgreSQL —
  OK, 45 testów. Obejmują podpisy EC/RSA, fałszerstwo, algorytmy, claims, JWKS
  cache/rotację/awarię, nieaktywne i nieznane konto, role z bazy oraz bootstrap.
- Nie znaleziono zmiennych konfiguracji Supabase w środowisku. Nie tworzono kont
  zewnętrznych ani nie wykonywano próby z prawdziwym tokenem. P2-01 pozostaje
  `blocked` do rzeczywistej weryfikacji integracji.
- Commit: `feat(auth): verify identities and load roles`.
- Następne niezależne zadania: P3-01 katalog oraz P3-02 reguły domenowe.

### 2026-11-21 — P1-03

- Dockerfile obu aplikacji, Compose z czterema usługami i jednorazowym `migrate`,
  trwałe wolumeny, dev reload, porty wyłącznie loopback, `.env.example` i instrukcja.
- `docker compose --env-file .env.compose-check -f infra/compose.yaml
  -f infra/compose.dev.yaml config --quiet` i `up --build --detach --wait
  --wait-timeout 180` — OK po ponowieniu powolnych pobrań. Docker Hub zwracał 429;
  oficjalne obrazy Node/Python pobrano z publicznego mirroru ECR.
- HTTP frontend 200 (treść Kompas), API readiness 200; podpisany boto3 S3
  create/put/get — OK. `restart db rustfs`, ponowne `up --wait`, odczyt rewizji
  `0001` z bazy i wcześniejszego obiektu S3 — OK; obiekty smoke-testu usunięte.
- RustFS 1.0.6: `/health` działa, `id` potwierdza UID/GID 10001, zapis na nazwanym
  wolumenie działa bez roota. `npm run precommit` — OK, 19 testów frontendu.
- Testowe środowisko używa ignorowanego `.env.compose-check` i niestandardowych
  portów 33080/33081/35432/39000/39001; wyłącznie dane lokalnej weryfikacji.
- Commit: `chore(infra): add local compose environment`.
- Następny krok: P2-01. Nie sprawdzano wyglądu w przeglądarce ani produkcji.

### 2026-11-21 — P1-02

- Synchroniczne SQLAlchemy 2/psycopg 3, sesja per request, zamykanie poola,
  maskowany i walidowany URL, timeout połączenia/zapytania; readiness z `SELECT 1`.
- Alembic: bazowa rewizja `0001` bez domeny, upgrade i sprawdzanie zgodności.
- Kontrole w `backend/`: `uv run ruff check .`, `uv run ruff format --check .`
  i `uv run pytest` z `KOMPAS_TEST_DATABASE_URL` — OK, 14 testów, bez skipów.
  Testy sprawdziły rzeczywiste PostgreSQL 17.7, dwukrotny upgrade, `alembic check`,
  brak konfiguracji i awarię połączenia (503 bez ujawnienia URL).
- Oddzielny lokalny kontener `kompas-postgres-test`, port loopback 55439, baza
  `kompas_test`; tylko fikcyjne dane testowe. Nie resetowano istniejących baz.
- Commit: `feat(backend): add database readiness`.
- Następny krok: P1-03; brak testów przeglądarkowych zgodnie z instrukcją.

### 2026-11-21 — P1-01

- FastAPI factory, Python 3.13, uv.lock, Pydantic Settings, restrykcyjny CORS,
  `/health`, instrukcja uruchomienia i ignorowanie artefaktów backendu.
- Kontrole w `backend/`: `uv sync --locked`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run pytest` — OK, 8 testów.
- Pierwsze pobieranie zależności przekroczyło timeout; ponowienie zakończone.
  Starlette ostrzega o przyszłym wycofaniu httpx w TestClient; testy działają.
- Commit: `chore(backend): initialize api`.
- Następny krok: P1-02. Nie uruchamiano przeglądarki ani usług zewnętrznych.

## Szablon wpisu po zadaniu

Dodaj na początku tej sekcji krótki wpis, zaktualizuj tabelę i następny krok:

```text
DATA — ID — rezultat
Kontrole: dokładne komendy i wynik; niewykonane kontrole oraz powód.
Migracje / konfiguracja: istotne zmiany, bez sekretów.
Commit: conventional commit subject.
Następny krok / blokery: konkretne informacje potrzebne kolejnej sesji.
```
