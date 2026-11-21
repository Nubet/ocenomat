# Środowisko lokalne

Wymagania: Docker Engine i Compose v2.20+; polecenia z katalogu głównego repo.
Obrazy bazowe Node i Python pobieramy z publicznego mirroru oficjalnych obrazów
Docker Library w ECR (Docker Hub zwracał 429 podczas weryfikacji).

1. Skopiuj `.env.example` do `.env` i zastąp `CHANGE_ME` własnymi losowymi
   wartościami (np. `openssl rand -hex 24`). Hasło PostgreSQL w tym wariancie musi
   być URL-safe; nie używaj znaków wymagających kodowania w URL. Nie commituj `.env`.
2. Sprawdź konfigurację bez wypisywania sekretów:

   ```sh
   docker compose --env-file .env -f infra/compose.yaml -f infra/compose.dev.yaml config --quiet
   ```

3. Uruchom:

   ```sh
   docker compose --env-file .env -f infra/compose.yaml -f infra/compose.dev.yaml up --build
   ```

Frontend: http://localhost:3000; API: http://localhost:8000/health oraz
http://localhost:8000/api/v1/health; RustFS S3: http://localhost:9000;
konsola: http://localhost:9001. Porty zmienisz w `.env`; dostosuj też
`KOMPAS_CORS_ORIGINS` do originu frontendu. Wszystkie porty są lokalne (loopback).
`API_BASE_URL` jest adresem dla kodu serwerowego Next.js; nie używaj nazwy
`backend` w przeglądarce. Integracja danych UI jest w kolejnych etapach planu.

Compose czeka na bazę, wykonuje jednorazowy serwis `migrate`, dopiero potem
uruchamia API i frontend. Po dodaniu migracji wykonaj ponownie `up --build`,
nie samo `restart`. Nie uruchamiaj migracji równolegle z kilku terminali.

`postgres-data` i `rustfs-data` są trwałymi wolumenami. Zwykłe `restart` i `down`
zachowują dane; **nie dodawaj `--volumes` / `-v` do `down`**. Zmiana hasła w `.env`
nie zmienia hasła już zainicjalizowanej bazy. RustFS działa jako UID 10001;
nazwany wolumen przejmuje uprawnienia katalogu obrazu. Nie montuj katalogu hosta
bez przygotowania właściciela. Healthcheck `/health` sprawdza wybraną wersję
RustFS, nie uprawnienia bucketu. Bucket i integracja API powstaną w P5-01.

To konfiguracja developerska (Next dev, reload API), nie wdrożenie produkcyjne.
Nie podłączaj prawdziwych danych pracowników. Ustaw `KOMPAS_SUPABASE_URL`,
`KOMPAS_JWT_ALGORITHM` i `SUPABASE_PUBLISHABLE_KEY` z projektu Supabase Cloud,
wyłącz publiczną rejestrację i utwórz lokalny profil zgodnie z `backend/README.md`.
Bez konfiguracji frontend pokazuje ekran logowania z informacją o braku usługi;
API nie ma trybu bypass. Supabase i OpenRouter nie są lokalnymi serwisami Compose.
