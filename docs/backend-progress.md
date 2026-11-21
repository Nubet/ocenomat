# Kompas Kompetencji — postęp backendu

Plan i obowiązujące decyzje: [backend-implementation-plan.md](backend-implementation-plan.md).
Ten plik opisuje faktyczny stan, nie planowane rezultaty. Aktualizacja: 2026-11-21.

## Bieżący stan

- **Etap:** 6 — kontrolowany RAG, źródła i analiza OSP.
- **Aktywne zadanie:** P6-07 — rzeczywista ewaluacja generowania (`blocked`: OpenRouter).
- **Następny krok:** po odblokowaniu providera uruchomić istniejące narzędzie
  z `--generate`, ocenić odpowiedzi i rekomendacje trzech OSP. Dopiero po zamknięciu
  fazy 6 rozpocząć P7-01. Zestaw 30 pytań i pomiar retrieval są gotowe.
  P6-02 zakończono dla ograniczonego korpusu: 4 źródła, 64 fragmenty, 17 approval
  wierności; pozostałe 47 nadal `needs_review`. Ustawa, FAQ, formularze i poradniki
  nie są zatwierdzoną wiedzą. Backend Compose healthy, migracje do 0015. Obowiązuje
  [phase6-plan.md](hacknation-materials/phase6-plan.md), nie dawny skrót trzech zadań.
- **Ostatnia zakończona praca:** implementacja analizy OSP (`9f4311c`) i narzędzie
  ewaluacji P6-07: 30 pytań, 23/23 trafienia źródeł top-5 bez generowania.
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
   W `evaluation` zapisujemy odpowiedzi wskaźników z przypiętego katalogu oraz
   sugestię backendu; przełożony osobno wybiera i zatwierdza każdą ocenę cząstkową.
   Zmiana poziomu lub notatki wymaga ponowienia decyzji dla tego kryterium.
   Wynik API pozostaje niekompletny do zatwierdzenia wszystkich kryteriów. Osobny
   zapis podsumowania i polecenie `complete` zamykają proces w `completed`;
   wynik, autor/czas i dane są odtąd niezmienne. Finalizacja nie oznacza podpisu/doręczenia.
  Frontend ma ekran logowania, cookie session i chroniony workspace; monitoring
   pozostaje do podłączenia w P7. Bez Supabase
  dostępny jest ekran logowania z jawną informacją o braku konfiguracji.
  RustFS przechowuje prywatne pliki oceny; API sprawdza dostęp, format i checksum.
   UI obsługuje załączniki, wybór wersji OSP i generowanie PDF zakończonej oceny C.
  Konfigurację Supabase Auth wpisano lokalnie; publiczny JWKS potwierdza ES256.
  Użytkownik potwierdził logowanie; live HTTP potwierdził JWT, autoryzację API,
  SSR, odświeżenie cookie przez proxy i wylogowanie Server Action.
   Adapter OpenRouter jest podłączony przez lifecycle; API asystenta i bezpieczne
   pobieranie źródeł są zaimplementowane. Drawer korzysta z API, bez fallbacku demo.
   Żywe generowanie zablokowane kontem OpenRouter. VPS niezintegrowany.
- **Kontrole P5-02:** końcowy `npm run precommit` — OK, 170 testów Vitest;
  wcześniejszy `npm run build` — OK. Końcowe testy dokumentów i migracji:
  37 passed w 9,17 s; Ruff lint/format OK. Wcześniej pełny backend: 371 passed
  oraz live RustFS/Supabase/HTTP/SSR. Po ostatnich zmianach nie powtarzano pełnej
  regresji, builda ani smoke; szczegóły niżej.
- **Środowisko lokalne:** Compose korzysta z ignorowanego `.env.compose-check`;
  frontend na życzenie użytkownika przeniesiono na `http://localhost:3000`,
  pozostałe porty testowe jak w P1-03. Oddzielny `kompas-postgres-test` jest
  uruchomiony (port 55439), używany wyłącznie do testów, nie jako baza aplikacji.
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
| P4-04 | Wskaźniki i decyzje | done | Migracja 0008, trwałe odpowiedzi/notatki, wersjonowana sugestia i ręczne zatwierdzenie; izolowane unieważnianie decyzji, rewizje i UI. 243 testy backendu, 143 UI, build i live HTTP/SSR OK. |
| P4-05 | Wynik i zakończenie | done | Migracja 0009, wynik API, trwałe podsumowanie, idempotentne zakończenie i blokada edycji; 270 testów backendu, 157 UI, build i live HTTP/SSR OK. |
| P5-01 | Prywatny storage | done | Migracja 0010, prywatny bucket, autoryzowane API, walidacja, rewizje i kompensacja/niepewny COMMIT; 351 testów backendu, 157 UI, build i live RustFS/HTTP OK. |
| P5-02 | OSP i PDF C | done | Migracje 0011–0012, wersje OSP pracownika, wybór w draft, PDF zakończonej oceny i UI pobrania; końcowe 37 testów backendu, 170 UI, wcześniejszy build/live HTTP OK. |
| P6-01 | Wymienialny provider LLM | done | Kontrakt, adapter, Settings/Compose i dependency injection; 63 celowane testy OK w 0,58 s. `feat(ai): add configurable llm provider` |
| P6-02 | Inwentaryzacja, ekstrakcja i weryfikacja oryginałów | done | Ograniczony korpus 4 źródeł/64 fragmentów w PostgreSQL i prywatnym RustFS, 17 indywidualnych approval, 47 needs_review. Hashy/ID/danych chronionych nie zmieniono; retry bez PUT i mutacji. Pełny audyt 16 źródeł lokalnie, reszta niezatwierdzona. |
| P6-03 | Wyszukiwanie wiedzy PostgreSQL | done | `79fa4ce`; FTS/simple, GIN 0015, filtry, deduplikacja i atomowy kontekst. 104 testy OK; live top-5 9/9, trzy odmowy, brak zmian danych. Backend healthy. |
| P6-04 | Asystent formalny RAG i cytowania | done | Autoryzowane API, dosłowne cytaty i osobny review poparcia/kompletności; testy asystenta OK. Wynik przez silnik, brak mutacji; rzeczywiste generowanie zablokowane kontem OpenRouter. |
| P6-05 | Integracja istniejącego draweru Next.js | done | Sesyjna Server Action, OpenAPI, jawne tryby/zakres, wynik silnika i chronione pobranie oryginału; precommit i 180 testów OK. Przeglądarka niewykonana. |
| P6-06 | Analiza OSP i rekomendacje kryteriów | blocked | Kod/API/UI i testy gotowe; 58 testów OSP+asystenta OK, w tym ekstrakcja trzech oryginałów. Do kryterium jakości rekomendacji trzech OSP potrzebne działające generowanie. |
| P6-07 | Ewaluacja jakości i demonstracja | blocked | Zestaw 30 pytań, narzędzie read-only i protokół przeglądu gotowe; retrieval 23/23 top-5. Jakość generowania i demonstracja wymagają odblokowania OpenRouter. |
| P7-01 | Arkusz B | pending | — |
| P7-02 | Pierwsza ocena | pending | — |
| P7-03 | Monitoring HR | pending | — |
| P8-01 | Test krytycznej ścieżki E2E | blocked | Poprzednie polecenie zabrania uruchamiania przeglądarki; potrzebna zmiana instrukcji. |
| P8-02 | Konfiguracja i deployment VPS | pending | Faktyczne wdrożenie wymaga dostępu do serwera i domeny. |

