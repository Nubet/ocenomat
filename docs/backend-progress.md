# Kompas Kompetencji — postęp backendu

Plan i obowiązujące decyzje: [backend-implementation-plan.md](backend-implementation-plan.md).
Ten plik opisuje faktyczny stan, nie planowane rezultaty. Aktualizacja: 2026-11-21.

## Bieżący stan

- **Etap:** 2 — tożsamość; fundament techniczny zakończony.
- **Aktywne zadanie:** brak; P3-01 zakończone.
- **Następny krok:** niezależne P3-02; do testu live P2-01 potrzebne
  skonfigurowane Supabase Cloud i rzeczywisty token użytkownika.
- **Ostatnia zakończona praca:** pełny import katalogu i chronione API.
- **Stan aplikacji:** frontend to demo z lokalnym stanem; backend ma `/health`
  i `/api/v1/health`, połączenie PostgreSQL i historię migracji bez tabel domenowych.
  RustFS działa lokalnie; integracja plików z API jest w P5-01.
  Supabase, OpenRouter i VPS nie zostały zintegrowane.
- **Kontrole frontendu:** `npm run precommit` — format, Oxlint, TypeScript oraz
  19 testów Vitest przeszły przed commitami zmian frontendu.
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
| P2-01 | Tożsamość, role, weryfikacja JWT | blocked | Kod i 45 testów OK; brak konfiguracji Supabase blokuje próbę live. `feat(auth): verify identities and load roles` |
| P2-02 | Logowanie i sesja | pending | — |
| P2-03 | Pracownicy i przypisania | pending | — |
| P3-01 | Katalog kompetencji | done | Import i porównanie treści XLSX, 52 testy; `feat(catalog): add competency model` |
| P3-02 | Reguły i testy domenowe | pending | — |
| P4-01 | Utworzenie i wznowienie oceny C | pending | — |
| P4-02 | Kryteria i terminy | pending | — |
| P4-03 | Obserwacje i rozmowa | pending | — |
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

## Wykonane zadania

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
