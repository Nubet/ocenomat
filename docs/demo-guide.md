# Prezentacja OcenoMat

## Dostęp i dane

Lokalne logowanie: `http://localhost:3000/login`. Konta i sposób przechowywania
hasła opisuje [rejestr kont](backend-progress.md#konta-środowiska-testowego).

- **Przełożony** (`konto-przelozony@hacknation.pl`): profile 63 przypisanych osób,
  prowadzenie ocen, prywatne dokumenty i asystent w kontekście własnej oceny.
- **HR** (`konto-hr@hacknation.pl`): 64 profile i monitoring metadanych, terminów
  oraz przypomnień. Bez treści ocen, notatek i dokumentów przełożonego.
- **Administrator** (`konto-admin@hacknation.pl`): 64 profile; sama rola ADMIN
  nie daje prawa prowadzenia oceny ani projekcji HR.

W bazie jest 64 pracowników i 61 ocen. Nowy zestaw obejmuje 60 osób w sześciu
obszarach: cyberbezpieczeństwo, AI, usługi cyfrowe, dane, współpraca międzynarodowa
i HR. Wszystkie nowe osoby przypisano do istniejącego konta przełożonego.
Profile mają realistyczne nazwy stanowisk i komórek. Osoby i zdarzenia są
opracowanymi scenariuszami, nie autentycznymi danymi personalnymi MC.

## Nawigacja po pracownikach

1. Otwórz **Pracownicy**. Domyślnie lista pokazuje 20 osób.
2. Wpisz imię, nazwisko lub stanowisko, np. `radca`, `Wysocka` albo `Lukasz`.
   Kolejność słów i polskie znaki nie są wymagane.
3. Opcjonalnie wybierz typ stanowiska i naciśnij **Szukaj**. Sortowanie po
   osobie, stanowisku lub komórce oraz 10/20/50 osób stosuje przycisk **Zastosuj**.
4. **Poprzednia / Następna** zachowują warunki wyszukiwania. Po otwarciu profilu
   przycisk **Wróć do pracowników** wraca do tej samej strony i filtrów.
5. **Wyczyść filtry** przywraca pełny katalog dostępny dla konta.

Wyszukiwarka pod `Ctrl/Cmd+K` pokazuje maksymalnie osiem osób i odsyła do pełnych
wyników. Wyszukiwanie i stronicowanie korzystają z backendu.

## Proponowane przypadki

| Osoba | Co pokazać |
| --- | --- |
| Michał Sokołowski | Zakończony arkusz B dla naczelnika; decyzja przełożonego różna od sugestii behawioralnej. |
| Katarzyna Wysocka | Bieżąca ocena na etapie oceniania oraz zakończona ocena z wcześniejszego okresu. |
| Łukasz Brzeziński | Trwający okres: obserwacje i przygotowanie rozmowy. |
| Joanna Cieślak | Szkic, dobór kryteriów i analiza OSP przed uzgodnieniem. |
| Robert Kubiak | Zakończona negatywna ocena okresowa z uzasadnieniem i działaniami rozwojowymi. |
| Natalia Zawadzka | Pierwsza ocena na etapie ustaleń wstępnych. |
| Igor Błaszczyk | Negatywna pierwsza ocena z niezdanym egzaminem. |
| Ewa Rutkowska | Zaległy termin w monitoringu i zapisane przypomnienie HR. |
| Tomasz Jaworski | Osoba bez rozpoczętej oceny, z OSP gotowym do wybrania: przeprowadzenie własnego procesu od początku. |

Nowy zestaw zawiera 60 ocen: 48 okresowych i 12 pierwszych; 21 zakończonych,
w tym dwie negatywne. Prywatny storage zawiera 60 opisów stanowisk i 24 notatki
do rozmów. PDF generuje się z zakończonej oceny przez standardowy formularz.

## Ponowienie importu

W skonfigurowanym backendzie:

```sh
python -m app.demo.seed \
  --manager-subject dfc5c072-34dd-4560-8c4d-46e3defa69a1 \
  --as-of 2026-11-22
```

Identyfikator wskazuje istniejące lokalne konto przełożonego; w innym środowisku
trzeba podać UID jego konta Auth. Import zachowuje istniejące osoby, oceny,
edycje i pliki. Uzupełnia brakujące OSP sześciu osób przygotowanych do rozpoczęcia
nowej oceny. Nie resetuje bazy ani kont.

Przeglądarka/E2E nadal nieuruchomione. Większy zestaw pracowników nie rozszerza
zatwierdzonej wiedzy prawnej asystenta; ograniczenia jakości RAG pozostają
w [rejestrze postępu](backend-progress.md#ograniczenia-i-zależności-zewnętrzne).
