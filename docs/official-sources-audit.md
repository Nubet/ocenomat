# Audyt oficjalnych źródeł i istniejącej implementacji RAG

**Sprawdzenie: 2026-11-21, od 19:23 UTC.** Raport opisuje odczyt usług,
kod i lokalne pliki, nie zakłada zakończenia fazy 6. Podczas audytu nie zmieniano
danych aplikacji ani schematu; po jego zakończeniu wykonano opisaną w §8 kontynuację:
odbudowę backendu i addytywne migracje. Nie wykonywano importu ani PUT/DELETE w RustFS.
§1–8 zachowują stan audytu wejściowego. Wykonana następnie ekstrakcja HTML/ustawy
i rozszerzenie manifestu 12 → 16 są opisane w §9.

## 1. Stan faktyczny implementacji i danych

| Obszar | Wynik odczytu / inspekcji |
| --- | --- |
| Git | `e8cae61` provider, `f122c29` ekstrakcja, `7b0ca74` trwały importer. Ostatni commit potwierdzony; siedem roboczych decyzji review pozostawało poza commitem i bazą. |
| Aplikacyjny PostgreSQL — stan wejściowy | Kontener `kompas-db-1`, baza `kompas`, **Alembic `0012`**, 17 tabel publicznych. Brak `knowledge_sources`, `knowledge_chunks` i indeksów wiedzy. Nie ma źródeł ani fragmentów RAG do deduplikacji w tej bazie. **Stan po kontynuacji: 0014, obie tabele istnieją, nadal 0 źródeł i 0 fragmentów** — szczegóły w §8. |
| Katalog aplikacji | Jedna wersja `model-2026-11-21`, ID `747213c6-5312-5c93-bc07-57070f6e8293`, 14 kryteriów. `source_sha256=f19e3d95e9331facf7ad4b291b6966f1807a080a9e84e7ba83a228f499c956d6`, zgodny z XLSX. To istniejący autorytatywny katalog, nie korpus tekstów prawnych. |
| Prywatne dokumenty | Jeden rekord `documents`, jeden `job_descriptions`. Nie są wspólną bazą wiedzy. Nie pobierano ich treści do modelu ani raportu. |
| RustFS | Kontener zdrowy. W prywatnym bucketcie `kompas-private` **jeden obiekt z prefiksem `job-descriptions/`**, zero `knowledge/`. Odczytano wszystkie strony `list_objects_v2`, nie samą pierwszą. Brak obiektów korpusu RAG. |
| Backend Compose — stan wejściowy | Uruchomiony, **unhealthy**: healthcheck `/api/v1/health` kończy się timeoutem 7 s; także `/health` timeout 3 s. Dostęp administracyjny do DB i S3 działa niezależnie. Log workera Uvicorn: `ModuleNotFoundError: No module named 'httpx'` podczas importu providera. Montowany kod P6-01 uruchamiał się w starym obrazie bez nowej zależności runtime. |
| Baza testowa | Oddzielny `kompas-postgres-test`, port 55439. Testy migracji i importu korzystały wyłącznie z tej bazy, nie z danych aplikacji. |
| Wyszukiwanie | **Nie istnieje jeszcze `KnowledgeRetriever`, FTS, embeddings ani endpoint wyszukiwania wiedzy.** P6-03 jest pending. Wersja katalogu nie oznacza zaindeksowania RAG. |
| Generowanie i cytowania | Jest adapter OpenRouter, ale nie ma backendowego chatu ani walidatora cytowań. Ostatnia wcześniejsza próba generowania: 401 `User not found.`; w tym audycie nie powtarzano płatnych wywołań. |
| UI | `responses.ts` wybiera gotowe odpowiedzi regexami i zwraca ręcznie wpisane teksty `source`. Brak `chunk_id`, dostępu do oryginału i sprawdzenia twierdzeń. Na zapisanych ocenach drawer pokazuje komunikat o przygotowywanej funkcji. |

### Co rzeczywiście robi importer

`app.modules.knowledge.ingestion` czyta **wyłącznie `SourceSpec.path`**, czyli
oryginalny PDF/DOCX/XLSX. Markdown jest czytany tylko przez osobny audyt porównawczy;
nie zastępuje nieobsługiwanego oryginału. Podczas audytu importer nie obsługiwał
jeszcze HTML; kontrolowane profile dodano w §9. Nadal nie obsługuje ogólnego XLSX
formularzy: ścieżka XLSX jest przeznaczona dla modelu kompetencji P3.
Nie wolno podać jej formularza Excel i uznać go za katalog.

Na początku audytu migracja `0013` istniała w kodzie, ale nie była wdrożona w Compose. Zapisuje źródło,
oryginał w prywatnym storage, fragmenty i jawne decyzje recenzenta. ID źródeł są
stabilne; ID fragmentu to UUID5 zależny od source ID, lokalizatora i hasha tekstu.
Retry sprawdza oryginał, metadane i treść fragmentów, ma blokadę transakcyjną i
kompensację nieudanego nowego uploadu. Nie jest to mechanizm konsolidowania dwóch
różnych source ID reprezentujących ten sam akt. Relacje kanoniczne są potrzebne
niezależnie od unikalności `(source_id, locator)`.

## 2. Inwentaryzacja wszystkich lokalnych dokumentów

Przejrzano rekurencyjnie **55 plików**: 26 w `oficjalne-zrodla/` (25 pobrań i
manifest), 12 Markdownów, 16 pozostałych oryginałów/archiwów oraz plan fazy 6.
Obliczono SHA każdego pliku, odczytano ekstrakcje PDF/DOCX, treść i strukturę HTML,
arkusze/komórki/formuły XLSX oraz zawartość ZIP. **Nie jest to deklaracja ręcznego
zatwierdzenia wszystkich zdań, tabel ani aktualności wszystkich interpretacji.**
Wszystkie 25 rozmiarów i hashy zgadzają się z `MANIFEST_POBRANYCH.json`, także po
przeniesieniu czterech plików do `historical/`. Zgodność z lokalnym manifestem jest
dowodem integralności pobrania, nie samodzielnym dowodem poprawnej interpretacji.

Skróty ścieżek poniżej: **O** = `docs/hacknation-materials/oficjalne-zrodla/`,
**M** = `docs/hacknation-materials/markdown/`, **H** = `docs/hacknation-materials/`.
Typ pliku jest podany rozszerzeniem. Kolumna „Rola” odsyła do pełnej klasyfikacji:

| Rola | Zawartość, status i użycie |
| --- | --- |
| L | Ustawa o służbie cywilnej wraz z obwieszczeniem i przypisami, 39 stron. Akt obowiązuje; tekst jednolity przedstawia stan na 14.04.2026. Ważny dla formalnego asystenta, terminów, OSP i sprzeciwu. Indeksować wybrane, zweryfikowane jednostki ustawy; nie utożsamiać całego pliku z jedną datą wejścia w życie. Szczegóły w §4. |
| P | Rozporządzenie okresowe, Dz.U. 2016/470: §§1–14, kryteria i formularze A/B/C. ELI: obowiązujący. Kanoniczny tekst docelowo HTML, PDF jako dowód i źródło załączników; cytowalne po kontroli ekstrakcji i zakresu zastosowania. |
| F | Rozporządzenie pierwszej oceny, Dz.U. 2015/1144: §§1–14 i trzy załączniki. ELI: obowiązujący. HTML dla jednostek normatywnych, oryginał dla tabel/formularzy; przydatne formalnie, nie jako dowód zachowania osoby. |
| GP/GF | Poradniki KPRM z września 2016: 45/44 strony. Wyjaśnienia procedury, terminy, rozmowy, przykłady. Aktualność interpretacji niezweryfikowana w całości; **nie przepisy prawa**. PDF i prawdziwa strona; selektywny kontekst po kontroli z ustawą. Przydatne do rozmowy. |
| A/B/C | Formularze okresowe: odpowiednio załączniki 2/3/4 do P. DOCX 166/168/168 fragmentów; XLSX to narzędzie z arkuszami pomocniczymi i formułami (wersja 1.1, 2016), nie nowy akt. Głównie walidacja pól, checkboxów, przypisów i reguł; nie osobne podstawy prawne. Sama publikacja na KPRM nie zatwierdza wszystkich komórek. |
| FF | Arkusz pierwszej oceny, załącznik 2 do F: DOCX 125 fragmentów; XLSX wersja 1.0 zawiera też formularz sprawozdania, opisy elementów i arkusz importu. Walidacja struktury, nie niezależna podstawa prawna. |
| R | Formularz sprawozdania, załącznik 3 do F, DOCX 19 fragmentów z przypisem opisującym zadania/terminy/rezultaty. Walidacja formularza i objaśnienie sprawozdania; cytat normatywny powinien odwołać się do F. |
| E | Opisy pięciu elementów pierwszej oceny, załącznik 1 do F, DOCX 34 fragmenty. **Nagłówek ma „z dnia … (poz. …)”**: nie odtwarzać daty z domysłu. Walidować z ogłoszonym załącznikiem; wartościowe opisy, nie samodzielna kompletna identyfikacja aktu. |
| Q | 31 pytań i odpowiedzi KPRM: zakres ocen, terminy, nieobecności, sprzeciw, uzasadnienia, pierwsza ocena. Źródło samo zastrzega: opinia, nie wiążąca wykładnia. Zachować ostrzeżenie, całe Q&A i przypisy; brać `article#main-content` / `details`, bez menu/stopki. Nie nadawać statusu przepisu. |
| I | Siedmiostronicowa instrukcja obsługi arkuszy Excel KPRM, wersja 1.0, 2015. Dotyczy starego narzędzia, nie naszej nawigacji. Wyłączyć z domyślnego RAG; pomoc w technicznej walidacji formularzy. |
| H15/H09/HF09 | Dawne rozporządzenia: okresowe 2015/1143 (20 stron), okresowe 2009/633 (22), pierwsze 2009/772 (12). ELI potwierdza utratę mocy; wyłącznie kontekst historyczny z datą. PDF 2009 ma dodatkowo problemy kodowania polskich liter. |
| HG09 | Poradnik okresowy 2009: 116 stron, tekst na 113, brak tekstu stron 1/3/116, uszkodzone glify i układ. Historyczny kontekst, nie aktualne prawo; domyślnie wyłączyć. Ewentualne ponadczasowe wskazówki rozmowy wymagają osobnej kontroli, nie legalizują dawnych reguł. |
| K | Model kompetencji: 15 arkuszy, 14 kryteriów, 49 wskaźników z poziomami. Używać istniejącego wersjonowanego katalogu aplikacji i jego UUID; nie drugiego katalogu tekstowego. Nie jest aktem prawa. |
| S1/S2/S3 | Przykładowe OSP: cyberbezpieczeństwo / regulacje AI / naczelnik współpracy międzynarodowej. Odpowiednio 157/131/144 fragmenty DOCX. Przykłady zadań do analizy OSP i rekomendowania kryteriów, nie dowody zachowań, oceny osoby ani źródła prawa. |
| AUX | Pomocnicze AI Markdown. 11 mapowań oryginałów i opis diagramu. Zgodność 1:1 niezatwierdzona; nie indeksować jako oryginałów, nie cytować samodzielnie. |
| DEV | Zadanie/regulamin konkursu, diagram i plan implementacji: wymagania/kontekst programisty, poza wiedzą asystenta. |
| META/ZIP | Manifest pobrań: dowód URL/hash, nie wiedza dla użytkownika. ZIP: transport identycznych trzech S, nie dodatkowy korpus. |

### 2.1. Oficjalne źródła — wszystkie pliki, także historical

