# Przegląd źródeł wiedzy — P6-02

> Robocza notatka sprzed audytu oficjalnych pobrań. Stan wdrożenia i aktualności
> prawnej zastępuje [official-sources-audit.md](official-sources-audit.md).
> Siedem decyzji w pliku reviews nie zostało zastosowanych w bazie. Poniższe
> liczby opisują lokalną ekstrakcję, nie istniejący indeks ani zatwierdzony korpus.

Stan: 2026-11-21. Kontekst implementacji: zadanie i regulamin konkursu opisują
wymagania dla programisty. **Nie są wiedzą udostępnianą asystentowi.** Diagram
produktu również jest poza korpusem. Nie dodajemy materiałów użytkownika do Git.

## Powtarzalne artefakty

- `backend/resources/knowledge-manifest.json`: 12 oryginałów, 11 mapowań Markdown,
  stabilne identyfikatory i jawne relacje załączników.
- `backend/resources/knowledge-reviews.json`: decyzje **agenta implementującego**
  po porównaniu tekstu z dostarczonymi oryginałami. Nie są opinią prawnika ani
  potwierdzeniem aktualnego stanu prawnego. Każda dotyczy konkretnego hasha strony.
- `app.modules.knowledge.audit`: raport pełnej ekstrakcji, checksum, lokalizacji,
  ostrzeżeń i różnic. Odtworzenie opisane w `backend/README.md`.
- Pełny lokalny raport: `/tmp/opencode/knowledge-audit.json`; nie jest artefaktem
  wdrożeniowym. Po klonowaniu należy wygenerować go z dostarczonych oryginałów.

## Wynik ekstrakcji i porównania

| Źródło | Fragmenty | Grupy różnic Markdown | Zatwierdzone fragmenty |
| --- | ---: | ---: | ---: |
| Katalog XLSX | 49 | brak reprezentacji | 0 |
| Rozporządzenie okresowe 2016 | 19 stron | 156 | strony 1–4 |
| Poradnik okresowy | 45 stron | 195 | 0 |
| Arkusz B DOCX | 168 | 134 | 0 |
| Arkusz C DOCX | 168 | 129 | 0 |
| Rozporządzenie pierwszej oceny 2015 | 8 stron | 74 | strony 1–3 |
| Poradnik pierwszej oceny | 44 strony | 118 | 0 |
| Arkusz pierwszej oceny DOCX | 125 | 119 | 0 |
| Powielony wykaz kryteriów | 3 strony | 77 | 0 |
| Przykładowe OSP cyberbezpieczeństwo | 157 | 157 | 0 |
| Przykładowe OSP regulacje AI | 131 | 130 | 0 |
| Przykładowe OSP naczelnik | 144 | 144 | 0 |

Łącznie **1061 fragmentów**, z czego **7 zatwierdzonych**, 1054 wymagają kontroli.
Żadne źródło nie jest w całości zatwierdzone. Liczba różnic obejmuje także
formatowanie Markdown, tabele, nagłówki, znaki podziału i sklejenia słów PDF;
nie jest liczbą błędów merytorycznych. Raport pokazuje pierwszych 40 grup różnic,
z jawnym znacznikiem ucięcia. Markdown nie został zaimportowany jako wiedza.

## Sprawdzone miejsca wysokiego ryzyka

Porównano tekst wybranych stron oryginalnych PDF z niezależną ekstrakcją pypdf:

- Okresowa: rozróżnienie formularzy A/B/C; sześć kryteriów A versus pięć B/C;
  do trzech dodatkowych; warunkowe cele, terminy i podpisy; ciągłość § 9 między
  stronami 2–3; skala 1/3/5/7/9, przedziały, średnia >4 i brak 1; obowiązek
  uzasadnienia negatywnego versus możliwość uzasadnienia pozytywnego.
- Pierwsza: pięć elementów; 21 dni i wyjątek zastępstwa; 8 miesięcy versus minimum
  7 miesięcy sprawozdania; skala 3/5/7, średnia ≥5, najwyżej jedna 3; wszystkie
  warunki pozytywnej oceny, trzy wyjątki egzaminu i przepisy przejściowe.
- Nie dopisywano numeracji ani korekt językowych z Markdown. Techniczne sklejenia
  słów i łamania pozostają w ekstrakcji, aby nie zmieniać źródła domysłem.

## Pozostały zakres kontroli

- Wszystkie tabele/formularze, przypisy i checkboxy DOCX; automatyczna numeracja
  oraz symbole niewyrażone zwykłym tekstem wymagają kontroli w oryginale.
- Załączniki i tabele PDF, w tym powielone warstwy tekstowe widoczne m.in. na
  stronie 10 pełnego rozporządzenia okresowego; brak automatycznej deduplikacji
  słów w samym tekście przepisu. Osobny trzystronicowy plik jest powiązany z
  pełnym rozporządzeniem, nie uznany za drugą niezależną podstawę.
- Poradniki: przegląd zgodności interpretacji, dat i zależności od przepisów.
- Katalog: istniejący importer P3 i jego ID są wykorzystywane, ale audyt wiedzy
  nie nadaje automatycznie approval nowej reprezentacji 49 fragmentów.
- Przykładowe OSP: przegląd struktury i zadań; nie są prawem ani dowodem zachowań
  konkretnego pracownika. Prywatne OSP nie trafiają do tego korpusu.
- Brakuje odrębnego zweryfikowanego tekstu ustawy o służbie cywilnej. Dostarczone
  rozporządzenia mają status historycznej edycji; nie sprawdzono aktualności prawa.
  Przed użyciem produkcyjnym wymagane jest uzupełnienie oficjalnych źródeł i
  niezależny przegląd prawny. Approval ekstrakcji nie zmienia tego statusu.