## Ograniczenia i zależności zewnętrzne

- Integracja auth wymaga skonfigurowanego projektu Supabase Cloud z kluczami
  asymetrycznymi i rzeczywistych danych konfiguracyjnych; nie zapisuj sekretów tutaj.
- Żywe testy AI wymagają klucza OpenRouter. Użytkownik zmienił ograniczenie
  darmowego modelu: płatny model jest dozwolony, priorytet skuteczność → czas → cena.
  Ustawiono Sonnet 5.5, bez automatycznej zmiany modelu. Nie deklarujemy zgodności
  tego wyboru z wcześniejszym ograniczeniem konkursowym bez jego wyjaśnienia.
- Klucz dodany lokalnie przez użytkownika: OpenRouter `/auth/key` → 200,
  ale `chat/completions` → 401 `User not found.` (tekst i JSON Schema).
  Brak udanego generowania; bloker konta/dostawcy, bez obchodzenia polityk.
- ELI potwierdza obowiązywanie rozporządzeń 2016/470 i 2015/1144 (2026-11-21).
  Ustawa jest już dostępna w oficjalnych pobraniach (tekst jednolity 2026/590),
  załącznik został wydzielony; kontrola czasowego stosowania jednostek jest nadal
  wymagana przed zatwierdzeniem ich jako aktualnej podstawy odpowiedzi.
  Pełna zgodność formalna i wszystkie interpretacje poradników nie są zatwierdzone.
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

### 2026-11-21 — P6-03, wyszukiwanie zatwierdzonego korpusu

- Dodano kontrakt `KnowledgeRetriever`, modele zapytania/wyniku oraz implementację
  PostgreSQL FTS. `simple` + translacja polskich znaków/prefiksy, bez nowych
  zależności ani bazy wektorowej; oryginalna treść pozostaje niezmieniona.
- `0015` dodaje współbieżny indeks GIN wyrażenia; test potwierdza jego używalność.
  Migracje upgrade/retry/check i roundtrip w oddzielnym schemacie testowym OK.
- Filtry approval/aktualności/rodzaju oceny/typu źródła i przeznaczenia wykluczają
  OSP i kopie walidacyjne. Sprawdzane są hash treści i oficjalne provenance;
  częściowe approval nie zatwierdza całego źródła.
- Deduplikacja canonical ID preferuje HTML z całymi paragrafami. Zależności
  `required_context` są przechodnie i ograniczone do źródła. Cykle obsługiwane;
  brak approval, przyszłe/niezweryfikowane warianty lub przekroczenie limitu
  pomijają cały kontekst. PDF bez struktury wymaga całego zatwierdzonego dokumentu
  mieszczącego się w limitach. Nie ma arbitralnego odcinania stron/wyjątków.
- Celowana regresja wiedzy/CLI/ekstrakcji/importu/migracji: **104 passed,
  20,65 s, bez skipów**; Ruff lint/format OK. Dziewięć pytań na oryginałach ma
  właściwy paragraf w top-5; to nie pełna ewaluacja P6-07. Znane ostrzeżenie
  deprecjacji Starlette/httpx, bez wpływu na wynik.
- Commit `79fa4ce`. `0015` wdrożona do aplikacji, upgrade head powtórzony,
  `alembic check` bez nowych operacji. Indeks `indisvalid=true`. Faktyczna instancja
  udostępnia `simple`, nie ma `polish`; wybrana konfiguracja jest dostępna.
- Rzeczywisty smoke na zaimportowanym korpusie: **9/9** pytań ze spodziewanym
  paragrafem w top-5, prawidłowy rodzaj oceny i wyłącznie reprezentacja HTML.
  Trzy przypadki bez podstaw (`§999`, `art.81`, podróże międzygalaktyczne) bez
  wyników. Cały smoke 0,066 s lokalnie; nie jest to benchmark obciążeniowy.
- Migawki wszystkich rekordów wiedzy i czterech tabel aplikacyjnych identyczne
  przed/po migracji i smoke. Żadnej zmiany treści, ID, approval ani dat rekordów.
- Odbudowano backend/migrate/storage-init przez Compose `up --build -d backend`,
  bez resetu danych. Obraz zawiera aktualne zasoby (16 źródeł). Retriever wywołany
  również wewnątrz kontenera wskazuje §5 dla pytania o kryteria dodatkowe.
  `/api/v1/health` 200, kontener healthy. Końcowy Ruff lint/format i `uv lock --check` OK.
- P6-03 done dla ograniczonego korpusu. P6-04 pending: wynik `matched` nie jest
  jeszcze odpowiedzią ani dowodem poparcia dowolnego twierdzenia. Błąd konta
  OpenRouter pozostaje nierozwiązany; nie wykonywano nowego generowania ani E2E.

## P6-04 — autoryzowany asystent i walidacja cytowań

- `POST /api/v1/ai/assistant`: jawny tryb formal/conversation, rodzaj oceny,
  opcjonalny assessment_id i zadanie assessment_result. Klient nie przekazuje
  pracownika, ról ani danych oceny. Kontekst odczytuje dotychczasowa autoryzacja,
  również po generowaniu; obcy manager/HR/admin bez przypisania otrzymują 404.
- Brak podstaw kończy się bez wywołania LLM. Przy opisowej odpowiedzi są dwa
  wywołania tego samego skonfigurowanego providera: generowanie i osobny prompt
  recenzenta poparcia całej odpowiedzi, warunków, wyjątków oraz konfliktów.
  To kontrola semantyczna LLM, nie deterministyczny dowód prawdziwości.
- Cytaty muszą występować w przekazanej treści; ID, hash, status, locator i
  ponownie pobrane metadane muszą się zgadzać. Odpowiedź zostaje odrzucona przy
  zmianie approval, braku poparcia któregokolwiek twierdzenia albo niepełnym
  rozwiązaniu pytania. Nie pokazujemy odrzuconej treści ani swobodnych uzasadnień
  modelu. Publiczne metadane pochodzą z bazy, nie z wygenerowanych URL/stron.
- Wynik konkretnej oceny pochodzi z `Assessment.result` i istniejących reguł,
  bez LLM. Wysyłka formalnego pytania nie przekazuje nazwiska, notatek ani OSP.
  Nie zapisujemy historii ani nie zmieniamy ocen. Cache-Control private/no-store.
- `GET /api/v1/knowledge/sources/{source_id}/original`: tylko zalogowany użytkownik
  i wspólne źródło kontekstowe z aktualną provenance oraz approved fragmentem.
  Prywatne OSP i inne niedozwolone typy odrzucane przed storage. Checksum oryginału
  sprawdzana; attachment, nosniff i CSP sandbox chronią także źródłowy HTML.