| Ścieżka | SHA-256 | Rola |
| --- | --- | --- |
| O/ustawa_sluzba_cywilna_tekst_jednolity_2026_DU590.pdf | `153e60d6fa8c196c4e022c006e363bccec816f30584c9634a3d2d9b24c8b0f3c` | L |
| O/rozporzadzenie_oceny_okresowe_2016_DU470.pdf | `036fe77d5dc4b87301496b72f6f468fd9a1c3e1c884eacbd7f1e8079a3314730` | P |
| O/rozporzadzenie_pierwsza_ocena_2015_DU1144.pdf | `0e8a0cf5c9c390edfc5a8868f57fcec2c539f37738c1775f9bed06e98389f217` | F |
| O/rozporzadzenie_oceny_okresowe_2016_eli.html | `e32ee6692ea3d4f4ddccc7abf16c0a600eaeee97b471f9512b9599b582cd6ba2` | P, alternatywny format |
| O/rozporzadzenie_pierwsza_ocena_2015_eli.html | `06515d7192f7d9501decf9013f0cde9d8313d8046eb2e4d1f1f341d64f1a2f5c` | F, alternatywny format |
| O/kprm_oceny_pracownicze_FAQ.html | `e725c3ae1984f897998cb94f476c05f99b77a67ceec662049175ab60f6cd8da8` | Q |
| O/kprm_okresowa_01_rozporzadzenie_o_ocenach_okresowych_z_2016_r_rozporzadzenie_o_ocenach_okres.pdf | `ea034d17073d1731304158787fe44ae356b33780562248892bf19f2b0452350e` | P, kopia konkursowa |
| O/kprm_okresowa_02_arkusz_oceny_a_arkusz_oceny_a_docx_0_04mb.docx | `aec1922ee2717f578ca4ca2ce8c1c96ffab83719ac67185c183ab7721e684e17` | A |
| O/kprm_okresowa_03_arkusz_oceny_b_arkusz_oceny_b_docx_0_04mb.docx | `47c2b62b81c49c62f03218dc7a1b5bacc0e21ab7d0c9c1437f56f4e52e1245c3` | B |
| O/kprm_okresowa_04_arkusz_oceny_c_arkusz_oceny_c_docx_0_04mb.docx | `4845015f886a56c8715006a5b803e77c6d628eab9aa4989763214c170ba662f0` | C |
| O/kprm_okresowa_05_arkusz_oceny_a_excel_arkusz_oceny_a_excel_xlsx_0_09mb.xlsx | `d2db71bf29f2d2eb92f2cc9eee39427f8ac1003b61b9b0989ef7b4a841d4bf27` | A, pomocnicze XLSX |
| O/kprm_okresowa_06_arkusz_oceny_b_excel_arkusz_oceny_b_excel_xlsx_0_09mb.xlsx | `5a86649c26e7591c438c10b017ae9b0672214f9a296b307e3bffa36cb466eba7` | B, pomocnicze XLSX |
| O/kprm_okresowa_07_arkusz_oceny_c_excel_arkusz_oceny_c_excel_xlsx_0_08mb.xlsx | `01d0498a746c5b59d3c0d3b18435045bd561f37cf7d27469733bf3747b38e633` | C, pomocnicze XLSX |
| O/kprm_okresowa_08_poradnik_oceny_okresowe_w_sluzbie_cywilnej_poradnik_oceny_okresowe_w_sluzbi.pdf | `62f91996b7d99e4177c5c559b88773112b31ce7c4f5cfb8e5ddb99f8d54476ac` | GP |
| O/historical/kprm_okresowa_09_rozporzadzenie_o_ocenach_okresowych_z_2015_r_rozporzadzenie_o_ocenach_okres.pdf | `d95c922b7fae04e3c7e6769687d809cc154d861396d12d44828d2f349146d75e` | H15 |
| O/historical/kprm_okresowa_10_rozporzadzenie_o_ocenach_okresowych_z_2009_r_rozporzadzenie_o_ocenach_okres.pdf | `598230cfafe8a917c3d86ef2cddf99d9e888445e93fdc146aae43940f9d89f83` | H09 |
| O/historical/kprm_okresowa_11_poradnik_oceny_okresowe_w_sluzbie_cywilnej_2009_r_poradnik_oceny_okresowe_w.pdf | `c38833d5e0c0f7f788a758c0af7531394ecc9b56bd8c3d04c11a61770ad42547` | HG09 |
| O/kprm_pierwsza_01_rozporzadzenie_o_pierwszej_ocenie_z_2015_r_rozporzadzenie_o_pierwszej_oceni.pdf | `0e8a0cf5c9c390edfc5a8868f57fcec2c539f37738c1775f9bed06e98389f217` | F |
| O/kprm_pierwsza_02_arkusz_pierwszej_oceny_arkusz_pierwszej_oceny_docx_0_04mb.docx | `12a6f89a8bb8b667e2e20b6efd504259c6cc061b36460b8d9b87fed50a5b1721` | FF |
| O/kprm_pierwsza_03_formularz_sprawozdania_formularz_sprawozdania_docx_0_02mb.docx | `aee7617e87287d9aeaedd0b074ff2d81a971acf3a29d033b338aef847b7bfbec` | R |
| O/kprm_pierwsza_04_opisy_elementow_oceny_opisy_elementow_oceny_docx_0_02mb.docx | `384269fd93876f31d72d179e4510e4f6a554167d0df13958dc05e1e40392800c` | E |
| O/kprm_pierwsza_05_arkusz_pierwszej_oceny_arkusz_pierwszej_oceny_xlsx_0_05mb.xlsx | `266008e62c5ff36c780ec5c3f668af3f020d22c364ea1ca59f4cbcca9f951658` | FF, pomocnicze XLSX |
| O/kprm_pierwsza_06_arkusze_ocen_instrukcja_uzytkownika_arkusze_ocen_instrukcja_uzytkownika_pdf.pdf | `9324bdf18bb10a609c6fda40d93f0b7019b99f4f5a5bce8e7f4cb9385c8d92ba` | I |
| O/kprm_pierwsza_07_pierwsza_ocena_w_sluzbie_cywilnej_poradnik_z_2016_r_pierwsza_ocena_w_sluzbi.pdf | `484cfcd0ed43d389d0ad61aa9bbe3c19ca2d02be378d785117cd93e909215307` | GF |
| O/historical/kprm_pierwsza_08_rozporzadzenie_o_pierwszej_ocenie_z_2009_r_rozporzadzenie_o_pierwszej_oceni.pdf | `8e5a52392fec97cf0fd8f2f33f2acf7cb7c96fe683f547803bac20a64b441fa0` | HF09 |
| O/MANIFEST_POBRANYCH.json | `0249f149d98f85476d234130bdc417e323df3f7524b4f8ffad8157944a8d16f5` | META |

### 2.2. Materiały konkursowe i kontekst implementacji

| Ścieżka | SHA-256 | Rola |
| --- | --- | --- |
| H/Model_kompetencji.xlsx | `f19e3d95e9331facf7ad4b291b6966f1807a080a9e84e7ba83a228f499c956d6` | K |
| H/Ocena okresowa w służbie cywilnej/Rozporządzenie o ocenach okresowych z 2016 r. (3).pdf | `ea034d17073d1731304158787fe44ae356b33780562248892bf19f2b0452350e` | P |
| H/Ocena okresowa w służbie cywilnej/Poradnik - oceny okresowe w służbie cywilnej (2).pdf | `62f91996b7d99e4177c5c559b88773112b31ce7c4f5cfb8e5ddb99f8d54476ac` | GP |
| H/Ocena okresowa w służbie cywilnej/Arkusz oceny B (2).docx | `47c2b62b81c49c62f03218dc7a1b5bacc0e21ab7d0c9c1437f56f4e52e1245c3` | B |
| H/Ocena okresowa w służbie cywilnej/Arkusz oceny C (2).docx | `4845015f886a56c8715006a5b803e77c6d628eab9aa4989763214c170ba662f0` | C |
| H/Pierwsza ocena w służbie cywilnej/Rozporządzenie o pierwszej ocenie z 2015 r. (1).pdf | `0e8a0cf5c9c390edfc5a8868f57fcec2c539f37738c1775f9bed06e98389f217` | F |
| H/Pierwsza ocena w służbie cywilnej/Pierwsza ocena w służbie cywilnej - poradnik z 2016 r. (1).pdf | `484cfcd0ed43d389d0ad61aa9bbe3c19ca2d02be378d785117cd93e909215307` | GF |
| H/Pierwsza ocena w służbie cywilnej/Arkusz pierwszej oceny (2).docx | `12a6f89a8bb8b667e2e20b6efd504259c6cc061b36460b8d9b87fed50a5b1721` | FF |
| H/Kompetencje wspierające analizę OSP + przykładowe OSP/Rozporządzenie o ocenach okresowych z 2016 r. (4).pdf | `5bc9792b1686158732a841dba682a54e477c53a2516321c5ce28afa395bb8eae` | P, podzbiór załącznika 1 |
| H/Kompetencje wspierające analizę OSP + przykładowe OSP/OSP_word/OSP DC WZKSOiC 6 starszy specjalista.docx | `ec066d1c658fda8a1302853752d7134d58766982f57b44d0b4ae8ee58dcad55f` | S1 |
| H/Kompetencje wspierające analizę OSP + przykładowe OSP/OSP_word/OSP DSI WWI 5 radca.docx | `2d47dd25778cac26d234ccee412ca7378cbf375610a8434b0ec726deecab3be5` | S2 |
| H/Kompetencje wspierające analizę OSP + przykładowe OSP/OSP_word/OSP DWM WKAM 1 naczelnik wydziału.docx | `1784499f1cb62dc3796e8d1de071c581840c63f60ced31ea4aa85b4a075951ff` | S3 |
| H/Kompetencje wspierające analizę OSP + przykładowe OSP/OSP_word.zip | `9d14fcc32a61d8c35d33527d628a588c0d954b65642941ef1d56de6c94637d5b` | ZIP |
| H/MC BDG - Pełna treść zadania konkursowego.pdf | `975756a8a79ae74caf75f5e74906ff3fc18e2627bb4eeffb83ca2de91ef73628` | DEV |
| H/MC BDG - Regulamin zadania konkursowego.pdf | `2864d280d9b9a62f098df181693c10419e7b5a0b7e711b6be9da694f7dc36d5c` | DEV |
| H/Kompas Kompetencji_ Ścieżki Oceny.png | `5d5c5135a7f3e8f00c046499ba77425ff676b33324ffa57fedffab960c707bb0` | DEV |
| H/phase6-plan.md | `103bcde5dae0ec3896c4149b6dfcff46632e8c1a4f061cec5d4156665ec2440f` | DEV |

