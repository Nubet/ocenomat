# Kompas Kompetencji — postęp backendu

Plan i obowiązujące decyzje: [backend-implementation-plan.md](backend-implementation-plan.md).
Ten plik opisuje faktyczny stan, nie planowane rezultaty. Aktualizacja: 2026-11-21.

## Bieżący stan

- **Etap:** 1 — fundament techniczny, w toku.
- **Aktywne zadanie:** brak; P1-02 zakończone.
- **Następny krok:** P1-03 — wspólne środowisko Compose.
- **Ostatnia zakończona praca:** PostgreSQL, Alembic i readiness.
- **Stan aplikacji:** frontend to demo z lokalnym stanem; backend ma `/health`
  i `/api/v1/health`, połączenie PostgreSQL i historię migracji bez tabel domenowych.
  Supabase, RustFS, OpenRouter i VPS nie zostały zintegrowane.
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
| P1-03 | Compose: frontend, API, PostgreSQL, RustFS | pending | — |
| P2-01 | Tożsamość, role, weryfikacja JWT | pending | — |
| P2-02 | Logowanie i sesja | pending | — |
| P2-03 | Pracownicy i przypisania | pending | — |
| P3-01 | Katalog kompetencji | pending | — |
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
