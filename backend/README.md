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
