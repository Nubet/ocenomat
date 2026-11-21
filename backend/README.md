# Kompas Kompetencji API

Python 3.13 i uv. Polecenia uruchamiaj w `backend/`:

```sh
uv sync --locked
uv run uvicorn app.main:create_app --factory --reload
```

`GET /health` sprawdza wyłącznie działanie procesu. CORS domyślnie nie dopuszcza
żadnego originu. Lokalnie ustaw `KOMPAS_CORS_ORIGINS='["http://localhost:3000"]'`.
Konfiguracja pochodzi ze zmiennych środowiskowych; aplikacja nie ładuje plików
`.env` automatycznie.

Kontrole:

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## PostgreSQL i migracje

Ustaw `KOMPAS_DATABASE_URL` na URL `postgresql+psycopg://USER:PASSWORD@HOST/DB`.
Hasło w URL musi być zakodowane procentowo. Wartość jest maskowana w reprezentacji
ustawień; nie publikuj zmiennych ani pełnych komunikatów sterownika.

```sh
uv run alembic upgrade head
uv run alembic check
```

Migracje uruchamiaj jawnie przed API. Początkowa rewizja ustanawia historię bez
tworzenia tabel domenowych. Sesja na żądanie zamyka i wycofuje niezatwierdzoną
transakcję; operacje biznesowe będą jawnie zarządzać commitem.

`GET /api/v1/health` wykonuje `SELECT 1`; brak konfiguracji lub awaria bazy zwraca
503 bez szczegółów połączenia. Nie sprawdza schematu ani innych usług.

Test integracyjny wymaga `KOMPAS_TEST_DATABASE_URL` wskazującego **oddzielną bazę
testową PostgreSQL**. Wykonuje upgrade i sprawdzenie schematu, nigdy reset danych:

```sh
uv run pytest -m integration
```

Bez tej zmiennej test integracyjny jest jawnie pomijany.

## Tożsamość i pierwszy administrator

`KOMPAS_SUPABASE_URL` to HTTPS origin projektu Supabase Cloud (bez `/auth/v1`).
`KOMPAS_JWT_ALGORITHM` ustaw zgodnie z kluczem projektu: `ES256` (domyślnie) lub
`RS256`. HS256 nie jest obsługiwany. JWKS pobierany jest wyłącznie z ustalonego
projektu, z cache 5 minut i timeoutem 5 s. PyJWT ogranicza odświeżanie nieznanych
`kid` do jednego na 30 s; przy rotacji opublikuj nowy klucz przed jego użyciem.
Restart API czyści cache. Niedostępny provider nigdy nie otwiera dostępu.

Najpierw operator tworzy konto w Supabase (publiczna rejestracja wyłączona).
Następnie, po migracji `0002`, jawnie tworzy pierwszego lokalnego administratora:

```sh
uv run python -m app.modules.users.bootstrap --subject SUPABASE_USER_UUID --display-name "Administrator"
```

Polecenie nie tworzy konta Supabase i nie weryfikuje go zdalnie; operator musi
skopiować właściwy UUID. Odmawia, gdy administrator lub ten subject już istnieje;
blokada transakcyjna serializuje równoczesne próby. Nie ma publicznego endpointu
bootstrap ani automatycznego nadawania ról przy logowaniu.

`GET /api/v1/me` wymaga `Authorization: Bearer ACCESS_TOKEN`. Sprawdza podpis,
algorytm, issuer, audience, expiry, issued-at i UUID subject, a potem aktywne konto
w naszej bazie. Role i nazwa pochodzą z bazy, nie z claimów tokenu. Brak/nieważny
token i nieznane/nieaktywne konto zwracają 401; brak konfiguracji auth lub awaria
JWKS — 503. Tokenów nie umieszczaj w adresach URL, plikach ani historii powłoki.

Testy generują jednorazowe klucze w pamięci i zastępują tylko transport JWKS;
testy `/me` wykonują prawdziwą weryfikację podpisu oraz odczyt PostgreSQL.
Próby z rzeczywistym Supabase i ich zakres zapisujemy w `docs/backend-progress.md`
w katalogu głównym repozytorium.

