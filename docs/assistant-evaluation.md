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

## Wynik bazowy 2026-11-21

- Rzeczywisty korpus PostgreSQL, transakcja read-only, bez LLM: właściwe fragmenty
  w top-5 dla **23/23** pytań referencyjnych; suma czasu retrieval **0,1575 s**.
- Pozostałych 7 przypadków nie wlicza się do skuteczności retrieval. Samo znalezienie
  tekstu nie oznacza, że wolno na jego podstawie odpowiedzieć.
- Wykonano 30 rzeczywistych odpowiedzi/odmów. Przegląd techniczny z oryginałami:
  **28/30 poprawnych rezultatów (93,3%)**, **21/23 odpowiedzi na pytania z podstawą**,
  6 prawidłowych odmów i jedno prawidłowe sprostowanie fałszywej przesłanki (N07).
  Dwie nadmiarowe odmowy: F03 (rozmowa wstępna), F09 (dwie trójki).
- F03 przy późniejszej próbie odpowiedział poprawnie, F09 ponownie odmówił.
  Nie zastępujemy nimi wyniku bazowego ani nie deklarujemy osiągnięcia celu 95%.
- 22 odpowiedzi zawierają **53 twierdzenia i 77 cytowań**. Cytowania przeszły
  kontrolę ID/statusu/hash/locatorów/literalności; treść odpowiedzi porównano
  z oryginalnymi paragrafami. Nie wykryto błędnej kategorycznej odpowiedzi.
- Czas bez przerw między pytaniami: średnia **4,469 s**, mediana **4,729 s**,
  maksimum **8,111 s**. Początkowe równoległe uruchomienie przerwał limit 429;
  wznowiono tylko brakujące pytania z odstępami. Nie obchodzono polityk dostawcy.
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

## Trzy OSP i ograniczenia

Pełne oryginały, przypięty katalog i wspólne prompty/walidatory, bez mutacji bazy:

| OSP | Formularz | Poparte rekomendacje |
| --- | --- | --- |
| Cyberbezpieczeństwo, starszy specjalista | C | Podejmowanie decyzji i odpowiedzialność; radzenie sobie w sytuacjach kryzysowych; myślenie analityczne |
| Prawo i regulacje AI, radca | C | Myślenie analityczne; podejmowanie decyzji i odpowiedzialność; kreatywność |
| Współpraca międzynarodowa, naczelnik | B | Rzetelność |

Sprawdzono rzeczywiste fragmenty pól zadań/samodzielności/odpowiedzialności.
Naczelnik miał trzy propozycje, review poparł tylko jedną; pozostałe odrzucono.
Z tego wynika poprawka API: odrzucenie jednej niezależnej propozycji nie kasuje
popartych pozostałych. 21 testów OSP i 38 asystenta OK, dodano tylko jeden test.
Weryfikacja B dotyczy rekomendacji; utworzenie procesu i dokumentu B to P7-01.

Faza 6 zakończona implementacyjnie i oceniona dla ograniczonego korpusu. Cel 95%
całych odpowiedzi pozostaje nieosiągnięty, dwie nadmiarowe odmowy są znanym
ograniczeniem. Review drugiego promptu tego samego modelu nie jest niezależnym
przeglądem prawnym. Scenariusz demonstracji jest gotowy; przeglądarki/E2E nie
wykonywano zgodnie z instrukcją użytkownika. Nie twierdzimy, że cała wiedza prawna
jest kompletna lub że wyeliminowano halucynacje.