### 2.3. Markdown — pełny zakres pomocniczy

| Ścieżka | SHA-256 | Mapowanie / rola |
| --- | --- | --- |
| M/rozporzadzenie_oceny_okresowe_2016.md | `ac45d042abc03ceb59172532a588890b125c4d157b64fe7fd3317f87d034c8af` | P, AUX |
| M/rozporzadzenie_pierwsza_ocena_2015.md | `eb2cbc0bbaaabc2ffc6c9526f75f09493e0ac2dfcfe1974d912f7ba754f78a5b` | F, AUX |
| M/poradnik_oceny_okresowe_2016.md | `1fbc06652fbaab7d98f3967aa2a64bade3a3524c0ea33940ba9fbe9b4573d7ae` | GP, AUX |
| M/poradnik_pierwsza_ocena_2016.md | `0b806c0861b6cefe0f99103e8d281aabd2bf778dfaee65c97fea33aff2083c0b` | GF, AUX |
| M/arkusz_oceny_B.md | `a1c68eb6f4a141ffb3c2aa7c2fb264942a82046567c517caa57e00e9e1a5a99b` | B, AUX |
| M/arkusz_oceny_C.md | `803c78f1321a01c87a22a2499b179daf8d386ba79c36adf9f9ecde76a3a045f2` | C, AUX |
| M/arkusz_pierwszej_oceny.md | `2afac851029e5244be52d2be7eb1c8fb0e786e6f44e6b176963423145e285af2` | FF, AUX |
| M/kryteria_ocen_okresowych_zalacznik_1_2016.md | `803308b94dd3a3727013f120fb21d0646acc6678ee3b3c0524d888a487f3702e` | podzbiór P, AUX |
| M/osp_starszy_specjalista_cyberbezpieczenstwo.md | `a802cb753e732374195029b22b9d24c92ece819e5b30255d8949a7a6149f23fd` | S1, AUX |
| M/osp_radca_sztuczna_inteligencja.md | `0f41bc13a35d155e2fd2a71afac0a8daf62e46d78c6570112077c83f5a5841d0` | S2, AUX |
| M/osp_naczelnik_wspolpraca_miedzynarodowa.md | `97c7d43be67a7c187bf1d03ec2e320f1615f34b3c96117597c9d0602d215df60` | S3, AUX |
| M/kompas_kompetencji_sciezki_oceny_opis.md | `58a7a425de8e25ee85060a8dd6974b91ac307ff82e91fe78ba8e261c8faaaf7c` | opis diagramu, DEV/AUX |

Porównanie niezależnej ekstrakcji z 11 Markdownami dało odpowiednio:
P **156**, F **74**, GP **195**, GF **118**, B **134**, C **129**, FF **119**,
podzbiór P **77**, S1 **157**, S2 **130**, S3 **144** grup różnic.
To także różnice formatowania, tabel i sklejeń słów PDF — **nie liczba błędów**.
Similarity nie potwierdza zgodności. Nie użyto Markdown do naprawiania przepisów.

## 3. Duplikaty i rekomendowany zestaw kanoniczny

**Siedem grup kopii bajtowych:** B, C, GP, GF, P konkursowe/KPRM oraz FF mają
po dwie kopie; F ma trzy (konkurs/KPRM/ELI). Nie tworzyć z nich dodatkowych źródeł.
Archiwum ZIP zawiera dokładnie trzy DOCX S1/S2/S3 z identycznymi SHA jak rozpakowane.

P z ELI i P z KPRM mają **różne bajty**, lecz każda z 19 par ekstrakcji stron jest
zgodna po normalizacji białych znaków. To nie uzasadnia podmiany przechowywanego
oryginału pod jego dotychczasowym hashem. Trzystronicowy wykaz odpowiada dokładnie
znormalizowanej ekstrakcji stron **5/6/7** pełnego PDF; jego lokalne strony 1/2/3
nie mogą być linkowane jako strony 1/2/3 pełnego aktu.