## Pracownicy i przypisania

Migracja `0004` dodaje komórki organizacyjne, pracowników i przypisania przełożonych.
Instalacja obejmuje jedną organizację. Typ stanowiska rozróżnia `OFFICE_HEAD`,
`DIRECT_MANAGER` i `OTHER`; nie jest rolą konta użytkownika.

- `GET /api/v1/employees` — lista podstawowych danych, opcjonalnie `?q=fragment`
  wyszukujący po nazwie (maks. 100 znaków; `%` i `_` traktowane dosłownie).
- `GET /api/v1/employees/{UUID}` — te same dane jednego pracownika.
- `?assigned_only=true` zawęża listę do przypisań MANAGER także przy dodatkowej
  roli HR/ADMIN; służy do wyboru pracownika do nowej oceny.
- `MANAGER` widzi wyłącznie przypisanych; `HR` i `ADMIN` podstawowe dane całej
  organizacji. Bez roli lista jest pusta. Cudze i nieistniejące ID zwracają 404.
- Listę filtruje zapytanie SQL, nie frontend. Schemat nie zawiera notatek ani ocen;
  dostęp do tych danych będzie wymagał osobnej autoryzacji w P4.

Seed jest jawną operacją operatora, nigdy częścią startu aplikacji ani migracji:

```sh
uv run python -m app.modules.employees.seed --manager-subject SUPABASE_MANAGER_UUID
```

Wymaga aktywnego lokalnego użytkownika `MANAGER`. Tworzy cztery **fikcyjne** osoby
w jednostce testowej: Jan Kowalski, Maria Wiśniewska, Alicja Zielińska i Piotr Nowak.
Pierwsze trzy przypisuje wskazanemu przełożonemu, Piotra pozostawia bez przypisania.
Ponowienie nie tworzy duplikatów ani nie nadpisuje istniejących danych pracowników.
Nie importuje stanu demo z przeglądarki. W Compose poprzedź polecenie
`docker compose --env-file .env.compose-check -f infra/compose.yaml -f infra/compose.dev.yaml exec -T backend`
i użyj `python` bez `uv run` (polecenie uruchamiane z katalogu głównego repo).

## Katalog kompetencji

Po migracji `0003` operator importuje lokalny materiał (nie jest częścią repo):

```sh
uv run python -m app.modules.catalog.importer '../docs/hacknation-materials/Model_kompetencji.xlsx' --version model-2026-11-21
```

Importer weryfikuje tabelę źródłową, 14 kompetencji, 49 wskaźników i pięć opisów
na wskaźnik. Zachowuje tekst bez usuwania polskich znaków i podziałów wierszy,
odrzuca formuły i niepełne arkusze. UUID zależą od nazwy/opisu, nie kolejności.
Wersja jest snapshotem JSONB z nazwą źródła i SHA-256. Ponowny import tego samego
pliku i wersji niczego nie powiela; inna zawartość pod tą wersją jest odrzucana.
Zmiana tekstu wskaźnika zmienia jego ID; historia pozostaje w poprzedniej wersji.

`GET /api/v1/catalog/criteria` wymaga aktywnego użytkownika. Zwraca najnowszą
zaimportowaną wersję, a `?version_id=UUID` wskazaną wersję historyczną; brak
katalogu zwraca 404. Nie ma automatycznego pobierania materiałów ani danych demo.

Ustaw `KOMPAS_TEST_CATALOG_XLSX` na ścieżkę do źródła, by test porównał każdy opis
i każdy poziom z oryginałem. Bez pliku ta dodatkowa kontrola jest jawnie pomijana;
testy parsera i API korzystają z generowanego, fikcyjnego workbooka.

## Utworzenie i wznowienie oceny C

Migracja `0005` dodaje `assessments`. Router odpowiada za kontrakt HTTP, serwis
za transakcję i dostęp, a `rules.py` pozostaje niezależne od HTTP i bazy.

