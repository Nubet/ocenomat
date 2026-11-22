# Weryfikacja i dalszy rozwój

## Co jest sprawdzone

Rejestr postępu opisuje wcześniejsze wyniki testów backendu, frontendu, importu
danych demonstracyjnych i wybranych wywołań rzeczywistych usług. Wyniki dotyczą
konkretnego stanu kodu i nie potwierdzają automatycznie późniejszych zmian.

Ostatnie zmiany kontekstowej rozmowy przeszły celowane kontrole formatowania,
lintu, typów i generowania OpenAPI. Dodano testy, ale nie zostały uruchomione.
Nie wykonano dla tych zmian testu w przeglądarce ani zapytania do żywego modelu.
Aktualne wyniki: [rejestr postępu](../backend-progress.md).

Ocena formalnego asystenta obejmowała 30 przypadków i ograniczoną bazę wiedzy.
Wynik 28/30 nie jest gwarancją jakości dla innych pytań. Szczegóły i metodyka:
[ewaluacja asystenta](../assistant-evaluation.md).

## Co należy uzupełnić przed wdrożeniem

1. Zweryfikować aktualność i stosowalność źródeł oraz zatwierdzić brakujące
   materiały bazy wiedzy. Osobno sprawdzić poprawność formalną workflow i PDF.
2. Uruchomić pełną regresję i sprawdzić kompletny scenariusz użytkownika.
   Zweryfikować działanie asystenta, dostępów i błędów na fikcyjnych danych.
3. Ocenić dostawcę AI, ochronę danych, retencję i polityki organizacji. Potwierdzić
   zgodność wybranego modelu i sposobu użycia z wymaganiem darmowych narzędzi AI.
4. Przygotować środowisko produkcyjne, domenę, kopie zapasowe, odtwarzanie,
   obserwowalność i procedury utrzymania. Lokalny Compose nie zastępuje wdrożenia.
5. Uzgodnić podpisy, doręczanie dokumentów i integracje z systemami urzędu.
   Integracje EZD/QNT nie są zaimplementowane. Przypomnienie w aplikacji nie jest
   wiadomością e-mail.

## Dane demonstracyjne

Przewodnik opisuje 60 dodatkowych fikcyjnych osób i 60 indywidualnych, uproszczonych
OSP. Dane służą do demonstracji, nie są aktami rzeczywistych pracowników.
Ich obecność zależy od wykonania importu w danym środowisku.
[Przykładowe scenariusze i import](../demo-guide.md).