- Błędy providera to osobne kody HTTP: 429/502/503/504, nie brak wiedzy.
- Kontrole: Ruff całego app/tests OK. Pierwszy pełny pytest: 562 passed, 1 skipped,
  7 failures wyłącznie w istniejącym generowaniu PDF — host nie ma domyślnego
  DejaVu (obraz Compose go ma). Po jawnym ustawieniu istniejącego hostowego fontu
  `KOMPAS_PDF_FONT_PATH=/usr/share/fonts/open-sans/OpenSans-Regular.ttf` powtórzono
  testy dokumentów i asystenta: **67 passed, 10,53 s**. Brak zmiany kodu PDF.
  Celowane retriever+asystent: wszystkie 69 asercyjnych przypadków OK; poprawiono
  testowy teardown savepoint przy symulacji cofnięcia approval, potem asystent OK.
- Żywa jakość generowania i pełna ewaluacja nadal niewykonane: wcześniejszy bloker
  OpenRouter 401. Testy używają jawnych atrap providera, nie fallbacku produkcyjnego.

## P6-05 — podłączenie draweru

- Usunięto hardcoded `assistantReply`, fikcyjnego domyślnego pracownika oraz blokadę
  draweru na zapisanych ocenach. Zostały wyłącznie propozycje pytań, nie odpowiedzi.
- Server Action korzysta z istniejącego sesyjnego `apiRequest`; jawne pola requestu,
  wygenerowane z OpenAPI typy, timeout 130 s dla dwóch przejść LLM po maks. 60 s.
  Transport zachowuje jawny sygnał serwera, domyślne 8 s pozostałych requestów bez zmian.
- Tryb formal/conversation i zakres first/periodic; assessment_id wyłącznie z UUID
  prawdziwej trasy. Zakres i dostęp do konkretnej oceny ponownie sprawdza API.
  Przycisk sprawdzenia zapisanego wyniku nie uruchamia modelu.
- Oczekiwanie blokuje powtórzenie zapytania/zmianę trybu; błąd zachowuje pytanie,
  oddzielne komunikaty timeoutu, limitu, awarii i braku podstaw. Cytaty, locator,
  datowana aktualność i link do oryginału. Bez renderowania Markdown/HTML modelu.
- Pobranie przez sesyjny Route Handler, attachment/nosniff/CSP sandbox/no-store.
  Czat tylko w pamięci panelu, znika przy zamknięciu lub zmianie trasy; brak retencji.
- `npm run precommit`: format/lint/typecheck i **180 testów w 25 plikach OK**.
  Testy akcji obejmują kody błędów, brak ujawnienia szczegółów dostawcy, redirect
  sesji, input i timeout; helper kontekstu odrzuca demo ID i trasę nowej oceny.
- Nie wykonywano przeglądarki ani rzeczywistego generowania; P6-07 nadal wymaga
  odblokowania providera i pomiarów jakości. UI nie udaje powodzenia przy awarii.

## P6-07 — zestaw referencyjny i narzędzie ewaluacji

- 30 pytań z oczekiwanymi odpowiedziami: 23 z locatorami oryginalnych paragrafów,
  7 o brakach podstaw, niejednoznaczności, fikcyjnych źródłach i injection.
- `uv run python -m app.modules.ai.evaluate`: publiczny korpus, transakcja read-only,
  JSON z oddzielnym retrieval i generowaniem. Opcjonalne `--generate` korzysta
  z obecnego adaptera, bez retry po awarii. Nie przesyła prywatnych ocen/OSP.
- Jednorazowy pomiar na aplikacyjnym PostgreSQL: **23/23 top-5**, suma czasu
  retrieval **0,1575 s**. Bez wywołań LLM; nie jest to pomiar jakości odpowiedzi.
- Kontrole: Ruff lint/format dwóch nowych plików OK;
  `uv run pytest -q tests/test_assistant_evaluation.py` — **1 passed, 0,67 s**.
  Bez powtarzania pełnej regresji, smoke ani przeglądarki. Nowa dyrektywa użytkownika:
  priorytet implementacji i clean code, tylko potrzebne celowane kontrole.
- Protokół przeglądu, komendy i ograniczenia: [assistant-evaluation.md](assistant-evaluation.md).
  P6-07 nadal **blocked** przez provider; nie oznaczamy fazy 6 jako ukończonej.
  Następny krok: rzeczywiste odpowiedzi i trzy OSP po odblokowaniu OpenRouter,
  następnie P7-01. Commit: `feat(ai): add reference corpus evaluation tool`.

## P6-06 — implementacja analizy prywatnego OSP

- `POST /api/v1/ai/assessments/{id}/job-description-analysis` pobiera wyłącznie
  wybraną w ocenie wersję `JobDescription`, po dotychczasowej autoryzacji. Odczyt
  storage sprawdza checksum. Ponowna kontrola przypisania/rewizji/wyboru OSP przed
  każdym wywołaniem modelu i po nim; cofnięcie dostępu 404, zmiana kontekstu 409.
- Reuse ekstraktora DOCX/PDF; zachowane nagłówki, tabele, negacje i locatory,
  deterministyczne ID fragmentów zależne od dokumentu/wersji ekstraktora/treści.
  Nie ma fikcyjnych stron DOCX, wspólnego indeksowania prywatnych OSP ani nowej
  tabeli. Unsupported/scan/pusty lub zbyt duży kontekst odmawia bez obcinania.
- Obowiązkowe kryteria i walidacja dodatkowych przez istniejące `periodic_criteria`
  i przypięty katalog. Pydantic: maks. 3; odrzucane duplikaty, obowiązkowe i obce ID,
  nieistniejące fragmenty i niedosłowne cytaty. Osobny review sprawdza rzeczywisty
  związek obowiązku z kryterium i wyklucza ocenianie osoby. Nie zmieniamy oceny.
- Panel na istniejącym kroku analizy pokazuje rekomendacje, uzasadnienia, cytaty,
  locatory i pobranie oryginału. Nie wybiera ani nie zapisuje kryteriów; przełożony
  robi to istniejącymi checkboxami i zapisem. Stan analizy resetowany przy zmianie
  wersji/rewizji. Bez OSP przycisk nieaktywny, brak usługi nie daje mocków.
- Testy OSP+asystenta: **58 passed, 4,23 s**, w tym autoryzacja przed storage/LLM,
  cofnięcie przypisania między wywołaniami, zmiana rewizji, brak OSP, fałszywe ID,
  quote/required/duplicate, brak mutacji i ekstrakcja trzech oryginalnych OSP.
  Te ostatnie testują wierność struktury/stabilność ID, nie realną jakość modelu.
- Frontend: `npm run precommit` **188 testów / 26 plików OK**, `npm run build` OK.
  Backend: Ruff całego app/tests i lockfile OK.
- Jedna próba rzeczywistej odpowiedzi na publicznym korpusie przez istniejącego
  providera kończy się kontrolowanym `LLMError(unavailable)`. Nie ujawniano body
  błędu ani sekretów, nie zmieniano routingu/modelu/polityki danych. Wcześniej
  zidentyfikowany problem konta 401 nie ma potwierdzonego rozwiązania.
- P6-06 **blocked**, choć kod i testy implementacyjne gotowe: nie wykonano
  rzeczywistego generowania i merytorycznej oceny rekomendacji trzech OSP.
  Niezależnie przygotowujemy ewaluację P6-07; nie deklarujemy ukończenia fazy 6.

### 2026-11-21 — P6-02, zapis zmian i selektywny import CLI

- Dotychczasowe zmiany zapisano: `ec1091a` (ekstrakcja/provenance), `cb17381`
  (częściowe decyzje), `de3c406` (etykiety demo), `ac9ec1c` (audyt i ograniczenia).
