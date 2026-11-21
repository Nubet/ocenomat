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
Próba z rzeczywistym Supabase wymaga osobnej konfiguracji i nadal jest niewykonana.