```text
POST /api/v1/assessments
Idempotency-Key: UUID
{"employee_id": "UUID", "kind": "periodic"}

GET /api/v1/assessments
GET /api/v1/assessments?employee_id=UUID
GET /api/v1/assessments/{assessment_id}
```

- Tworzy wyłącznie aktywny MANAGER z przypisaniem do pracownika. Dane oceniającego,
  formularz, status i rewizja pochodzą z API; dodatkowe pola żądania są odrzucane.
- Stanowisko `OTHER` tworzy C; A/B oraz pierwsza ocena nie są jeszcze obsługiwane.
  Bez katalogu tworzenie zwraca 503, bez zastępowania źródła danymi demo.
- Zapis zawiera UUID procesu, autora, czas UTC, `draft`, rewizję 1, migawkę
  podstawowych danych pracownika i FK do niezmiennej wersji katalogu. Zmiana profilu
  lub import nowego katalogu nie zmienia wcześniejszej oceny.
- Pierwsze żądanie zwraca 201 i `Location`, ponowienie z tym samym kluczem i danymi
  200 oraz ten sam UUID. Ten sam klucz z innym pracownikiem zwraca 409.
  Klucz jest unikalny w obrębie oceniającego; blokada transakcyjna PostgreSQL
  serializuje równoległe ponowienia. Nowy klucz tworzy osobny proces i zachowuje historię.
- Lista i szczegół wymagają roli MANAGER, własnego autorstwa i aktualnego przypisania.
  Samo HR/ADMIN ani przypisanie drugiego przełożonego nie otwiera cudzej oceny.
  Brak dostępu do szczegółu zwraca 404, lista bez dostępnych procesów jest pusta.
- GET, odświeżenie i parametry nawigacji nie zmieniają statusu ani rewizji.
  Edycja ustaleń jest dostępna w szkicu przez poniższe operacje.

## Kryteria i terminy oceny C

Migracja `0006` dodaje kryteria oceny, daty/czynności i zdarzenia audytowe.

```text
PUT   /api/v1/assessments/{id}/criteria
{"revision": 1, "additional": [{"criterion_id": "UUID", "justification": "Obowiązki z OSP"}]}

PATCH /api/v1/assessments/{id}
{"revision": 2, "date_talk": "2026-01-10", "date_assessment": "2027-01-10",
 "duties_discussed": true, "expectations_discussed": true, "arrangements_shared": true}

POST  /api/v1/assessments/{id}/transitions
{"revision": 3, "action": "agree_criteria"}
```

- API dobiera pięć obowiązkowych kryteriów C. Dodatkowe: 0–3 unikalne ID z katalogu
  przypiętego do oceny, bez powielania obowiązkowych, z niepustym uzasadnieniem
  do 4000 znaków. Zapis zastępuje zestaw tylko w szkicu, bez zmiany katalogu.
- Daty są `date`, termin oceny nie może poprzedzać rozmowy. Można zaplanować
  przyszłą rozmowę i zapisać niepełne potwierdzenia; nie można odnotować przyszłej
  rozmowy jako wykonanej. Nie obliczamy terminów prawnych na podstawie demo.
- Potwierdzenie wymaga zapisanego zestawu, obu dat i trzech wykonanych czynności;
  dopiero to polecenie zmienia `draft` na `criteria_agreed`. Kolejne zmiany ustaleń
  są odrzucane. To rejestr czynności, nie podpis ani dowód doręczenia.
- Wszystkie mutacje sprawdzają autorstwo, MANAGER i aktualne przypisanie. Ocena
  i przypisanie są blokowane w transakcji; rewizja jest sprawdzana po uzyskaniu
  blokady. Starsza rewizja lub niedozwolony stan → 409, błędne dane → 422,
  cudzy/brakujący zasób → 404. Zapis i zdarzenie z autorem/czasem są atomowe.
- GET zwraca zapisane kryteria/daty/czynności i obowiązkowe ID; nie przesuwa stanu.
  Frontend pobiera katalog wyłącznie przez `version_id` zapisany w ocenie.