- Ponowna kontrola przed commitami: 70 testów backendu z oryginałami i oddzielnym
  PostgreSQL, 19,37 s; Ruff lint/format OK. `npm run precommit` OK: format,
  lint, typecheck i 170 testów UI. Bez przeglądarki.
- CLI otrzymał powtarzalne `--source`: jawny wybór źródeł, walidacja nieznanych
  ID i kompletu rodziców przed bazą/storage. Kolejność rodzic → dziecko, bez
  automatycznego importu pozostałych dokumentów. Trzy testy CLI OK (0,41 s).
- `fe5f611`: selektywny CLI; `5741157`: 10 decyzji wierności pełnych paragrafów
  ELI HTML (okresowa §§2–5,11; pierwsza §§2,3,6,9,10), z osobnymi uzasadnieniami
  i hashami. Zachowano siedem decyzji PDF. To nie niezależna opinia prawna.
- Testy po zmianach: CLI/reviews/importer/ekstrakcja oficjalna **37 passed,
  9,36 s**; Ruff lint OK, końcowy format OK. Po korekcie formatu testy reviews/CLI
  **5 passed, 2,26 s**. Znane ostrzeżenie Starlette/httpx bez zmiany zależności.
- Rzeczywisty CLI uruchomiony z hosta uv, z konfiguracją kontenera przekazaną
  wyłącznie w pamięci i lokalnymi portami DB/RustFS. Wybrano dwa PDF i dwie
  reprezentacje HTML, bez importu reszty manifestu. **4 źródła / 64 fragmenty**,
  **17 approved / 47 needs_review**; całe źródła nadal needs_review.
- Pierwszy import zapisał cztery obiekty. Kontrola powtórzeń: **0 PUT**, identyczne
  rekordy źródeł/fragmentów (ID, review, daty), klucze/ETag/rozmiary. Checksum
  wszystkich czterech oryginałów i istniejącego dokumentu zgodne z DB.
  Pełne migawki `catalog_versions`, `documents`, `job_descriptions`, `assessments`
  bez zmian; obiekty spoza `knowledge/` również bez zmian.
- Lokalny skrypt kontrolny po udanym imporcie miał błąd serializacji SQLAlchemy Row
  w końcowym wydruku; poprawiono wyłącznie wydruk i powtórzono całą weryfikację.
  Nie powtórzono PUT ani nie resetowano danych. P6-02 done dla jawnie ograniczonego
  korpusu, zgodnie z zakresem MVP planu. Kolejny krok: P6-03.

### 2026-11-21 — P6-02, kontrolowana ekstrakcja ELI/FAQ i ustawy

- Dodano jawne profile `eli-html-v1`, `kprm-faq-v1`, `statute-2026-590-v1`
  w istniejącym ekstraktorze, audycie i importerze. `lxml` był zależnością
  przechodnią python-docx; zadeklarowano go bezpośrednio i uaktualniono lockfile.
  Brak nowego magazynu, migracji czy systemu RAG.
- Manifest rozszerzono 12 → 16 źródeł, zachowując wcześniejsze ID/locatory/reviews.
  ELI HTML: odpowiednio 19 i 18 fragmentów, komplet §§1–14, nieodrywane warunki
  i przypisy. Załączniki zawierające tylko link do PDF mają jawny brak treści.
- FAQ: 31 kompletnych Q&A, rzeczywiste XPath, przypisy i oryginalne zastrzeżenie
  opinii w każdym fragmencie; bez menu/skryptów i dostępu do sieci z parsera.
- Ustawa: 218 fragmentów; obwieszczenie s.1–2 oddzielone od załącznika s.3–39,
  zachowane wszystkie 41 przypisów, równoległe brzmienia i pominięty zakres
  art.132–190. Dalej są zależności `required_context` dla kontynuacji/wariantów
  i warunków publikacji. Przyszłe i zależne od zdarzenia brzmienia nie są
  automatycznie wybierane; ustawa pozostaje `legal_status=unknown`.
- Kontrole: `uv lock`; Ruff lint/format OK; pytest dla `test_official_extraction`,
  `test_knowledge_{extraction,ingestion,provenance,sources}` i `test_database`
  z oryginałami oraz oddzielnym PostgreSQL **70 passed, 17,50 s, bez skipów**.
  Ostrzeżenie deprecjacji Starlette/httpx, bez wpływu na wynik. Testy sprawdzają
  też brak utraty tekstu PDF, właściwe rozdzielenie art.35, pełny art.81 s.24–25,
  warunki przyszłej zmiany z przypisu28, XPath i ponowienie importu HTML.
