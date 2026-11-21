# Ewaluacja asystenta — P6-07

## Uruchomienie

Z `backend/`, przy ustawionych zmiennych `KOMPAS_*` istniejącego środowiska:

```sh
uv run python -m app.modules.ai.evaluate
uv run python -m app.modules.ai.evaluate --generate
```

Pierwsze polecenie mierzy wyłącznie retrieval. Drugie dodatkowo wywołuje
skonfigurowany model (może generować koszty), przerywając generowanie po pierwszym
błędzie providera. Oba wypisują raport JSON i używają transakcji tylko do odczytu.
Nie przekazują prywatnych ocen ani OSP. Nie zmieniają modelu lub polityk dostawcy.

Zestaw `backend/resources/assistant-evaluation.json` zawiera 30 pytań: 23 z
oczekiwanymi odpowiedziami i locatorami oryginałów ELI oraz 7 dotyczących braków
podstaw, niejednoznaczności, fikcyjnych źródeł i narzucania poleceń. Odpowiedzi
porównano z oryginalnymi paragrafami; źródła mają hash-bound review powiązane
z dostarczonymi PDF. Zestaw nie zastępuje przeglądu prawnego.

## Wynik 2026-11-21

- Rzeczywisty korpus PostgreSQL, transakcja read-only, bez LLM: właściwe fragmenty
  w top-5 dla **23/23** pytań referencyjnych; suma czasu retrieval **0,1575 s**.
- Pozostałych 7 przypadków nie wlicza się do skuteczności retrieval. Samo znalezienie
  tekstu nie oznacza, że wolno na jego podstawie odpowiedzieć.
- Generowanie, poprawność semantyczna i skuteczność odmów: **niezmierzone**,
  OpenRouter zablokowany. Wynik 23/23 nie jest wynikiem jakości odpowiedzi.
- Jeden test narzędzia: rozdzielenie retrieval/generowania i brak kolejnych prób
  po awarii providera. Ruff lint/format OK. Bez nowych smoke/E2E i pełnej regresji.

## Przegląd po odblokowaniu providera

1. Uruchom `--generate`; dla każdego rekordu porównaj całą odpowiedź z
   `expected_answer`, oryginałem i warunkami/wyjątkami. Sam `status_matches` nie
   oznacza poprawności merytorycznej. Uzasadnione sprostowanie fałszywej przesłanki
   jest dopuszczalne także wtedy, gdy przewidziano odmowę.
2. Sprawdź dosłowność cytatów, właściwy typ oceny i dostępność oryginału. Zanotuj
   osobno błąd treści, cytowania, wyjątku i kategoryczną odpowiedź bez podstaw.
3. W istniejącym UI wykonaj analizę trzech dostarczonych OSP: oceń związek obowiązku
   z kryterium, locatory i brak automatycznego wyboru. Nie zapisuj treści OSP w raporcie.
4. Dopiero po przeglądzie raportuj trafność semantyczną, odmowy i czas generowania.
   Demonstracja: rzeczywista ocena → pytanie ze źródłem → oryginał → brak podstaw
   → analiza OSP → ręczny wybór kryteriów → wynik istniejącego silnika.

P6-06/P6-07 pozostają zablokowane kryterium rzeczywistej jakości. Faza 6 nie jest
ukończona; rozpoczęcie fazy 7 czeka zgodnie z ustaloną kolejnością.