## Obserwacje i rozmowa oceniająca

Migracja `0007` dodaje `assessment_observations` i `assessment_conversations`.
Obserwacja ma własne UUID, kryterium (FK do wyboru w tej ocenie), tekst,
datę zdarzenia, autora i czas zapisu UTC. Rozmowa ma agendę, mocne strony,
obszary rozwoju, opcjonalną datę czynności oraz osobny autor/czas potwierdzenia.

```text
POST /api/v1/assessments/{id}/transitions
{"revision": 4, "action": "start_period"}

POST /api/v1/assessments/{id}/observations
{"revision": 5, "criterion_id": "UUID", "text": "Sytuacja — działanie — rezultat",
 "occurred_on": "2026-02-12"}

PUT /api/v1/assessments/{id}/conversation
{"revision": 6, "agenda": "", "strengths": "", "growth": "", "occurred_on": null}

POST /api/v1/assessments/{id}/transitions
{"revision": 7, "action": "confirm_conversation"}
```

- `start_period`: `criteria_agreed` → `in_progress`. Tylko w tym stanie zapisujemy
  obserwacje i rozmowę. Obserwacje są dopisywane, a PUT zastępuje szkic rozmowy.
- Daty czynności od rozmowy rozpoczynającej do dzisiaj w `Europe/Warsaw`.
  Tekst obserwacji 1–10 000 znaków; każda z trzech notatek 0–10 000 znaków.
  Nie wymuszamy upływu planowanego terminu oceny bez zweryfikowanych reguł prawnych.
- Szkic rozmowy można zapisać bez daty. Potwierdzenie wymaga zapisanej daty;
  obserwacje i notatki są opcjonalne. Zmiana `in_progress` → `evaluation` blokuje
  ich dalszą edycję. Potwierdzenie nie oznacza podpisania/doręczenia.
- Autorzy i czasy są wyłącznie serwerowe. Wszystkie operacje korzystają z tej
  samej blokady oceny/przypisania, rewizji i atomowego zdarzenia co P4-02.
  Stara rewizja chroni również przed podwójnym dopisaniem obserwacji po timeout.
- GET oceny odtwarza wpisy i rozmowę, nie zmieniając stanu. Identyczne zasady
  autorstwa/przypisania obejmują odczyt oraz każdą mutację; HR/ADMIN nie czytają notatek.

## Wskaźniki i decyzje przełożonego

Migracja `0008` dodaje `criterion_ratings` i `indicator_answers`. Operacje są
dostępne wyłącznie w `evaluation`, dla prowadzącego MANAGER z aktualnym przypisaniem.

```text
PUT /api/v1/assessments/{id}/criteria/{criterion_id}/answers
{"revision": 8, "answers": [{"indicator_id": "UUID", "level": 2, "note": "Przykład"}]}

POST /api/v1/assessments/{id}/criteria/{criterion_id}/rating
{"revision": 9, "score": 7}
```

- PUT zastępuje odpowiedzi jednego wybranego kryterium. Wymaga dokładnie wszystkich
  jego wskaźników z przypiętego katalogu, każdy UUID raz. `level`: 0–4 albo `null`
  (brak obserwacji); `note`: 0–4000 znaków. Inne kryterium, wskaźnik z nowego
  katalogu, duplikaty i niepełny zestaw zwracają 422 bez częściowego zapisu.
- Backend zapisuje sugestię 1/3/5/7/9 albo `null`, wersję polityki, autora i czas UTC.
  Brak obserwacji jest pomijany, remis rozstrzyga niższa ocena. Bez odpowiedzi
  nie ma domyślnej sugestii ani zatwierdzenia.
- POST wymaga jawnego `score` 1/3/5/7/9; decyzja może różnić się od sugestii,
  również przy braku obserwacji. Zapisuje osobne `confirmed_by` i `confirmed_at`.