- Rzeczywisty `uv run python -m app.modules.knowledge.audit` z manifestem pobrań
  wykonany dla wszystkich 16 źródeł. Raport lokalny:
  `/tmp/opencode/official-source-extraction-audit.json`; wynik opisany w
  [official-sources-audit.md, §9](official-sources-audit.md#9-kontrolowana-ekstrakcja-eli-faq-i-ustawy).
- Nowe fragmenty mają `needs_review`. Nie uruchamiano importu do bazy/RustFS
  aplikacji, generowania LLM ani przeglądarki. P6-02 nadal `in_progress`;
  następna czynność: review przypięty do hashy i kontrolowany import/retry,
  po nim dopiero P6-03 z obsługą zależności i rozróżnieniem dat/typów źródła.

### 2026-11-21 — P6-02, audyt oficjalnych źródeł przed dalszą rozbudową

- Na polecenie użytkownika wstrzymano nowe funkcje; sprawdzono kod, plan,
  migracje oraz rzeczywiste PostgreSQL/RustFS. Stan wyjściowy: DB 0012, brak tabel
  wiedzy i indeksu, jeden prywatny OSP w storage, istniejący katalog 14 kryteriów.
- Rekurencyjna inwentaryzacja 55 plików, w tym 25 oficjalnych pobrań i historical.
  Wszystkie rozmiary/SHA zgodne. Siedem grup kopii bajtowych, identyczne treści
  19 stron PDF okresowego ELI/KPRM i wykaz równy stronom 5–7 pełnego PDF.
- Online ELI/Sejm: dwa rozporządzenia obowiązują; trzy dawne są uchylone.
  Ustawa 2026/590 już istnieje; obwieszczenie i przyszłe/przejściowe brzmienia
  nie mogą być potraktowane jak jeden bezwarunkowo aktualny fragment ustawy.
- Pochodzenie SHA/URL, canonical ID, role i alternatywne formaty w istniejącym
  manifeście, zachowane ID/oryginały; nullable JSONB 0014 bez backfillu. Importer
  odrzuca hash niezgodny z pochodzeniem. Markdown pozostaje pomocniczy.
- UI ma ręczne odwołania demo, nie cytowania RAG; poprawiono mylący opis. Brak
  retrievera/chatu/walidatora cytowań jest jawny, nie zastąpiony nowym demo.
- Testy pięciu dotkniętych modułów backendu z dedykowaną bazą i oryginałami:
  **61 passed, 9,41 s**. Po poprawce serializacji dat w CLI provenance:
  **9 passed, 5,37 s** i rzeczywisty audyt CLI OK; Ruff lint/format OK.
  Frontend oxlint OK, celowane testy asystenta **2 passed**, format TSX OK.
- Końcowe testy provenance i zapisanych decyzji po kontroli hashy kopii:
  **11 passed, 6,95 s**, Ruff OK. Self-check raportu: wszystkie 55 ścieżek/SHA zgodne.
- Raport trwały: [official-sources-audit.md](official-sources-audit.md), zawiera
  każdą ścieżkę/SHA/rolę, źródła ustaleń prawnych, luki i kolejność dalszych prac.
  Dane i obiekty aplikacji pozostawiono bez zmian podczas audytu.
- Dodatkowa diagnoza timeoutu API: log worker Uvicorn wskazuje
  `ModuleNotFoundError: No module named 'httpx'`. Kod P6-01 był montowany do
  starego obrazu bez nowej zależności runtime. **Po audycie kontynuowano P6-02:**
  celowy Compose `up --build -d backend`, bez resetu wolumenów. Migracje
  **0012 → 0013 → 0014**, `/api/v1/health` **200**, `alembic check` OK,
  powtórny upgrade head bez nowych operacji, backend **healthy**.
- Odczyt po wdrożeniu: **0 źródeł / 0 fragmentów**, katalog z tym samym ID/SHA,
  nadal jeden dokument i OSP. RustFS jeden obiekt, zero `knowledge/`; klucze
  zgodne z DB, checksum istniejącego pliku zgodny. Bez importu lub PUT/DELETE.
- Dokładna kontynuacja: ekstrakcja ELI HTML/FAQ i ustawy, hash-bound review,
  dopiero ograniczony import i retry. P6-03 nadal pending, nie nowy system RAG.

### 2026-11-21 — P6-02, manifest i niezależna ekstrakcja

- Manifest 12 oryginałów i 11 jawnych powiązań z pomocniczym Markdown.
  Na polecenie użytkownika zadanie/regulamin konkursu i diagram produktu są
  wyłączone z korpusu aplikacji. ZIP nie jest powielony; wykaz ma parent rozporządzenia.
- pypdf pozostaje jedynym parserem PDF (strony/layout); python-docx 1.2 dodany
  do DOCX (kolejność, zagnieżdżone tabele, deduplikacja scaleń, checkboxy,
  symbole i przypisy). Nieodtworzona numeracja i złożone struktury są oznaczane
  do kontroli. XLSX wykorzystuje istniejący importer i jego UUID, z komórkami.
- CLI `app.modules.knowledge.audit` tworzy raport SHA/stron/lokalizacji,
  ostrzeżeń i rozbieżności słów po normalizacji białych znaków. Nie zatwierdza
  nawet identycznej reprezentacji. Liczby, negacje i nierówności pozostają.
- Audyt uruchomiono na wszystkich 12 dostarczonych oryginałach; pełny raport
  lokalnie `/tmp/opencode/knowledge-audit.json`, poza Gitem. Różnice obejmują
  formatowanie Markdown, układ tabel i sklejenia tekstu PDF; similarity nie
  jest miarą zgodności merytorycznej. Brak automatycznego approval.
- Kontrole pierwszej części: Ruff OK; `uv run pytest -q
  tests/test_knowledge_extraction.py tests/test_catalog.py` — 25 passed,
  2 skipped (brak testowej bazy/XLSX w tej komendzie), 0,98 s, w tym
  test niezmiennego bufora XLSX.
- Realny provider: klucz rozpoznany, generowanie odrzucone 401 `User not found.`;
  żadnych sekretów/prompts prywatnych w artefaktach. Nie zmieniano modelu.
- Commit pierwszej części: `feat(knowledge): audit original source extraction`.
- P6-02 nadal in_progress: następne są migracja/import, jawny przegląd fragmentów
  i testy PostgreSQL/RustFS. Nie rozpoczęto chatu ani retrievera.

### 2026-11-21 — P6-02, trwały import i decyzje o fragmentach

- Migracja `0013`: źródła i fragmenty z FK, hashami, lokalizacją, osobnym statusem
  treści/aktualności i decyzją recenzenta. Bez backfillu wcześniejszych danych.
  Downgrade chroni istniejący korpus. Rejestracja modeli w Alembic.
- CLI importuje oryginał do prywatnego RustFS i fragmenty w transakcji PostgreSQL.
  Blokada źródła, stałe ID fragmentów, walidacja oryginału/ekstrakcji/metadanych
  przy ponowieniu. Zmiana wersji wymaga nowego source_id, bez nadpisywania cytowań.
- Jawny plik decyzji wiąże approval z hashem oryginału, ekstraktorem, lokalizatorem
  i hashem fragmentu. Zatwierdzenie części nie zatwierdza całego źródła.
  Ponowienie bez decyzji nie cofa zatwierdzeń; stare/sprzeczne decyzje są odrzucane.
- Osobny losowy klucz każdej próby i kompensacja; niepewny COMMIT zachowuje
  zatwierdzony/niemożliwy do rozstrzygnięcia obiekt. Logi naprawy zawierają tylko klucz.
- Kontrole z dedykowaną bazą PostgreSQL i rzeczywistym XLSX: pytest dla
  `test_knowledge_ingestion.py`, `test_knowledge_extraction.py`, `test_catalog.py`
  i `test_database.py` — **53 passed w 2,49 s**, bez skipów. Upgrade/check i
  roundtrip w izolowanym schemacie OK; równoległe importy, błędy PUT/flush/COMMIT,
  częściowe approval, checksum i cofanie decyzji OK. Końcowe celowane testy
  `tests/test_knowledge_ingestion.py` — **21 passed w 1,16 s**: dodatkowo
  uszkodzony tekst, constraint approval i odświeżenie starego identity map po
  blokadzie. Ruff check/format zmienionych plików OK.
- Commit drugiej części: `feat(knowledge): persist reviewed source documents`.
- Następne w P6-02: zapisać przegląd wybranych stron oryginałów, odbudować API
  z zależnościami i wykonać rzeczywisty, powtórny import do Compose/RustFS.

### 2026-11-21 — P6-01, wymienialny provider LLM

- `LLMProvider` i typowane komunikaty są niezależne od dostawcy. Jeden adapter
  HTTPX: tekst i odpowiedzi Pydantic, lokalna walidacja, ograniczenie kontekstu,
  tokenów i bajtów odpowiedzi; kontrolowane błędy, bez automatycznych retry.
- Lifecycle tworzy/zamyka klienta, zależność FastAPI zwraca 503 bez konfiguracji
  i może być zastąpiona atrapą. Nie dodano przedwcześnie endpointu chatu.
- Pydantic Settings (`KOMPAS_LLM_*`), `.env.example` i Compose, klucz `SecretStr`
  wyłącznie po stronie backendu. HTTPX przeniesiony z dev do runtime, lock odświeżony.
- Po pierwszej wersji użytkownik zmienił wymóg darmowego modelu i poprosił o
  skuteczność przed czasem i ceną. Domyślnie `anthropic/claude-sonnet-5.5`,
  limit wyjścia **8192** (obejmuje reasoning), reasoning **medium**, timeout 60 s.
  Publiczne metadane OpenRouter potwierdziły aktywne endpointy i parametry
  `max_tokens/reasoning/response_format/structured_outputs`, ceny $2/$10 za milion
  tokenów wejścia/wyjścia. Sprawdzono też alternatywy GPT-5.4 i Gemini 3.5 Flash;
  wybór Sonnet to rekomendacja, nie pomiar skuteczności/opóźnień na naszym korpusie.
  Adapter weryfikuje możliwości przy pierwszym użyciu; routing latency pozwala
  zmienić dostawcę tego samego modelu, bez automatycznej zmiany modelu. Polityka
  `data_collection=deny` blokuje trening na danych, nie gwarantuje zerowej retencji.
- Kontrole: `uv lock`, Ruff check/format zmienionych plików — OK;
  `uv run pytest -q tests/test_llm.py tests/test_health.py` — **63 passed w 0,58 s**,
  znane ostrzeżenie Starlette/httpx. Testy obejmują tekst/JSON Schema, atrapę,
  lifecycle, niedostępny model, timeout/sieć/429, błędne i ucięte odpowiedzi,
  limity i brak promptów/sekretów w błędach/logach. Brak zewnętrznych generowań.
  `docker compose --env-file .env.compose-check -f infra/compose.yaml -f infra/compose.dev.yaml config --quiet`
  — OK, bez wypisywania sekretów i bez rebuilda/smoke.
- Dokumentacja: Context7 OpenRouter i HTTPX, publiczny endpoint modelu. Nie
  mierzono jeszcze jakości modelu ani skuteczności źródeł — to P6-07.
- Commit: `feat(ai): add configurable llm provider`.

### 2026-11-21 — plan etapu 6

- Specyfikacja użytkownika znajduje się w `docs/hacknation-materials/phase6-plan.md`.
  Przeczytano plan, progres i rzeczywiste integracje/config/lifecycle backendu.
  Etap 6, DEC-011 i sekcja 8 są uzgodnione z kolejnością P6-01–P6-07.
- Pracujemy małymi, zweryfikowanymi częściami i commitujemy po ich powodzeniu.
  Celowane testy pozostają domyślne; bez ponawiania pełnej regresji/smoke.
- Kontrola dokumentacji: `git diff --check` — OK. Commit:
  `docs: define evidence-first phase six workflow`.

### 2026-11-21 — P5-02, wersje OSP i PDF arkusza C

- Poprzednią fazę zapisano jako `17e3144 feat(documents): store private assessment files`.
- Migracje `0011`–`0012`: OSP należy do pracownika niezależnie od procesu,
  wersje numerowane pod blokadą pracownika; ocena przypina wersję wyłącznie
  w `draft`. Nowszy plik nie zmienia historycznego wyboru. Import operatora
  nie tworzy oceny i rozpoznaje ponowienie ostatniego identycznego źródła.
  Downgrade chroni metadane istniejących nowych rodzajów dokumentów.
- Przykładowy `OSP DSI WWI 5 radca.docx` zaimportowano dla fikcyjnego Jana
  jako wersję 1; ponowienie zwróciło tę samą wersję. Źródło zachowano w RustFS.
- PDF z części I–II dostarczonego wzoru C zawiera zatwierdzone dane i utrwalony
  wynik; jawnie uzupełnia się brakujące dane urzędu/oceniającego, datę końca
  okresu i status zatrudnienia. Brak wniosku o kolejny stopień wymaga deklaracji.
  Podpisy i doręczenie pozostają niewypełnione. Wersja szablonu i hash źródła
  są utrwalone, a dane generowania nie trafiają do publicznych metadanych.
- Generowanie pod wspólną blokadą/transakcją nie zmienia rewizji, zdarzeń ani
  stanu zakończonej oceny. Identyczne ponowienie zwraca istniejący artefakt,
  inne dane dają 409. Błędy storage/bazy korzystają z kompensacji P5-01.
- UI: wersje OSP w kontekście stanowiska, zakładka „Dokumenty i PDF”, załączniki,
  uzupełnienia do PDF i sesyjny streaming download. Aktualizowane są rewizja,
  lista plików i wersji; konflikt/niepewna odpowiedź blokuje ślepe ponowienie.
  Kontrakt OpenAPI odświeżono; limit Server Action wynosi 11 MiB dla pliku 10 MiB.
- Font Unicode jest osadzany w PDF. Docker instaluje DejaVu Sans obsługujący
  polskie litery; lokalne testy korzystają z Liberation Sans z polskimi glifami.
  Sprawdzono tekst „Zażółć gęślą jaźń”, mapę Unicode, długie uzasadnienia,
  escaping oraz odrzucenie znaków nieobsługiwanych zamiast cichej utraty tekstu.
- Kontrole końcowe:
  - `uv run ruff check app tests alembic` oraz
    `uv run ruff format --check app tests alembic` — OK.
  - Z `KOMPAS_PDF_FONT_PATH`, osobnym `KOMPAS_TEST_DATABASE_URL` i źródłowym
    `KOMPAS_TEST_CATALOG_XLSX`: `uv run pytest -q tests/test_generated_documents.py tests/test_database.py`
    — **37 passed w 9,17 s**. Wynik dodatni/ujemny, uprawnienia, obcy OSP,
    cofnięcie przypisania, błędy zapisu/COMMIT, import i roundtrip migracji OK.
    Znane ostrzeżenie Starlette/httpx pozostaje.
  - `npm run api:types -- http://127.0.0.1:33081/openapi.json` oraz
    `npm run precommit` — format/lint/typy i **170 testów** OK (Vitest 1,25 s).
- Wcześniej w tej fazie: pełny backend **371 passed**, build frontendu i Compose
  z migracją do `0012` — OK. Live HTTP/SSR z RustFS i Supabase potwierdził
  import, oba wyniki, współbieżną idempotencję PDF, checksum/polskie znaki,
  sesyjny download PDF/OSP, HR/ADMIN 404 i anonymous 401. Usunięto własne
  procesy/obiekty smoke i wylogowano sesje; źródłowy OSP pozostał.
- Na prośbę użytkownika ograniczamy kosztowne kontrole: podczas rozwoju szybkie
  testy zmienianej logiki, integracyjne tylko dla dotkniętej granicy. Pełna
  regresja/build/smoke przy faktycznej potrzebie; nie ponawiamy zaliczonych
  kontroli bez nowych zmian lub konkretnej wątpliwości. Precommit przed commitem
  frontendu pozostaje wymagany. Nie dodano kolejnych skryptów smoke.
- Nie uruchamiano przeglądarki/E2E ani porównania wizualnego PDF z DOCX.
  Aktualność prawna historycznego źródła wymaga osobnej weryfikacji; brak AV
  i ręczna procedura naprawy osieroconych obiektów pozostają jak w P5-01.
- Commit: `feat(documents): generate assessment C PDFs`.

### 2026-11-21 — P5-01, prywatne pliki oceny

- Poprzednią fazę zapisano jako `58ecfba feat(assessments): finalize periodic assessments`.
  Przed commitem ponowiono `npm run precommit`: 157 testów, format/lint/typy OK.
- Migracja `0010` dodaje `documents`: UUID, ocena, rodzaj załącznika, bezpieczna
  nazwa, rozpoznany MIME, rozmiar, SHA-256, prywatny klucz, autor i czas UTC.
  FK/CHECK/unikalność i indeks powiązania; bez zmiany danych wcześniejszych ocen.
- `ObjectStorage` używa boto3, S3v4/path-style, jawnych timeoutów i dwóch prób.
  Błędy SDK nie ujawniają danych połączenia. `storage-init` w Compose tworzy
  brakujący prywatny bucket lub sprawdza owner-only ACL i brak polityki bucketu.
  Nie nadpisuje zastanych uprawnień. Uwzględniono domyślny ACL RustFS 1.0.6,
  który pomija ID właściciela. Klucze S3 pozostają wyłącznie po stronie serwera.
- POST `/assessments/{id}/documents?revision=…&filename=…` odbiera surowe bajty
  bez multipart, z limitem 10 MiB podczas czytania strumienia. Używa wspólnego
  `edit_assessment`, blokady przypisania/oceny i atomowego zdarzenia/rewizji.
  Zwraca metadane i nową rewizję. Starszy zapis daje 409; `completed` blokuje upload.
- Walidacja nazwy, rzeczywistej struktury PDF (pypdf) i DOCX (ZIP/CRC/OOXML), MIME,
  szyfrowania, makr i rozpakowywania. Limit DOCX: 256 wpisów, 32 MiB po rozpakowaniu,
  4 MiB na odczytywaną część XML, bez DTD/encji i ścieżek ZIP. Bez ekstrakcji treści.
- GET list/download wymaga autorstwa MANAGER i aktualnego przypisania, także po
  zakończeniu. Inny przypisany przełożony, HR/ADMIN i cudzy plik nie dostają treści.
  Klucz nie trafia do JSON. Download sprawdza rozmiar i checksum przed odpowiedzią,
  zwraca załącznik UTF-8, `nosniff` i `private, no-store`; brak/awaria/niespójność → 503.
- Błąd metadanych lub zdarzenia wycofuje rewizję i kompensuje świeży obiekt.
  Obsłużono PUT, który dotarł do storage mimo błędu odpowiedzi. Po niepewnym COMMIT
  sprawdzamy metadane; zatwierdzony lub niemożliwy do rozstrzygnięcia plik pozostaje.
  Nieudane sprzątanie/reconciliation zapisuje wyłącznie wygenerowany klucz do ręcznej
  naprawy; procedura w `backend/README.md`. Przerwanie procesu między usługami wymaga
  porównania obiektów z metadanymi, bez automatycznego kasowania.
- Wspólne ładowanie tożsamości zwraca 503 przy awarii PostgreSQL, zanim plik trafi
  do storage; nie otwiera dostępu. Naprawiono losowy test P4-05: brak kryterium
  obowiązkowego wskazywany jest teraz jawnie, zamiast zależeć od kolejności UUID.
- Kontrole w `backend/`:
  - `uv run ruff check app tests alembic` i `uv run ruff format --check app tests alembic` — OK.
  - `KOMPAS_TEST_DATABASE_URL=… KOMPAS_TEST_CATALOG_XLSX=… uv run pytest -q` —
    **351 passed**, bez skipów; znane ostrzeżenie Starlette/httpx pozostaje.
  - Testy formatu/limitu, nazw Unicode, spoofingu, uprawnień i cofnięcia przypisania,
    stanów oceny, rewizji, rollbacku metadanych/zdarzenia, błędów PUT/GET/DELETE,
    utraconego potwierdzenia COMMIT i braku dostępu do bazy podczas reconciliation.
  - Migracja head → 0009 → head, wcześniejsze roundtripy i `alembic check` — OK
    w osobnym schemacie. Bazy operatora nie cofano.
- Typy OpenAPI odświeżone przez `npm run api:types -- http://127.0.0.1:33081/openapi.json`.
  `npm run precommit` — format/lint/typy i **157 testów** OK; `npm run build` — OK.
  UI nie montuje jeszcze załączników; P5-02 obejmuje OSP i ekran pobrania PDF.
- Compose `config --quiet` i `up --build --detach --wait --wait-timeout 180 frontend`
  z API/migracją/storage-init — OK; migracja `0010` wdrożona, usługi healthy.
- `PYTHONPATH=. uv run python /tmp/opencode/p5-01-smoke.py` — rzeczywisty MANAGER,
  PDF i źródłowy DOCX OSP, ponowienie 409, błędny PDF 422, dwa równoległe uploady
  201/409 i tylko jedna rewizja, HR/ADMIN 404, brak tokenu 401, anonimowy S3 403.
  Zatrzymanie RustFS daje 503 pobrania i zachowuje listę; ponowny start odtwarza
  identyczne bajty. Usunięto wyłącznie własną ocenę smoke, metadane i obiekty;
  wylogowano sesje testowe. Compose pozostaje uruchomiony.
- Nie uruchamiano przeglądarki ani E2E. Walidacja formatu nie jest skanerem AV;
  procedura naprawy po przerwaniu procesu jest ręczna. Następny krok: P5-02.
- Commit: `feat(documents): store private assessment files`.

### 2026-11-21 — P4-05, wynik i zakończenie oceny C

- Migracja `0009` dodaje `assessment_summaries` z tekstami, autorem/czasem zapisu,
  osobnym autorem/czasem zakończenia i migawką wyniku (outcome, suma/liczba ocen).
  FK/CHECK pilnują wartości i spójności zakończenia. Istniejące dane pozostają bez zmian.
- `result` w odpowiedzi oceny i GET `/{id}/result` używają reguły `periodic_result`
  wyłącznie dla zatwierdzonych decyzji. Przed kompletem: `incomplete` i średnia `null`.
  Dokładny ułamek ustala wynik; tekst średniej z dwoma miejscami służy wyświetlaniu.
  Po zakończeniu odczyt korzysta z utrwalonego wyniku/sumy/liczby ocen.
- PUT `/{id}/summary`: osobny szkic uzasadnienia i wniosków, po 10 000 znaków,
  normalizacja tekstu, serwerowy autor/czas i rewizja. Wnioski są opcjonalne.
- Jawne `complete` sprawdza ustalenia, potwierdzoną rozmowę, komplet wybranych
  kryteriów i zapis podsumowania; wynik negatywny wymaga niepustego uzasadnienia.
  Wspólny `edit_assessment` blokuje ocenę/przypisanie i odświeża ORM. Migawka,
  `completed`, rewizja i zdarzenie są atomowe. Retry źródłowej/wynikowej rewizji
  zwraca ten sam rekord bez nowego zdarzenia; nadal sprawdza aktualny dostęp.
- Zakładka „Wynik i zakończenie” pokazuje wyłącznie wynik API i zatwierdzone oceny,
  braki oraz formularz podsumowania. Niezapisane odpowiedzi/wybrane oceny lub teksty
  blokują zakończenie. Szkice pozostają zamontowane przy zmianie zakładek i błędzie.
  Pending blokuje zapis/nawigację; konflikt daje odnośnik do nowej karty.
  Zamknięta ocena otwiera podsumowanie i wszystkie pola ma tylko do odczytu.
  Bez autofill demo, nowych zależności ani lokalnego obliczania wyniku.
- Kontrole:
  - `uv run ruff format app tests alembic`, `uv run ruff check app tests alembic`
    oraz pytest z `KOMPAS_TEST_DATABASE_URL` i `KOMPAS_TEST_CATALOG_XLSX` —
    **270 passed**, bez skipów. Znane ostrzeżenie Starlette o httpx pozostaje.
  - Testy API: średnia dokładnie 4, ponad 4, ocena 1 mimo wysokiej średniej,
    unieważniona decyzja/sama sugestia, szkic i uzasadnienie, komplet czynności,
    stare rewizje, role/odwołane przypisanie (także retry), rollback zdarzenia,
    wszystkie mutacje po zamknięciu, odczyt bez mutacji i jeden event zakończenia.
  - Dwie rzeczywiste sesje PostgreSQL: zakończenie kontra zmiana odpowiedzi —
    jeden sukces i jeden konflikt, także ze wcześniej załadowanymi danymi ORM.
    Dwa równoległe zakończenia/retry zwracają ten sam wynik i czas.
  - Upgrade/downgrade `0009` do `0008`, upgrade, roundtrip do `0007` i check — OK
    w izolowanym schemacie; danych operatora nie cofano.
  - Naprawiono zastany losowy test izolacji kryteriów: wybierał pierwszy UUID,
    który czasem był tym samym dodatkowym kryterium. Teraz jawnie wybiera inne.
  - `npm run api:types -- http://127.0.0.1:33081/openapi.json` — typy odświeżone.
    `npm run precommit` — format/lint/typecheck i **157 testów / 22 pliki** OK;
    `npm run build` — OK.
  - `npm run doctor` — 31 wskazań doradczych. Nowe dotyczy rozgałęzień formularza
    podsumowania (niekompletność, wynik negatywny, konflikt, tryb odczytu).
    Zachowano jawne stany bez wyciszeń i niepowiązanego refaktoru.
  - Compose rebuild/up dla `frontend` wraz z API/migracją — OK, migracja `0009`
    wdrożona. `node /tmp/opencode/p4-05-smoke.mjs` — pełny proces HTTP/SSR:
    niekompletny/pozytywny/negatywny wynik, wymagane uzasadnienie, stale 409,
    zapis i zakończenie/retry, reload tylko do odczytu, HR/ADMIN → 404.
    Usunięto tylko własną ocenę smoke i wylogowano utworzone sesje.
- Zaktualizowano kontrakt, instrukcje backendu/frontendu i Pomoc. Następny krok:
  P5-01. Nie uruchamiano przeglądarki ani E2E; P8-01 pozostaje blocked.
  PDF, podpisy/doręczenie i procedura korekty nie są częścią tego zakończenia.

### 2026-11-21 — P4-04, wskaźniki i decyzje przełożonego

- Migracja `0008` dodaje `criterion_ratings` oraz `indicator_answers`, FK do
  wybranych kryteriów i CHECK poziomów/ocen/spójności potwierdzenia. Nie zmienia
  wcześniejszych migracji ani danych istniejących ocen.
- Cienkie endpointy PUT `/{id}/criteria/{criterion_id}/answers` oraz POST
  `/{id}/criteria/{criterion_id}/rating` korzystają z serwisu `evaluation.py`,
  wspólnego `edit_assessment` i czystej reguły `suggest_score`. Bez nowych zależności
  i uniwersalnych repozytoriów. Dostęp tylko dla prowadzącego MANAGER z aktualnym
  przypisaniem, zapis wyłącznie w `evaluation`.
- Odpowiedzi obejmują dokładnie wskaźniki danego kryterium z przypiętego snapshotu:
  UUID, poziom 0–4 lub `null` i notatkę do 4000 znaków. Sugestia ma utrwaloną wersję
  polityki, autora i czas UTC. Formalna decyzja 1/3/5/7/9 ma osobny autor/czas;
  nie jest automatycznie przyjmowana i może różnić się od sugestii.
- Zmieniony poziom lub notatka czyści potwierdzenie tylko tego kryterium.
  Identyczny zestaw po normalizacji, również w innej kolejności, zachowuje decyzję.
  Brak obserwacji nie daje domyślnej oceny. Zatwierdzenie kryteriów nie finalizuje
  procesu ani nie oblicza jeszcze wyniku zbiorczego (P4-05).
- Trasa UUID ma zakładkę „Ocena zachowań” z pełnymi opisami katalogu, notatkami,
  osobnym zapisem odpowiedzi i ręcznym wyborem oceny. Niezapisane odpowiedzi blokują
  zatwierdzenie; formularze pozostają zamontowane podczas nawigacji i błędów.
  Pending blokuje kolejne zapisy i nawigację, konflikt daje odnośnik do nowej karty.
  Odtwarzanie nie używa localStorage ani demonstracyjnej punktacji.
- Zgodnie z korektą użytkownika komunikaty mówią o „Proponowanej ocenie”,
  „Zapisie odpowiedzi” i „Twoim zatwierdzeniu”. Nie pokazują określeń „backend”,
  identyfikatora polityki ani UUID autora. Pomoc opisuje ponowienie zatwierdzenia
  i wskazuje, co pozostaje w przygotowaniu.
- Kontrole:
  - `uv run ruff check app tests alembic` oraz format — OK.
  - `KOMPAS_TEST_DATABASE_URL=… KOMPAS_TEST_CATALOG_XLSX=… uv run pytest -q` —
    **243 passed**, bez skipów; znane ostrzeżenie Starlette o `httpx` pozostaje.
  - Testy: remisy/braki, własna decyzja, zmiana notatki i izolowane unieważnianie,
    obcy/nowszy katalog i wskaźnik innego kryterium, uprawnienia/odwołane przypisanie,
    stany/rewizje, rollback po błędzie zdarzenia. Dwie rzeczywiste równoległe sesje
    PostgreSQL (zapis odpowiedzi kontra decyzja): jeden sukces i jeden konflikt,
    również po wcześniejszym załadowaniu danych do identity map.
  - Alembic upgrade/downgrade `0008`/upgrade i `command.check` — OK w osobnym,
    losowym schemacie testowym; istniejących danych operatora nie cofano.
  - Typy odświeżone przez `npm run api:types -- http://127.0.0.1:33081/openapi.json`.
  - `npm run precommit` — format, lint, typecheck i **143 testy / 21 plików** OK;
    `npm run build` — OK.
  - `npm run doctor` — 30 doradczych wskazań. Nowe dotyczy prostego inicjalizatora
    wyboru zapisanej oceny; operacja jest trywialna, stan celowo zachowuje szkic.
    Brak wyciszeń i zmian niepowiązanego kodu.
  - Compose rebuild/up dla `frontend` — OK; API i web healthy, migracja `0008`
    wdrożona. `node /tmp/opencode/p4-04-smoke.mjs` — pełny proces HTTP/SSR na
    rzeczywistym katalogu: odpowiedzi/sugestia, inna decyzja, stale 409, identyczny
    zapis, zmiana notatki, ponowne zatwierdzenie pięciu kryteriów, odświeżenie;
    HR/ADMIN odczyt i obie mutacje → 404. Usunięto tylko własną ocenę smoke
    i wylogowano utworzone sesje.
- Compose pozostawiono działający pod `http://localhost:3000`; oddzielny
  `kompas-postgres-test` zatrzymano po testach.
- Ograniczenia: zgodnie z instrukcją nie uruchamiano przeglądarki ani E2E;
  brak weryfikacji wizualnej. Następny dokładny krok: P4-05, wykorzystać wyłącznie
  aktualnie zatwierdzone `ratings`, regułę `periodic_result` i wspólną kontrolę
  rewizji do wyniku/finalizacji; nie traktować zapisanych sugestii jak decyzji.

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
