# Kompas Kompetencji — wskazówki dla agentów

## Przed pracą nad backendem

1. Przeczytaj `docs/backend-implementation-plan.md` oraz `docs/backend-progress.md`.
   Pierwszy plik zawiera decyzje i kryteria wykonania; drugi — rzeczywisty stan,
   aktywne zadanie, ograniczenia i następny krok.
2. Sprawdź `git status`, odpowiedni kod i testy. Nie zakładaj, że stan odpowiada
   wcześniejszej rozmowie. Szanuj niepowiązane i nieśledzone pliki użytkownika.
3. Wybierz następne zadanie zgodnie z progresem i oznacz je `in_progress`.
   Nie zmieniaj ustalonych decyzji bez uzasadnienia w planie.

## Zasady implementacji

- Pracuj małymi vertical slices zgodnie z planem; kończ zadanie wraz z wymaganymi
  testami, migracją, API i integracją UI, zamiast budować warstwy na zapas.
- Zachowaj wygląd i komponenty frontendu. Dane demonstracyjne i lokalna punktacja
  nie są autorytatywnym modelem biznesowym. Wynik formalny ustala backend,
  a ocenę cząstkową zatwierdza uprawniony przełożony.
- Stack i granice: Next.js, FastAPI/Python/uv, PostgreSQL/SQLAlchemy/Alembic,
  Supabase Cloud wyłącznie do auth, własna autoryzacja w API i bazie, prywatny
  RustFS, OpenRouter za adapterem, Docker Compose. Bez Redis, kolejek i mikroserwisów.
- Nie wprowadzaj sekretów do repozytorium, logów ani dokumentacji. Nie traktuj
  fikcyjnych danych ani niezweryfikowanych przepisów jako danych produkcyjnych.
- Nie uruchamiaj przeglądarki ani testów przeglądarkowych, dopóki użytkownik nie
  zmieni wcześniejszej instrukcji. Ograniczenia zewnętrznych usług zapisuj jako
  blokery, nie zastępuj brakującej funkcjonalności pozornie działającym demo.

## Po zadaniu

- Uruchom kontrole stosowne do zmiany; przed każdym commitem obejmującym frontend
  wykonaj `npm run precommit` w `frontend/`. React Doctor jest doradczy, a jego
  wskazania wymagają oceny w kontekście.
- Uaktualnij `docs/backend-progress.md`: status, faktyczny wynik, komendy i ich
  wynik, blokery oraz dokładny następny krok. `done` oznacza spełnione kryteria.
- Po udanej weryfikacji sprawdź status, diff, staged diff i historię; stage'uj
  wyłącznie zamierzone pliki i wykonaj krótki angielski Conventional Commit bez
  body. Nie dodawaj zbiorczo nieśledzonych `.idea/`, `.opencode/` ani materiałów
  w `docs/hacknation-materials/` i `docs/inspo/`.