- Zmiana poziomu lub notatki czyści formalny wynik i potwierdzenie tylko tego
  kryterium. Identyczny zestaw (niezależnie od kolejności, po przycięciu notatek)
  zachowuje potwierdzenie. Każdy przyjęty zapis podnosi rewizję i tworzy zdarzenie.
- FK i CHECK ograniczają powiązania oraz wartości w bazie; UUID wskaźników
  sprawdza serwis wobec snapshotu JSONB. Wszystkie mutacje używają wspólnej
  blokady oceny/przypisania i atomowej transakcji. Konflikt → 409, brak dostępu → 404.
- GET odtwarza odpowiedzi, sugestie i decyzje w `ratings`. Nawigacja nie zapisuje
  danych. Wynik zbiorczy i finalizacja są opisane poniżej.

## Wynik i zakończenie oceny C

Migracja `0009` dodaje `assessment_summaries`: tekst podsumowania, autora/czas
zapisu oraz osobny niezmienny wynik i autor/czas zakończenia.

```text
GET /api/v1/assessments/{id}/result
{"outcome": "positive", "mean": "5.00"}

PUT /api/v1/assessments/{id}/summary
{"revision": 15, "negative_justification": "", "development_conclusions": "Plan rozwoju"}

POST /api/v1/assessments/{id}/transitions
{"revision": 16, "action": "complete"}
```

- Odczyt oceny zawiera ten sam `result` i zapisane `summary` (lub `null`).
  Przed kompletem zatwierdzeń wynik to `incomplete`, a średnia `null`.
  Sugestie nigdy nie zastępują formalnych decyzji. Reguła: dokładna średnia > 4
  i brak oceny 1; średnia w odpowiedzi to tekst z dwoma miejscami po przecinku.
- Podsumowanie można zapisywać w `evaluation`, także jako niepełny szkic.
  Oba teksty są przycinane i ograniczone do 10 000 znaków. Wnioski rozwojowe
  są opcjonalne; wynik negatywny wymaga niepustego zapisanego uzasadnienia.
- `complete` ponownie sprawdza ustalenia, potwierdzoną rozmowę, wszystkie wybrane
  kryteria i zapis podsumowania. Wspólna blokada/rewizja chroni przed równoległą
  zmianą odpowiedzi. Wynik, suma/liczba ocen, autor/czas, status `completed`,
  nowa rewizja i jedno zdarzenie są zapisywane atomowo.
- Ponowienie zakończenia z rewizją źródłową lub wynikową zwraca ten sam zapis
  bez nowego zdarzenia, czasu ani rewizji. Starsza/inna rewizja → 409.
  Nadal obowiązują własne autorstwo, MANAGER i aktualne przypisanie, również przy retry.
- Po zakończeniu wszystkie mutacje danych są odrzucane. Wynik odczytuje utrwaloną
  decyzję i dokładną sumę/liczbę ocen, a nie ponownie stosowaną przyszłą wersję reguł.
  To zamknięcie w aplikacji, nie podpis ani doręczenie; pliki/PDF pozostają do P5.

## Reguły ocen

`app/modules/assessments/rules.py` zawiera czyste funkcje bez API, ORM i AI:
zestawy B/C, walidację do trzech dodatkowych kryteriów z przypiętego katalogu,
wynik okresowy, sugestię behawioralną i warunki punktowe pierwszej oceny.
Średnie są dokładnymi ułamkami (`Fraction`), a nie zaokrąglonymi floatami.
Braki zwracają `incomplete`, nigdy domyślny wynik pozytywny. Do funkcji wyniku
okresowego przekazuje się tylko oceny zatwierdzone przez człowieka.

Brak obserwacji to `None`, poziomy to 0–4; sugestia ma osobną wersję polityki,
remis rozstrzyga niższa ocena. Pierwsza ocena wymaga pięciu elementów, jawnej
informacji o terminowym sprawozdaniu i egzaminie; zwolnienie wymaga podstawy.
Kwalifikacja, obliczanie terminów i wyjątki prawne zostają do P7-02 po weryfikacji
aktualnych źródeł. Sam tekst podstawy nie jest jej weryfikacją prawną.