| Logiczny dokument | Kanoniczna reprezentacja / decyzja |
| --- | --- |
| Ustawa `eli:DU/2008/1505`, edycja 2026/590 | [Tekst jednolity PDF](https://eli.gov.pl/api/acts/DU/2026/590/text/T/D20260590L.pdf). Nie znaleziono w pobraniach HTML tej edycji; HTML aktu pierwotnego z 2008 nie może być uznany z automatu za aktualny tekst jednolity. Najpierw identyfikacja treści załącznika ustawy i przepisów o różnych datach obowiązywania. |
| `eli:DU/2016/470` | [ELI HTML](https://eli.gov.pl/api/acts/DU/2016/470/text.html), rzeczywiste `para_1`–`para_14`, podrzędne `pass`/`pint` i załączniki. Zachować oryginalne PDF i aktualne source ID `periodic-regulation-2016`; nie zmieniać istniejących lokalizatorów PDF na HTML w miejscu. |
| `eli:DU/2015/1144` | [ELI HTML](https://eli.gov.pl/api/acts/DU/2015/1144/text.html), rzeczywiste `para_1`–`para_14`; PDF i oryginały załączników jako punkt odniesienia. Zachować `first-regulation-2015`. |
| Formularze A/B/C, FF, R, E | Oryginał załącznika PDF + DOCX jako wzór pól. XLSX do walidacji i porównania działania, bez indeksowania setek helper cells jako nowych podstaw. `annex/3` i `annex/4` w canonical ID są identyfikatorami aplikacji, nie wymyślonymi anchorami ELI. |
| GP i GF | Oryginalne PDF KPRM; jedna wersja każdej publikacji, ekstrakcja stronami, jawna etykieta poradnika. |
| Q | [FAQ KPRM](https://www.gov.pl/web/sluzbacywilna/oceny-pracownicze). Wydzielić kompletne Q&A + przypisy i ostrzeżenie o niewiążącym charakterze. Nie pobierać nawigacji do promptu. |
| K | Istniejący `catalog_versions` i powiązane UUID. Reprezentacja wyszukiwawcza, jeśli potrzebna, musi wskazać tę samą wersję katalogu. |
| S1/S2/S3 | Oryginały DOCX wyłącznie jako oznaczone przykłady. Rzeczywiste OSP pracownika przez istniejący model `JobDescription` i autoryzację, poza wspólnym indeksem. |
| H15/H09/HF09/HG09 | Poza domyślnym kontekstem aktualnym. Indeks historyczny w tej samej bazie dopiero z zakresem czasu i jawnym żądaniem użytkownika; nie osobny RAG. |

Bieżący manifest importu nadal ma **12 istniejących source ID**; nowe pobrania
(ustawa, FAQ, A, R, E, instrukcja, historia) są zinwentaryzowane, lecz **nie są
udawane jako gotowe do importu**. Dodanie ich wymaga kontrolowanej ekstrakcji/review,
a nie rekurencyjnego wczytania wszystkiego. Metadane alternatywnych formatów nie
są dodatkowymi zadaniami importu. `preferred_text_path` określa kierunek poprawy,
nie przełącza istniejącego ekstraktora i nie nadaje automatycznego approval.

## 4. Aktualność prawna — oficjalna weryfikacja

Sprawdzono online karty ELI oraz metadane API Sejmu (nie tylko nazwy plików):

| Akt | Wynik i późniejsze relacje |
| --- | --- |
| [DU/2016/470](https://api.sejm.gov.pl/eli/acts/DU/2016/470) | `IN_FORCE`, „obowiązujący”, od 23.04.2016. Karta [ELI](https://eli.gov.pl/eli/DU/2016/470/ogl) zgodna; brak aktów zmieniających w zwróconych relacjach, uznaje za uchylony DU/2015/1143. **Rok 2016 nie oznacza historycznego prawa.** |
| [DU/2015/1144](https://api.sejm.gov.pl/eli/acts/DU/2015/1144) | `IN_FORCE`, „obowiązujący”, od 27.08.2015; [ELI](https://eli.gov.pl/eli/DU/2015/1144/ogl) zgodna. Brak aktów zmieniających w relacjach; uchyla DU/2009/772. |
| [DU/2015/1143](https://api.sejm.gov.pl/eli/acts/DU/2015/1143) | `NOT_IN_FORCE`, uznany za uchylony od **23.04.2016**, relacja do DU/2016/470. |
| [DU/2009/633](https://api.sejm.gov.pl/eli/acts/DU/2009/633) | `NOT_IN_FORCE`, uchylony **27.08.2015** przez DU/2015/1143. |
| [DU/2009/772](https://api.sejm.gov.pl/eli/acts/DU/2009/772) | `NOT_IN_FORCE`, uchylony **27.08.2015** przez DU/2015/1144. |
| [DU/2008/1505](https://api.sejm.gov.pl/eli/acts/DU/2008/1505) | Ustawa `IN_FORCE`, „akt posiada tekst jednolity”. Lista zmian obejmuje m.in. DU/2026/160 oraz **DU/2026/26 z datą 1.01.2027** dla zmiany tej ustawy. Nie wolno pominąć dat stosowania. |
| [DU/2026/590](https://api.sejm.gov.pl/eli/acts/DU/2026/590) | **Obwieszczenie**, nie nowa ustawa. `legalStatusDate=2026-04-14`; tekst jednolity dla DU/2008/1505. `IN_FORCE` obwieszczenia nie zatwierdza wszystkich przyszłych wariantów w przypisach. |
| [DU/2026/26](https://api.sejm.gov.pl/eli/acts/DU/2026/26) | Akt zmieniający ma różne daty wejścia w życie; relacja zmiany ustawy o służbie cywilnej wskazuje **1.01.2027**. Dla odpowiedzi „dzisiaj” nie stosować automatycznie przyszłej zmiany. |

**Ograniczenia treści, nie tylko metadanych:**

- PDF ustawy zawiera najpierw obwieszczenie i cytaty przepisów nowelizujących.
  `Art. 35` na **stronie 2** nie jest art. 35 ustawy w załączniku (**strona 16**).
  Prosty regex artykułów po całym pliku tworzyłby fałszywe cytowania.
- Art. 37–38 jest na stronie **17**; art. 81 przechodzi ze strony **24 na 25**,
  art. 82–83 są na 25. Nie wolno wyciąć warunków/wyjątków kontynuowanych na kolejnej stronie.
- Strona 16 ma m.in. art. 33 z przypisem o wejściu w życie zależnym od komunikatu.
  Z tego powodu nie nadajemy całemu PDF jednolitego bezwarunkowego approval.
- Obowiązywanie rozporządzenia P nie oznacza, że każdy dawny zakres formularza A
  stosuje się do wszystkich dzisiejszych wyższych stanowisk. Trzeba zestawić
  aktualny art. 81, zakres podmiotowy i §13 przepisu przejściowego. FAQ pytanie 6
  wyraźnie wyłącza wyższe stanowiska z bieżącej oceny okresowej.
- Q zawiera własne zastrzeżenie opinii, GP/GF nie są prawem. Ich cytaty ustaw,
  przykładów i starych terminów wymagają oceny, nawet jeśli nadal są publikowane.
  W Q istnieją m.in. odwołania zapisane jako `1013`/`292`: nie odtwarzać z nich
  automatycznie superskryptów ani rzekomych jednostek bez sprawdzenia oryginalnego aktu.
- Dla historycznego poradnika nie istnieje „uchylenie poradnika” jak dla przepisu.
  Historyczność wynika z treści i kontekstu edycji; brak niezależnego przeglądu
  wszystkich wskazówek komunikacyjnych. Status nie może być odziedziczony z folderu.

Ustalenia są datowane. Nie są opinią prawną ani gwarancją przyszłej aktualności.
Wprowadzenie odpowiadania na pytania historyczne wymaga dat obowiązywania na
poziomie właściwych jednostek, nie wyłącznie pojedynczego statusu całego źródła.

## 5. Audyt cytowań

### Obecny stan: brak pełnego łańcucha odpowiedzi

Gotowe odpowiedzi UI mają odwołania do rzeczywistych aktów, lecz **nie mają
udowodnionego powiązania z fragmentami**. To nie cytowania RAG, nie dowód poprawności
całej odpowiedzi i nie wynik jakiegokolwiek modelu. Naprawiono mylący opis UI:
jawnie mówi o ręcznych, niezweryfikowanych odwołaniach demo, także przy każdym
odnośniku tekstowym. Nie podmieniono gotowych odpowiedzi na pozornie działający chat.

Zaprojektowany zapis fragmentu jest bliżej wymaganego łańcucha:
`chunk.id → source_id → storage_key + original_sha256 → locator/page`.
PDF ma fizyczną stronę pliku, DOCX lokalizację strukturalną bez wymyślonego numeru
strony, XLSX arkusz/komórki i UUID katalogu. Fragmenty są ekstrakcją oryginału,
nie wygenerowanym Markdownem. **Nie ma jednak tych rekordów w aplikacyjnej bazie.**
Siedem decyzji `knowledge-reviews.json` jest lokalnym artefaktem technicznego
porównania dwóch PDF, nie opinią prawnika i nie zaaplikowanym zatwierdzeniem bazy.
1061 fragmentów to lokalny wynik ekstrakcji manifestu, **nie liczba w indeksie**.

### Dokładne braki i minimalne dalsze rozwiązania

| Problem | Najmniejsza potrzebna zmiana |
| --- | --- |
| Model może w przyszłości wymyślić URL/§, bo walidatora jeszcze nie ma | P6-04: zwracać wyłącznie ID dostarczonych fragmentów; serwer odrzuca nieprzekazane/niezatwierdzone/niedostępne ID i buduje link/lokalizację z własnych danych. Nie ufać bibliografii wygenerowanej przez model. |
| Nie ma adresu pochodzenia w dotychczasowym modelu | Wykonane: hash-bound `provenance`, oficjalny HTTPS URL, canonical ID, mapowanie reprezentacji i datowana kontrola. Migracja 0014 zachowuje to w DB; wdrożona po audycie (§8), bez importu źródeł. |
| Podzbiór kryteriów i pełny akt mogłyby dać dwa niezależne dowody | Wykonane mapowanie wspólnego canonical ID i `duplicate_subset`, z prawdziwymi stronami. P6-03 musi użyć tego mapowania do deduplikacji wyników. |
| Strona PDF nie jest dowodem numeru paragrafu | Nie emitować jednostek prawa z odgadniętych metadanych. HTML: rzeczywisty identyfikator elementu i pełna zawartość; PDF: kontrolowana strukturalna ekstrakcja, weryfikacja fragmentu i kontekstu. |
| Sam prawdziwy cytat nie potwierdza twierdzenia | P6-04/P6-07: osobno walidacja pokrycia twierdzeń, wyjątków i zakresu czasowego/podmiotowego. Testy przypadków z art. 81, §11, warunkami pierwszej oceny i nieobecnością, nie sam test istnienia ID. |
| Historyczne/poradnik mogłyby być traktowane jak dzisiejszy przepis | P6-03: domyślnie zatwierdzone, aktualne jednostki prawa, jawne rozróżnienie `source_type`; poradnik/FAQ jako oznaczony kontekst, nie substytut brakującej podstawy; historia tylko po określeniu daty. Obecnie brak retrievera, więc nie deklarujemy działającego filtra. |

Oficjalne linki nadają się do aplikacji: są kontrolowanymi metadanymi, nie
wyjściem modelu. Link publiczny dotyczy właściwego dokumentu; prywatny oryginał
z RustFS wymaga autoryzowanego endpointu. PDF może dostać `#page=N` dopiero po
sprawdzeniu mapowania. Lokalizator DOCX nie powinien udawać numeru strony ani
nieistniejącego anchoru w publicznym pliku. P6-05 pozostaje właściwym miejscem
na klikalne cytowania; ten audyt nie tworzy pozornej integracji.

## 6. Wykonane zmiany i weryfikacja

- `backend/resources/knowledge-manifest.json`: zachowane wszystkie 12 source ID,
  ścieżki oryginałów, wersje i 11 mapowań Markdown. Oficjalne URL-e przypięte do
  SHA oryginału, alternatywne PDF/HTML/DOCX/XLSX z hashami, canonical ID i role.
  Poprawione zbyt szerokie `historical`: dwa obowiązujące akty i ich wykaz mają
  datowane `verified_current`, poradniki i formularze `unknown`, bez podnoszenia
  statusu wierności ekstrakcji. Formularze/katalog do walidacji, OSP jako przykłady.
- `manifest.py`: typowane pochodzenie, kontrolowane hosty HTTPS, bez credentials,
  walidacja ścieżek, deklaracja formatu preferowanego. Markdown nie może być
  reprezentacją oryginału; status current wymaga datowanego oficjalnego dowodu.
- `ingestion.py`: checksum pochodzenia sprawdzany **przed** ekstrakcją i operacjami
  storage, zapis pochodzenia oraz zachowanie rygorystycznej idempotencji.
- `models.py`, nowa `0014_knowledge_provenance.py`: nullable JSONB, bez backfillu,
  kasowania lub zmiany ID. Downgrade odmawia utraty niepustych metadanych.
- `audit.py`: weryfikacja hashy reprezentacji i manifestu pobrań także po
  przeniesieniu do historical; brak pliku, wieloznaczność, duplikat wpisu i
  nieoficjalny URL są odrzucane. Audit nigdy nie nadaje approval.
- `tests/test_knowledge_provenance.py`, `test_knowledge_ingestion.py`:
  integralność wszystkich 25 pobrań i mapowań, brak automatycznego approval,
  błędne URL/ścieżki/hash, powtórny import metadanych bez nowego uploadu.
  `test_knowledge_sources.py`: istniejące siedem decyzji i warunki wysokiego ryzyka.
- `frontend/src/features/assistant/assistant-drawer.tsx`: uczciwa etykieta demo.
- `docs/knowledge-source-review.md`: wskazanie tego raportu jako nowszego ustalenia;
  stara notatka nie jest dowodem wdrożenia ani aktualności prawa.

**Wyniki:**

- Celowane testy backendu: `test_knowledge_extraction.py`, `test_knowledge_ingestion.py`,
  `test_knowledge_provenance.py`, `test_knowledge_sources.py`, `test_database.py`:
  **61 passed, 9,41 s**, bez skipów, z oryginałami i oddzielną bazą. Obejmują
  upgrade/check/ponowny upgrade oraz roundtrip migracji w izolowanym schemacie.
- Uruchomienie CLI wykryło serializację daty jako nie-JSON; poprawiono
  `model_dump(mode="json")`, dodano kontrolę serializacji. Po poprawce testy
  provenance ponownie: **9 passed, 5,37 s**; rzeczywisty CLI audytu: **OK**.
- Ruff lint/format dotkniętego kodu: **OK**. Frontend: oxlint **OK**, testy
  `responses.test.ts` **2 passed**, format dotkniętego TSX **OK**.
- Końcowa kontrola po walidacji hashy kopii oznaczonych `identical_bytes`:
  testy provenance + zapisanych decyzji **11 passed, 6,95 s**, Ruff OK.
  Niezależny self-check raportu potwierdza wszystkie **55 par ścieżka/SHA**.
- Znane ostrzeżenie Starlette o httpx pozostaje; bez związku z pochodzeniem źródeł.
- Raport pełnej ekstrakcji lokalnie `/tmp/opencode/official-source-extraction-audit.json`.
  Inwentaryzacja i robocze ekstrakcje całego drzewa w `/tmp/opencode/official-inventory.json`
  i `official-texts.json`; nie są wymaganymi plikami wdrożeniowymi. Trwałe SHA,
  klasyfikacja, wnioski i komenda odtworzenia znajdują się w tym raporcie.

Odtworzenie audytu istniejącego manifestu i wszystkich oficjalnych pobrań z `backend/`:

```bash
uv run python -m app.modules.knowledge.audit ../docs/hacknation-materials \
  --downloads-manifest ../docs/hacknation-materials/oficjalne-zrodla/MANIFEST_POBRANYCH.json \
  --output /tmp/opencode/official-source-extraction-audit.json
```

### Konsekwencje wdrożenia i wycofanie

Nie było potrzeby korygowania rekordów aplikacyjnych: wyjściowo tabele wiedzy nie istniały.
W samym audycie nie uruchamiano DDL ani importu na Compose; wdrożenie po audycie
opisuje §8. 0013 pozostaje bez zmian; 0014 jedynie
dodaje nullable kolumnę, nie zmienia rekordów wcześniejszych etapów. Ponowny upgrade
obsługuje Alembic. **W bazie mającej już źródła null provenance nie jest automatycznie
uzupełniane ponownym importem:** zmiana metadanych zostanie odrzucona. Taka instalacja
wymaga oddzielnego, zatwierdzonego, hash-bound backfillu z zapisem poprzednich wartości.
Nie ma potrzeby wykonywać go w sprawdzonym środowisku. Przy rollbacku aplikacji można
pozostawić nullable kolumnę; nie usuwać danych pochodzenia ani oryginałów dla downgrade.

## 7. Otwarte problemy i dokładna kontynuacja fazy 6

**Audyt stanu i inwentaryzacja zakończone. P6-02 nadal in_progress; nie zaczynamy
fazy 6 od nowa i nie deklarujemy gotowego RAG.** Obecnie historyczne pliki i Markdown
nie zanieczyszczają wyszukiwania, ponieważ nie ma aktywnego korpusu ani retrievera.
Sama klasyfikacja w manifestach nie zastępuje przyszłych filtrów runtime.

Kolejność dalszych prac w istniejącym planie:

1. **P6-02:** kontrolowana ekstrakcja ELI HTML oraz Q&A z prawdziwymi locatorami,
   wydzielenie ustawy z obwieszczenia i identyfikacja czasowo właściwych przepisów.
   Dopiero potem uzupełnić istniejący manifest o ustawę/FAQ i potrzebne załączniki;
   nie dodawać osobnego source ID na każdą kopię pliku. Kryteria: wyjątki, tabele,
   przypisy, kompletność jednostek, żadnej zamiany PDF cytatu na inny hash w miejscu.
2. Sprawdzić i naprawić timeout backendu, odbudować z nowymi zależnościami; odrębnie
   wdrożyć migracje bez resetu i wykonać ograniczony import sprawdzonych fragmentów
   wraz z kontrolowanym retry oraz kontrolą SHA w DB/RustFS. Raportować rzeczywiste liczby.
3. **P6-03:** jeden PostgreSQL retriever, filtry zatwierdzenia/aktualności/typu/okresu,
   canonical dedup i sąsiednie warunki. Katalog aplikacji nadal źródłem UUID kryteriów.
4. **P6-04/P6-05:** autoryzowane API, walidacja ID cytowań i pokrycia twierdzeń,
   klikalne oryginały. Nie przenosić ręcznych odwołań demo do nowej odpowiedzi modelu.
5. Rozwiązać zewnętrzny błąd generowania OpenRouter przed oceną jakości odpowiedzi;
   nie obchodzić go zmianą modelu/polityki. P6-07 osobno mierzy retrieval i generowanie.

Nie sprawdzano pełnej zgodności prawnej aplikacji, każdego zdania poradników,
wizualnego renderowania wszystkich formularzy ani przeglądarki/E2E. Nie ma wyników
jakości i latencji odpowiedzi AI. To jawne ograniczenia dalszego wdrożenia, nie
podstawa do usunięcia dokumentów czy odtworzenia bazy od zera.

## 8. Kontynuacja P6-02 po zakończeniu audytu

Wykonano celowy rebuild usług backendowych, bez resetu ani odtwarzania wolumenów:

```bash
docker compose --env-file .env.compose-check \
  -f infra/compose.yaml -f infra/compose.dev.yaml up --build -d backend
```

- Obraz ma runtime `httpx` i `python-docx`. Uvicorn ponownie uruchamia API:
  `GET http://127.0.0.1:33081/api/v1/health` → **200 `{"status":"ok"}`**.
- Usługa migracyjna zakończyła się pomyślnie: **0012 → 0013 → 0014**. Tabele
  wiedzy mają **0 źródeł / 0 fragmentów**; korpusu jeszcze nie importowano.
- `docker exec kompas-backend-1 alembic check` → **No new upgrade operations detected**.
  Powtórne `alembic upgrade head` → **OK, bez nowych operacji**; końcowy status
  kontenera backendu: **healthy**.
- Katalog zachował ten sam ID, wersję i hash. Nadal jeden prywatny `documents`
  i jeden `job_descriptions`; listowanie całego bucketu nadal daje jeden obiekt,
  zero `knowledge/`. Zbiór kluczy storage jest zgodny z rekordami `documents`,
  SHA każdego istniejącego obiektu jest zgodne z DB. Bez operacji usuwania.
- Nie uruchomiono kolejnych funkcji RAG ani ponownych generowań. Następny
  kontrolowany fragment P6-02: ekstrakcja ELI HTML/FAQ/załącznika ustawy i review;
   P6-03 pozostaje pending. Naprawa obrazu nie jest potwierdzeniem pełnej ścieżki UI.

## 9. Kontrolowana ekstrakcja ELI, FAQ i ustawy

Kontynuacja na polecenie użytkownika, 2026-11-21. Te czynności wykonano już po
inwentaryzacji opisanej wyżej. Oryginały zachowano bez modyfikacji; nie wykonano
importu do aplikacyjnego PostgreSQL/RustFS ani automatycznych zatwierdzeń.

### Wynik

| Nowe source ID | Profil | Fragmenty | Lokalizacja / ograniczenie |
| --- | --- | --- | --- |
| `periodic-regulation-2016-html-v1` | `eli-html-v1` | 19 | Preambuła, rzeczywiste `para_1`–`para_14`, załączniki `part_2`–`part_5`. Formularze w `part_3`–`part_5` są wyłącznie linkami do PDF, oznaczonymi jako nieobsługiwana treść. |
| `first-regulation-2015-html-v1` | `eli-html-v1` | 18 | Preambuła, rzeczywiste `para_1`–`para_14`, trzy załączniki dostępne tylko w PDF. |
| `kprm-assessment-faq-html-v1` | `kprm-faq-v1` | 31 | Pełne pytanie i odpowiedź z przypisami, rzeczywisty XPath `details` wewnątrz `article#main-content`; oryginalne zastrzeżenie opinii w każdym fragmencie. |
| `civil-service-statute-2026-590-v1` | `statute-2026-590-v1` | 218 | Osobne obwieszczenie s.1–2 i załącznik ustawy s.3–39; artykuły/części i przypisy mają rzeczywiste strony. |

Manifest obejmuje teraz **16 źródeł**, 1347 lokalnych fragmentów ekstrakcji,
w tym 286 nowych. To nadal nie liczba źródeł/fragmentów w bazie. Dotychczasowe
12 ID, `original-v1`, lokalizatory PDF i istniejące decyzje review zachowano.
HTML jest wersjonowaną reprezentacją tego samego canonical ID rozporządzenia,
nie niezależnym potwierdzeniem. SHA i oficjalne URL-e wskazano w manifeście;
audyt oraz importer odrzucają zmianę oryginału przed ekstrakcją.

Parser HTML korzysta z już obecnego `lxml` (teraz jawna zależność). Przetwarza
lokalne bajty UTF-8 bez pobierania zasobów. Pomija menu, skrypty, style i komentarze;
odrzuca niejednoznaczne ID, brak oczekiwanego korzenia i nieciągłą numerację
paragrafów/pytań. Nie tworzy stron HTML ani nie dopisuje treści brakujących form.

### Jednostki ustawy i warunki czasowe

- Profil PDF jest związany z SHA edycji 2026/590. Nie jest uniwersalnym parserem
  dowolnego polskiego aktu. Inna edycja wymaga nowego, sprawdzonego profilu.
- `notice/page-2` zachowuje cytat art.35 ustawy nowelizującej, ale nie otrzymuje
  locatora artykułu ustawy o służbie cywilnej. Ten właściwy to
  `annex/page-16/article-35/part-1`: 12-miesięczna umowa i możliwość przedłużenia
  na wniosek przy usprawiedliwionej nieobecności dłuższej niż 3 miesiące.
- Art.36 jest na s.16–17; art.37–38 na s.17. Zachowane są wyjątek absolwenta KSAP
  składającego wniosek o mianowanie oraz warunek pierwszej oceny po 8 miesiącach
  i nie później niż miesiąc przed końcem umowy.
- Art.81 jest rozdzielony fizycznie między s.24 i s.25. Każda część wskazuje drugą
  przez `required_context:<locator>`. Zachowano pełną listę ust.8 z warunkiem
  ponad 6 miesięcy oraz ust.9 o ponownej ocenie po negatywnym wyniku. Nie zgubiono
  odniesienia ust.7 wyłącznie do terminu z ust.4. Art.82–84 pozostają na s.25.
- Zachowano i sprawdzono ciąg **wszystkich 41 przypisów**. Przypis28 na s.22
  podaje wejście zmiany art.71 ust.1a od **1 stycznia 2027 r.**; fragment art.71
  ma zależność od tej strony przypisów. Przypisy na s.4 zachowują warunek
  uruchomienia systemu naboru i 7 dni od ogłoszenia komunikatu — nie zmieniono
  go w wymyśloną datę kalendarzową.
- Dwa brzmienia art.28 na s.12 i pozostałe powtórzone jednostki mają odrębne
  lokalizatory części, zależności i `parallel_wordings_require_temporal_review`.
  Żaden wariant nie jest wybierany automatycznie jako aktualny.
- Zakres `Art.132–190. (pominięte)` pozostaje jedną oznaczoną jednostką, nie
  fikcyjnymi pełnymi artykułami. Przepisy przejściowe/końcowe od art.191 mają
  osobne ostrzeżenie stosowalności; nie są traktowane jak bezterminowa reguła.

`required_context` jest zapisanym wymaganiem do przeglądu oraz przyszłego
retrievera, a nie działającym filtrem czasowym. P6-03/P6-04 musi rozwiązać zależności
w obrębie źródła i odmówić odpowiedzi przy niezatwierdzonym lub niedostępnym
kontekście, braku ustalonej daty/zdarzenia albo przekroczeniu limitu. Nie wolno
samodzielnie cytować obwieszczenia jako artykułu ustawy. Ustawa i FAQ pozostają
`legal_status=unknown`, nowe fragmenty `needs_review`.

### Kontrole i następny krok

- Ruff lint/format, `uv lock`: **OK**.
- Sześć modułów pytest z oryginałami i dedykowanym PostgreSQL: **70 passed,
  17,50 s, bez skipów**. Jedno ostrzeżenie deprecjacji Starlette/httpx.
- Testy obejmują m.in. zgodność kompletnej treści paragrafów z DOM, 31 Q&A,
  rzeczywiste XPath, negacje/wyjątki, odrzucenie zmiany SHA, brak menu/skryptów,
  równoległe brzmienia i poprawne zależności kontynuacji art.81.
- Kontrola zachowania tekstu PDF porównuje multizbiory wszystkich tokenów przed
  i po wydzieleniu jednostek (pomijając wyłącznie nagłówki stron i datę stopki).
  Żadna treść załącznika ani przypisów nie znika. Nie jest to wizualny audyt PDF.
- Testy integracyjne potwierdzają, że istniejący importer zapisuje te same
  locatory/hashe/ostrzeżenia HTML, pozostawia `needs_review` i przy ponowieniu
  nie wykonuje drugiego PUT. Baza testowa jest oddzielna od aplikacji.
- CLI audytu uruchomiono na wszystkich 16 źródłach, także z manifestem 25 pobrań.
  Pełne teksty/hashe są lokalnie w
  `/tmp/opencode/official-source-extraction-audit.json` i mogą być odtworzone
  komendą z backend README. Nie zmieniano oryginalnych materiałów.

Zlecony fragment ekstrakcji jest wykonany. Następne w P6-02: jawne decyzje
hash-bound dla ograniczonego zakresu (wierność oraz osobno daty/wyjątki), potem
kontrolowany import i retry. Przed użyciem CLI w Compose trzeba odbudować obraz
z nowym manifestem/resources; bieżące testy i audyt uruchamiano przez `uv` na hoście.
Nie uruchamiano przeglądarki ani LLM; nie zatwierdzono pełnej zgodności prawnej.

## 10. Ograniczony import i wyszukiwanie — aktualizacja 2026-11-21

Później wykonano kolejny krok: indywidualne decyzje wierności i import czterech
oryginałów (dwa rozporządzenia PDF oraz odpowiadające im HTML). Nie importowano
pozostałych dwunastu źródeł manifestu. Zakres decyzji:

| Reprezentacja | Fragmenty w DB | Approved | Needs review |
| --- | ---: | ---: | ---: |
| Okresowa PDF | 19 | 4 (s.1–4) | 15 |
| Pierwsza PDF | 8 | 3 (s.1–3) | 5 |
| Okresowa HTML | 19 | 5 (§§2,3,4,5,11) | 14 |
| Pierwsza HTML | 18 | 5 (§§2,3,6,9,10) | 13 |
| **Razem** | **64** | **17** | **47** |

Każda decyzja w `backend/resources/knowledge-reviews.json` jest przypięta do
SHA oryginału, ekstraktora, locatora i SHA treści; ma osobne uzasadnienie.
Pełne warunki, negacje, wyjątki egzaminacyjne i przedziały zachowane. To przegląd
wierności przez agenta implementującego, nie niezależne zatwierdzenie prawne.
Wszystkie cztery źródła jako całość nadal mają `needs_review`.

CLI obsługuje wielokrotne `--source`, weryfikuje ID i komplet rodziców przed
otwarciem bazy/storage. Import uruchomiono przez host uv na lokalnym PostgreSQL
i prywatnym RustFS. Cztery oryginały mają checksum zgodne z DB; retry nie
wykonuje PUT ani nie zmienia rekordów/ID/dat/decyzji. Pozostałe dokumenty,
istniejący OSP, katalog i oceny pozostały niezmienione.

P6-03 dodaje `KnowledgeRetriever`/PostgreSQL FTS oraz migrację `0015` z indeksem
GIN. Instancja ma `simple`, nie ma słownika `polish`; wyszukiwanie korzysta z
translacji polskich znaków i prefiksów, bez zmiany tekstu źródłowego. Tylko approved
i verified_current z właściwym przeznaczeniem i rodzajem oceny trafiają do wyników.
Canonical ID deduplikuje reprezentacje, z preferencją całych paragrafów HTML.

Zależności kontekstu są sprawdzane przechodnio w obrębie źródła; brak zatwierdzenia,
niezgodny hash, niezweryfikowany wariant czasowy lub przekroczenie limitu blokuje
dany kontekst. Strony zwykłego PDF nie są samodzielnym fallbackiem: bez struktury
potrzebny jest cały zatwierdzony dokument mieszczący się w limitach. Nie rozstrzygamy
czasowej stosowalności ustawy ani konfliktów rankingiem.

**Kontrole:** 104 testy wiedzy/CLI/importu/migracji OK, bez skipów; Ruff i lockfile
OK. `0015` wdrożona, powtórny upgrade i `alembic check` OK, GIN valid. Live smoke:
9/9 pytań ma właściwy paragraf w top-5, trzy przypadki bez podstaw nie zwracają
wyników. To mały test wyszukiwania, nie ewaluacja LLM ani deklaracja pełnego RAG.
Po odbudowie Compose `/api/v1/health` 200 i backend healthy; migawki rekordów
wiedzy/katalogu/dokumentów/OSP/ocen przed/po identyczne.

P6-02 i P6-03 zakończone dla tego ograniczonego korpusu. Następne P6-04: odpowiedź
grounded i walidacja cytowań, potem drawer, OSP oraz pełna ewaluacja. Ustawa, FAQ,
formularze i poradniki nadal wymagają osobnego review; braki nie mogą być
uzupełniane wiedzą modelu. Provider nadal ma wcześniejszy bloker konta 401.
