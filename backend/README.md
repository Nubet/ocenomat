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
