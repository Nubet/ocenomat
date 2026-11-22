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

Compose czeka na bazę i RustFS, wykonuje jednorazowe serwisy `migrate` oraz
`storage-init`, dopiero potem uruchamia API i frontend. `storage-init` tworzy
prywatny bucket `KOMPAS_STORAGE_BUCKET` (domyślnie `kompas-private`) lub sprawdza
jego politykę i ACL; nie usuwa danych ani nie zmienia zastanych uprawnień.
Po dodaniu migracji lub zmianie inicjalizacji wykonaj ponownie `up --build`,
nie samo `restart`. Nie uruchamiaj migracji równolegle z kilku terminali.

`postgres-data` i `rustfs-data` są trwałymi wolumenami. Zwykłe `restart` i `down`
zachowują dane; **nie dodawaj `--volumes` / `-v` do `down`**. Zmiana hasła w `.env`
nie zmienia hasła już zainicjalizowanej bazy. RustFS działa jako UID 10001;
nazwany wolumen przejmuje uprawnienia katalogu obrazu. Nie montuj katalogu hosta
bez przygotowania właściciela. Healthcheck `/health` sprawdza wybraną wersję
RustFS, nie uprawnienia bucketu. Prywatne pliki są dostępne wyłącznie przez API;
konfiguracja S3 i oba klucze trafiają tylko do backendu i usług inicjalizacyjnych.
Pobranie sprawdza dostęp do oceny, rozmiar i checksum. Przy logach
`Storage cleanup required` / `Storage reconciliation required` operator sprawdza
metadane przed usunięciem wskazanego obiektu (procedura w `backend/README.md`).

To konfiguracja developerska (Next dev, reload API), nie wdrożenie produkcyjne.
Nie podłączaj prawdziwych danych pracowników. Ustaw `KOMPAS_SUPABASE_URL`,
`KOMPAS_JWT_ALGORITHM` i `SUPABASE_PUBLISHABLE_KEY` z projektu Supabase Cloud,
wyłącz publiczną rejestrację i utwórz lokalny profil zgodnie z `backend/README.md`.
Bez konfiguracji frontend pokazuje ekran logowania z informacją o braku usługi;
API nie ma trybu bypass. Supabase i OpenRouter nie są lokalnymi serwisami Compose.

## Serwer demonstracyjny

Na VPS użyto `compose.yaml` z `compose.deploy.yaml` i plikiem `.env` na serwerze:

```sh
docker compose --env-file .env -f infra/compose.yaml -f infra/compose.deploy.yaml up -d --build
```

Frontend buduje `frontend/Dockerfile.deploy` i nasłuchuje wyłącznie na loopbacku.
Nginx na hoście obsługuje HTTPS według `nginx-deploy.conf`; konfiguracja zawiera
adres IP i ścieżkę certyfikatu konkretnego serwera. Baza i RustFS nie mają
publikowanych portów. Firewall dostawcy dopuszcza SSH, HTTP, HTTPS i ICMP.

Certyfikat IP ma krótki okres ważności. Certbot używa webroot
`/var/www/letsencrypt` oraz deploy hooka przeładowującego nginx. Sprawdzenie:

```sh
certbot renew --dry-run --run-deploy-hooks
```

Środowisko zawiera kopię fikcyjnych danych i korzysta z tego samego Supabase Auth
oraz konfiguracji AI co lokalne demo. Kopie zapasowe i ich odtwarzanie wymagają
osobnej konfiguracji; nie usuwaj wolumenów podczas aktualizacji.

### Wdrożenie z GitHub Actions

Workflow `.github/workflows/deploy.yml` uruchamia kontrole frontendu i backendu,
a po ich powodzeniu wysyła dokładny commit z `main` na VPS. Serwer buduje obrazy,
zatrzymuje aplikację, zapisuje kopię PostgreSQL w `/opt/ocenomat/backups/`,
wykonuje migrację Alembic i uruchamia backend oraz frontend. Wolumeny PostgreSQL
i RustFS pozostają na miejscu. Wdrożenia są kolejkowane, a dodatkowa blokada na
serwerze zapobiega równoczesnemu wykonaniu skryptu.

Wymagane sekrety GitHub Actions: `DEPLOY_SSH_KEY` (osobny klucz SSH mający
dostęp do serwera) i `DEPLOY_KNOWN_HOSTS` (zweryfikowany klucz hosta w formacie
`known_hosts`). Workflow łączy się jako root z adresem wpisanym w workflow;
dostęp do sekretu daje uprawnienia administratora serwera. Klucz hosta należy
zweryfikować niezależnie przed skonfigurowaniem sekretu. Repozytorium musi
zawierać pliki wdrożenia, a `/opt/ocenomat/.env` musi pozostać na serwerze.

Po błędzie migracji lub uruchamiania wdrożenie kończy się błędem i aplikacja może
pozostać zatrzymana; sprawdź logi Actions i stan Compose przed ręczną naprawą.
Nie uruchamiaj automatycznego rollbacku migracji. Kopia przed wdrożeniem jest
lokalna, obejmuje tylko PostgreSQL i nie zastępuje niezależnych, regularnych kopii
PostgreSQL i RustFS ani przetestowania ich odtwarzania. Pliki kopii i katalogi
wydań nie są automatycznie usuwane — kontroluj wolne miejsce na VPS.
